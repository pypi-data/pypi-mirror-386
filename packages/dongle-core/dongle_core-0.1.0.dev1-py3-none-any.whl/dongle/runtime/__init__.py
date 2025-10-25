# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

import os
import sys


def init_from(fullname: str):
    import logging
    logging.basicConfig(level=os.getenv("LOGLEVEL", "INFO"))

    from .machinery import DongleReady, reload_module
    from .supervisor import DongleRuntime

    module = sys.modules[fullname]
    if DongleRuntime.init_runtime():
        class _DongleReady(DongleReady):
            def reload(self):
                if fullname == '__main__':
                    _fullname = module.__package__ + "." + fullname
                else:
                    _fullname = fullname
                return reload_module(_fullname, module)

        raise _DongleReady(fullname)

    return sys.modules[fullname]

__signature__ = "MGQCMGzNcti5/KHo4+sE6aFmBS+yFq0eQFK/tkZHEb0ibJphOdm7yEetaPnsNBzp2Kd4vgIwKrHouiT1GiuwJfebpU2b9Zzyzfmlc0BEUoCT59cIwqPnPeAqdPF6T4xG/sHanFeI"
