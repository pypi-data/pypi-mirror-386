# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

import pathlib
import sys
from importlib import import_module, metadata

from .exceptions import MissingDongle, InvalidProof


pkg_dists = metadata.packages_distributions()


def split_module_name(fullname: str) -> (str, str):
    if '.' in fullname:
        package_name, *_, module_name = fullname.split('.')
    else:
        package_name = module_name = fullname
    return package_name, module_name


def find_distribution(package: str) -> metadata.Distribution | None:
    dist_names = pkg_dists.get(package)
    if not dist_names:
        raise FileNotFoundError("Distribution for %s not found.", package)

    dist = metadata.distribution(dist_names[0])
    return dist


def get_package_path(package_name, module):
    package_module = sys.modules.get(package_name, None)

    # If we have a package_module with a path, use this path.
    if package_module is not None and hasattr(package_module, '__path__'):
        return [*map(pathlib.Path, package_module.__path__)]

    # If we have a module_path pointing to a file, use this to derive the package path.
    elif package_module is None and hasattr(module, '__file__'):
        module_path = pathlib.Path(module.__file__)
        return [module_path.parents[module.__name__.count('.')]]

    return []


def find_in_path(fullname: str, path: [str], suffixes: [str]):
    for path_entry in map(pathlib.Path, path):
        for suffix in suffixes:
            full_path = (path_entry / (fullname + suffix))
            if full_path.exists():
                return full_path

    raise ModuleNotFoundError(fullname)


def check_module(fullname: str, module):
    # Get latest version from sys.modules.
    module = sys.modules.get(fullname, module)

    # Check if dongle is present (i.e., loaded using dongle import system)
    if not (hasattr(module, "__proof__") and hasattr(module, "__dongle__")):
        raise MissingDongle(fullname)

    # Check if proof is still valid.
    if not module.__dongle__.check_proof(fullname, module.__proof__):
        raise InvalidProof(fullname)

    return module


def collect_protected_packages(exclude: list = None) -> list:
    exclude = exclude or []
    packages = {}

    for fullname, module in sys.modules.items():
        package_name, *tail = fullname.split(".")
        if package_name in exclude or package_name in packages:
            continue

        for package_dir in get_package_path(package_name, module):
            if (package_dir / "__dongle__.py").is_file():
                packages[package_name] = True
                break
        else:
            packages[package_name] = False

    return [name for name, is_protected in packages.items() if is_protected]


def collect_protected_modules(protected_packages: list, exclude: list = None) -> list:
    exclude = exclude or []
    modules = []

    loaded_modules = [(name, mod) for name, mod in sys.modules.items() if name not in exclude]
    for fullname, module in loaded_modules:
        package_name, _ = split_module_name(fullname)
        if package_name in protected_packages:
            modules.append((fullname, sys.modules[fullname]))

    return modules


def reload_module(fullname: str, module):
    # Get latest version from sys.modules.
    module = sys.modules.get(fullname, module)

    # Try to validate module to avoid useless reload.
    try:
        module = check_module(fullname, module)

    # If no dongle is present, perform reload.
    except MissingDongle as e:
        # Ensure we don't get a cached version.
        if fullname in sys.modules:
            del sys.modules[fullname]
        module = import_module(fullname, fullname.rsplit('.', 1)[0])

    return module

__signature__ = "MGYCMQD62picNNH4RDu+0C1FfqMC+lrPJ75tdhsUinLIpLo+f8bdFSdMCmB893L1q8H6LIYCMQDZR3RzXRfzhM7EHeaANo/mKhOfU6dBCNY3QKiBH+fDMqtr+NYDyj1DkHPLWsweJw4="
