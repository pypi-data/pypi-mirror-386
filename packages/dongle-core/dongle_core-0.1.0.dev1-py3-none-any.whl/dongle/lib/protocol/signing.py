# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

import base64
import json

from cryptography import exceptions

from dongle.lib.primitives import PublicKey


def get_signing_algorithm():
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec

    hashing_algorithm = hashes.SHA256()
    signing_algorithm = ec.ECDSA(hashing_algorithm)
    return signing_algorithm


def verify_data(signing_key: PublicKey, signed_data: bytes, signature: bytes) -> bool:
    try:
        signing_key.key.verify(signature, signed_data, get_signing_algorithm())
    except exceptions.InvalidSignature:
        return False
    return True


def to_canonical_json(json_data: dict) -> bytes:
    json_str = json.dumps(json_data, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return json_str.encode("ascii")


def verify_json(signing_key: PublicKey, signed_json: bytes) -> dict:
    signed_data = json.loads(signed_json)
    signature = base64.b64decode(signed_data.pop("signature"))

    if not verify_data(signing_key, to_canonical_json(signed_data), signature):
        raise ValueError("Verification failed.")

    return signed_data

__signature__ = "MGQCMCoWXqZp8g/vuEN5RZySAD+urWvwS43fBbiXMrGf643Ljk72bfWLo8O9WCVIKcxkwAIwCVnZLwZrPNwVyHvCVMQBevKcSnfsRCRisxIIPJacaLh1uCViS8belcTa/c7W6mIL"
