# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

import base64

from dongle.exceptions import SignatureVerificationError
from dongle.lib import protocol
from dongle.lib.primitives import PublicKey


class ModuleVerifier:
    SIGNATURE_SEPARATOR = b'\n\n'
    SIGNATURE_PREFIX = b'__signature__ = "'
    SIGNATURE_SUFFIX = b'"\n'

    def __init__(self, signing_key: PublicKey):
        self.signing_key = signing_key

    def _extract_signed_module(self, module_data):
        # Calculate length of prefix and suffix to signature line.
        _prefix_len = len(self.SIGNATURE_PREFIX)
        _suffix_len = len(self.SIGNATURE_SUFFIX)

        # Signature is expected on the last line, seperated by an empty line (i.e., two line breaks)
        try:
            module_data, sig_data = module_data.rsplit(self.SIGNATURE_SEPARATOR, 1)
        except ValueError as e:
            raise SignatureVerificationError("No signature found.") from e

        # Check if signature line has correct beginning and ending.
        if not (
                sig_data[:_prefix_len] == self.SIGNATURE_PREFIX and
                sig_data[-_suffix_len:] == self.SIGNATURE_SUFFIX
        ):
            raise SignatureVerificationError("No signature found.")

        # Extract and convert signature data from base64 string.
        signature = base64.b64decode(sig_data[_prefix_len:-_suffix_len])

        return module_data, signature

    def verify_module(self, module_data: bytes) -> bytes:
        module_data, signature = self._extract_signed_module(module_data)

        if not protocol.verify_data(self.signing_key, module_data, signature):
            raise SignatureVerificationError("Invalid signature.")

        return module_data

__signature__ = "MGYCMQC5yC2R6jbBsCfmgY/ck7bnIEHXYHZ8dsEF0CL4DBu155Qk9HSrFnAEvXtqNFwZ07ACMQCP2GPLaxdB0S7ut7zszrnxPQvX178heat9miFMfhm5zxrjzluBlWJVsytvDr0K+e4="
