# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import sys


class CLI:
    def __init__(self):
        self.arg_parser = argparse.ArgumentParser(
            __name__,
            description="Dongle utility commands.",
            add_help=True
        )
        self.sub_parsers = self.arg_parser.add_subparsers(required=True)

    def command(self, *args):
        def decorator(command_func):
            command_parser = self.sub_parsers.add_parser(command_func.__name__)
            all(command_parser.add_argument(*arg, **kwarg) for arg, kwarg in args)
            command_parser.set_defaults(func=command_func)
            return command_func
        return decorator

    def __call__(self):
        args = self.arg_parser.parse_args()
        try:
            args.func(args)
        except RuntimeError as e:
            print("An error occurred:", e)
            sys.exit(1)

__signature__ = "MGQCMCg0VaYU/dgGO+YmB7rp1R59qqdUPjI1c11Zj9wCs/xXPgdasr+fbEc62v/lxdYuKQIweRPI44SoYPs5WMEQkPmQATEtL7rYBDlg/4F37KvsHUWjRU1c+8EYcufGEuGd8OnB"
