# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

import base64

from dongle.lib import protocol
from dongle.lib.primitives import SymmetricKey
from .ascii_armor import ASCIIArmoredFile


class ModuleDecryptor:
    def __init__(self, secret: SymmetricKey):
        self.secret = secret

    def load_encrypted_module(self, module_data: bytes) -> bytes:
        # Parse PGP-like block.
        module_data = module_data.decode("utf-8").splitlines()
        headers, block_data, _ = ASCIIArmoredFile.load_block("ENCRYPTED MODULE", module_data)

        # Extract relevant parts of the payload.
        module_build = headers.pop("Module") + "-" + headers.pop("Build")
        module_nonce = SymmetricKey(base64.b64decode(headers.pop("Nonce")))
        encrypted_data = base64.b64decode("".join(block_data))

        # Apply cryptographic protocol.
        module_secret, module_tag = protocol.derive_module_secrets(self.secret, module_build)
        module_source = protocol.decrypt_data(module_secret, module_nonce, encrypted_data, module_tag)

        return module_source

__signature__ = "MGUCMQCPDV/rmyQKEQHH1uQk8Xc6SpCgWByQfPXgRa/y3Exbo3RHZ+9GQPiicANwpOJpwgICMAq/AplYBdfU26tsjrU+GxBHF5hTbFZnaI64HTTfZ9zALIgZK3ik/N1HyXk1KusTwg=="
