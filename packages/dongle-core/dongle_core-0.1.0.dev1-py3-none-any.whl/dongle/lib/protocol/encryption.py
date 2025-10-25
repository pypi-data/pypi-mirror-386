# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

from dongle.lib.primitives import SymmetricKey


def get_cipher(secret: SymmetricKey):
    from cryptography.hazmat.primitives.ciphers import aead

    return aead.AESGCM(secret.key)


def decrypt_data(secret: SymmetricKey, nonce: SymmetricKey, encrypted_data: bytes, tag: SymmetricKey) -> bytes:
    return get_cipher(secret).decrypt(nonce.key, encrypted_data, tag.key)

__signature__ = "MGUCMQCkkwIIrREs53KxGAp782lUqNa9wvCipUh1BakGSxDds67aVNcA1kwGjOA07vTutegCMHHyLlqUKht1HSl2SpDWwT6vSW80lV9lItJpIm28h2AL0sDIhKiC1SudQ7nxKhK1+w=="
