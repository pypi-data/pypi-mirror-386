# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

class DongleReady(ImportError):
    """ Raised by dongle.init_from when the runtime was initialized. """
    pass


class MissingDongle(RuntimeError):
    """ Raised when a module is checked but has no dongle. """
    pass


class NoLicenseError(RuntimeError):
    """ Raised when a module is loaded without a valid license. """
    pass


class InvalidProof(Exception):
    """ Raised when the proof for a given module could not be verified. """
    pass

__signature__ = "MGYCMQDJsIhDp+bUX47Q3B4EGgWH6yanxBjlVUKmAcI4A93J8ljChMt/3/0SPfUiQFkHXisCMQDJbw0kY+7il4V9AP4vd8YfvXhuUbHVG0tRl89UbmbgZJMjYJHgMox5xZNwKyZ291c="
