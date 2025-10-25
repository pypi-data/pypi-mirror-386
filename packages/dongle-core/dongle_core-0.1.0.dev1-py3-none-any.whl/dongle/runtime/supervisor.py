# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import sys
import threading
from importlib import import_module, metadata
from types import ModuleType

from . import runtime_hooks


_runtime = None


class DongleRuntime:
    BUILT_IN_HOOKS = {
        "api": [
            runtime_hooks.RuntimeAPI,
        ],

        "dongle": [
            runtime_hooks.RuntimeAPI,
        ],

        "license": [],

        "runtime": [],
    }

    class ModuleDongle:
        pass

    def __init__(
            self,
            primitives: ModuleType,
            protocol: ModuleType,
            machinery: ModuleType,
            bootstrap: ModuleType,
            **kwargs
    ):
        self.log = logging.getLogger("dongle.runtime")

        self.primitives = primitives
        self.protocol = protocol
        self.machinery = machinery
        self.bootstrap = bootstrap

        self.user_key = kwargs.get("user_key", None) or self.load_user_key()
        self.runtime_key = kwargs.get("runtime_key", None) or self.protocol.generate_key()
        self.cache = kwargs.get("cache", None)

        self.runtime_secret = lambda app_key: self.protocol.derive_shared_secret(self.runtime_key, app_key)

        self.package_dongles = kwargs.get("package_dongles", {})
        self.licenses = kwargs.get("licenses", {})

        self.module_finder = kwargs.get("module_finder", None)
        self.develop_hook = kwargs.get("develop_hook", None)

    def check_runtime(self):
        self.log.debug("Starting self check...")

        try:
            from dongle.util import check

            self.machinery.check_module(check.__name__, check)
        except self.machinery.MissingDongle as e:
            self.log.warning("Self check failed with %s", e)

            if self.develop_mode(activate=True):
                self.log.info("Develop mode activated.")
 #           else:
 #               raise RuntimeError("Self check failed.") from e

    def develop_mode(self, activate: bool = False) -> bool:
        if self.develop_hook is None:
            return False
        if self.develop_hook.is_active():
            return True
        if activate:
            return self.develop_hook.activate()
        return True

    def calculate_proof(self, app_key, module_name: str) -> str:
        runtime_secret = self.runtime_secret(app_key)
        return self.protocol.derive_from_secret(runtime_secret, module_name, ITERATIONS=1_500)

    def load_user_key(self):
        from .license import License

        user_name = os.environ.get("DONGLE_USER")
        user_key = License.keyring.load_key("user", user_name, private=True, password=None)

        return user_key

    def _init_package_hooks(self, module: ModuleType):
        package_hooks = getattr(module, "hooks", None)
        module.hooks = {}
        if package_hooks is None:
            return

        filter_hooks = lambda scope: [hook for hook in package_hooks if hook["scope"] == scope]
        for scope in self.BUILT_IN_HOOKS.keys():
            ep_group = f"dongle.hook.{scope}"
            module.hooks[scope] = []

            scope_hooks = filter_hooks(scope)
            self.log.debug("Loading %s hooks for %s scope...", len(scope_hooks), scope)

            for hook in scope_hooks:
                eps = metadata.entry_points(group=ep_group, name=hook["use"])
                module.hooks[scope] += [(ep, hook) for ep in eps]

    def init_package_dongle(self, package_name: str, package_dongle: ModuleType):
        from .license import License

        self.log.debug("Initialize dongle for %s...", package_dongle.app_name)

        self.package_dongles[package_name] = package_dongle

        package_dongle.app_key = self.primitives.PublicKey.import_pem(package_dongle.app_key)
        package_dongle.vendor_key = License.keyring.load_key("vendor", package_dongle.vendor_name)

        package_dongle.runtime_secret = lambda: self.runtime_secret(package_dongle.app_key)

        checks = []
        class Watchdog:
            def add_check(self, check):
                checks.append(check)

            def check(self):
                for check in checks:
                    check()

        package_dongle.watchdog = Watchdog()

        def get_build_secret(app_key):
            if package_dongle.build_name not in self.licenses:
                self.licenses[package_dongle.build_name] = License.load_user_license(self.user_key, package_dongle.vendor_key, package_dongle.build_name)
                license = self.licenses[package_dongle.build_name]

                for hook, config in package_dongle.hooks.get("license", []):
                    hook.load().init(config, license)

                self.log.info("License for %s loaded.", package_dongle.build_name)
            return self.licenses[package_dongle.build_name].build_secret

        package_dongle.build_secret = lambda: get_build_secret(package_dongle.app_key)

        self._init_package_hooks(package_dongle)
        for hook, config in package_dongle.hooks.get("dongle", []):
            hook.load().init(config, package_dongle)

    def load_package_dongle(self, package_name: str):
        if package_name in self.package_dongles:
            return self.package_dongles[package_name]

        self.package_dongles[package_name] = None
        try:
            return import_module(f"{package_name}.__dongle__", package_name)
        except ModuleNotFoundError as e:
            del self.package_dongles[package_name]
            return None

    def make_module_dongle(self, package_dongle: ModuleType, module: ModuleType) -> ModuleDongle:
        self.log.debug("Initialize module dongle for %s...", module.__name__)

        class _ModuleDongle(DongleRuntime.ModuleDongle):
            build_name = package_dongle.build_name
            check_proof = staticmethod(lambda module_name, proof: self.calculate_proof(package_dongle.app_key, module.__name__))

            def __init__(_self):
                _self.module = module

        for hook, config in package_dongle.hooks.get("api", []):
            hook.load().init(config, _ModuleDongle)

        return _ModuleDongle()

    def reload_runtime(self):
        self.primitives = self.machinery.reload_module(self.primitives.__name__, self.primitives)
        self.protocol = self.machinery.reload_module(self.protocol.__name__, self.protocol)
        self.machinery = self.machinery.reload_module(self.machinery.__name__, self.machinery)
        self.bootstrap = self.machinery.reload_module(self.bootstrap.__name__, self.bootstrap)

        global _runtime

        runtime_module = self.machinery.reload_module(__name__, sys.modules[__name__])
        cls = getattr(runtime_module, self.__class__.__name__)

        _runtime = runtime_module._runtime = cls(
            self.primitives,
            self.protocol,
            self.machinery,
            self.bootstrap,
            user_key=self.user_key,
            runtime_key=self.runtime_key,
            cache=self.cache,
            package_dongles=self.package_dongles,
            licenses=self.licenses,
            module_finder=self.module_finder,
            develop_hook=self.develop_hook,
        )

        return _runtime

    @classmethod
    def init_runtime(cls):
        global _runtime

        if _runtime is None:
            from dongle.lib import primitives, protocol
            from dongle.runtime import machinery, bootstrap

            _runtime = cls(primitives, protocol, machinery, bootstrap)

            _runtime.bootstrap.step_1(_runtime)
            _runtime.bootstrap.step_2(_runtime)
            _runtime.bootstrap.step_3(_runtime)
            _runtime.bootstrap.step_4(_runtime)

            return True

        return False

__signature__ = "MGUCMQDJ8vdTYnk4DaqcggtR9OA5A5B2yb4hTrw32F5umcPbmFXHoi7V4+ulUcx/H3GjM8YCMEH25+GTbXC4hkw8GzvmRxL3mBEdlpdHcna4h8A1MdUCJ/wcOJjrIW2+dfG4scseMw=="
