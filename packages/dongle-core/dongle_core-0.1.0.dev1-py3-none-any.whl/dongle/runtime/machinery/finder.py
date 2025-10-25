# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

import pathlib
import sys
from importlib import abc, machinery, metadata, util as import_util


def make_finder(runtime):
    from .loader import make_loader_classes
    from . import util

    SignedSourceFileLoader, EncryptedSourceFileLoader = make_loader_classes(runtime)

    class MetaPackageDongle:
        def verify(self, signed_data: bytes) -> bytes:
            return signed_data


    class DongledFileFinder(abc.MetaPathFinder):
        def package_dongle_spec(self, fullname: str, module_path: pathlib.Path) -> machinery.ModuleSpec:
            loader = SignedSourceFileLoader(fullname, str(module_path), MetaPackageDongle())

            runtime.log.debug("Dongle spec for %s created.", fullname)
            return import_util.spec_from_loader(fullname, loader)

        def module_spec(self, package_dongle, fullname: str, module_path: pathlib.Path, is_package: bool):
            is_encrypted = package_dongle.is_encrypted(fullname)

            if is_encrypted:
                loader = EncryptedSourceFileLoader(fullname, str(module_path), package_dongle)
            else:
                loader = SignedSourceFileLoader(fullname, str(module_path), package_dongle)

            module_spec = import_util.spec_from_loader(fullname, loader, is_package=is_package)
            runtime.log.debug("Spec for %s created.", fullname)
            return module_spec

        def find_module_spec(self, fullname, module_path):
            # Load package dongle for the root package.
            package, _ = util.split_module_name(fullname)
            package_dongle = runtime.load_package_dongle(package)

            # Stop any further attempts if there is no __dongle__.
            if package_dongle is None:
                return None

            # If target module is a directory, path needs to be adjusted.
            if module_path.is_dir():
                is_package = True
                module_path = module_path / "__init__.py"
            else:
                is_package = False

            # Import the actual module file.
            if module_path.is_file():
                return self.module_spec(package_dongle, fullname, module_path, is_package)

            return None

        def find_spec(self, fullname: str, path: str | None, target = None):
            if path is None:
                # Handle root package import, use sys.path.
                path = sys.path

            package, module = util.split_module_name(fullname)
            try:
                module_path = util.find_in_path(module, path, suffixes=["", ".py"])
                if module == "__dongle__":
                    # Treat import __dongle__ correctly as it is signed by vendor_key instead of app_key.
                    return self.package_dongle_spec(fullname, module_path)
                else:
                    return self.find_module_spec(fullname, module_path)

            except (FileNotFoundError, ModuleNotFoundError):
                return None

    return DongledFileFinder()

__signature__ = "MGUCMFGwyCYTUE8Ih1jQV5e81wvCgDALmtBpk3np2aocsqPC6fZWQZB7Y3b4pj3qzwwPcwIxAN9sDu0/KrQywR2IWE/y8ek/gDCfkjClGlsJETC3zMgWNTmqn+qBKs/xt+u5FUjSwA=="
