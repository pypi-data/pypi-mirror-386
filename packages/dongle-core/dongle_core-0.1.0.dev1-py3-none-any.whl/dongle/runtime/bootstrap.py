# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

import sys


def step_1(runtime):
    runtime.log.debug("Step 1: Install dongle import system (unverified)")

    runtime.module_finder = runtime.machinery.make_finder(runtime)
    sys.meta_path.insert(0, runtime.module_finder)

    runtime.check_runtime()


def step_2(runtime):
    runtime.log.debug("Step 2: Unload unverified modules.")

    protected_packages = runtime.machinery.collect_protected_packages()
    protected_modules = runtime.machinery.collect_protected_modules(protected_packages, exclude=[__name__, "dongle.runtime.supervisor"])
    for module_name, _ in protected_modules:
        del sys.modules[module_name]

    runtime.cache = protected_packages, protected_modules


def step_3(runtime):
    if runtime.develop_mode():
        runtime.log.debug("Step 3 skipped in develop mode.")

    runtime.log.debug("Step 3: Reload runtime and re-initialize import system.")

    runtime = runtime.reload_runtime()

    old_module_finder = runtime.module_finder
    runtime.module_finder = runtime.machinery.make_finder(runtime)

    sys.meta_path.remove(old_module_finder)
    sys.meta_path.insert(0, runtime.module_finder)


def step_4(runtime):
    runtime.log.debug("Step 4: Verify and clean up environment.")

    protected_packages, protected_modules = runtime.cache

    for fullname, module in protected_modules:
        if fullname not in sys.modules:
            continue

        module = sys.modules.get(fullname, module)
        try:
            runtime.machinery.check_module(fullname, module)
        except runtime.machinery.MissingDongle as e:
            module = runtime.machinery.reload_module(fullname, module)
            runtime.machinery.check_module(fullname, module)

__signature__ = "MGUCMCImSp/X8yZihZja3uKANcLW6F1uL6603Y2LoVfithk8OiYJ8YJwYhm7yR5vYnd45QIxAOiCiwDOoitvnuOk+zYdACMrQM+DflMcpzciX+OztN/aGdTcuTpr74qyWgjjb8Urng=="
