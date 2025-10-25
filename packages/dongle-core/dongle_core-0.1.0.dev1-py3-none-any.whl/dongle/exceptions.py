# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

class SignatureVerificationError(ValueError):
    """ Raised when the signature could not be verified. """
    pass


class ModuleFormatException(Exception):
    """ Raised when parsing an encrypted module failed. """
    pass


class DecryptionError(Exception):
    """ Raised when decryption of encrypted module data failed. """
    pass

__signature__ = "MGYCMQDAZ0GTCnC3VRCH2e5uhHZPauQ/bonXuvqiLdNXiJllnHJ/xRqXP2ToAOElEzxrQpkCMQChe2s7JnXbyTUCR3hp7Lwv7XaOUVNkDAgBa41yaafkxnMAYt3qBz7nZckZg3a3xG0="
