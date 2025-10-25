# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

import sys
from importlib import machinery

from .util import split_module_name


def make_loader_classes(runtime):
    class SignedSourceFileLoader(machinery.SourceFileLoader):
        def __init__(self, fullname: str, path: str, package_dongle):
            super().__init__(fullname, path)

            self.verify_module = lambda signed_data: package_dongle.verify(signed_data)

        def verify_data(self, path: str, signed_data: bytes) -> bytes:
            try:
                return self.verify_module(signed_data)
            except ValueError as e:
                raise ImportError(f"Could not verify signature for {self.name}.", name=self.name, path=path) from e

        def exec_module(self, module):
            package_name, module_name = split_module_name(module.__name__)

            package_dongle = runtime.package_dongles.get(package_name)

            if module_name != "__dongle__":
                runtime.log.debug("Prepare module dongle for %s.", self.name)
                module.__proof__ = runtime.calculate_proof(package_dongle.app_key, self.name)
                module.__dongle__ = runtime.make_module_dongle(package_dongle, module)

            super().exec_module(module)

            if module_name == '__dongle__':
                runtime.init_package_dongle(package_name, module)
                sys.modules[self.name] = None

        def get_data(self, path):
            data = super().get_data(path)
            return self.verify_data(path, data)

        def set_data(self, path, data, *, _mode=...):
            # No caching of compiled code, yet.
            pass

    class EncryptedSourceFileLoader(SignedSourceFileLoader):
        def __init__(self, fullname: str, path: str, package_dongle):
            super().__init__(fullname, path, package_dongle)
            self.decrypt_data = lambda encrypted_data: package_dongle.decrypt(encrypted_data)

        def decrypt_data(self, path: bytes | str, encrypted_data: bytes) -> bytes:
            try:
                return self.decrypt_data(encrypted_data)
            except ValueError as e:
                raise ImportError(f"Decryption of {self.name} failed.", name=self.name, path=path) from e

        def get_data(self, path):
            encrypted_data = machinery.SourceFileLoader.get_data(self, path)
            signed_data = self.decrypt_data(encrypted_data)
            return self.verify_data(path, signed_data)

    return SignedSourceFileLoader, EncryptedSourceFileLoader

__signature__ = "MGQCMEA+Mg+0X0xxrVszclw10uodQlEzCMBthFOeh+Mu4YOgZBWCHt97t+Wt8VpCOaDzqwIwLIknfW/Z5RHVzokp1YRReZi+OhEEYn8wi3ehiQ0dn8Vhe85ZqhQCgwm6Zd5FRFLl"
