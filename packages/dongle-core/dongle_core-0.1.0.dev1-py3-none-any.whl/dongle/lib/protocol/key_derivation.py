# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

from cryptography.hazmat.primitives.asymmetric import ec

from dongle.lib.primitives import PrivateKey, PublicKey, SymmetricKey, Password, PBKDF2


def generate_key(tag: str | None = None) -> PrivateKey:
    key = ec.generate_private_key(PrivateKey.CURVE)
    return PrivateKey(key, tag=tag)


def derive_shared_secret(private_key: PrivateKey, public_key: PublicKey, tag: str | None = None) -> SymmetricKey:
    shared_secret = private_key.key.exchange(ec.ECDH(), public_key.key)
    return SymmetricKey(shared_secret, tag=tag, derived_from=public_key)


def derive_from_secret(secret: SymmetricKey, tag: str, **kwargs) -> SymmetricKey:
    password = Password.from_str(tag)
    derived_key = PBKDF2[kwargs].get_kdf(secret.key).derive(password.key)
    return SymmetricKey(derived_key, tag=tag, derived_from=secret)


def derive_module_secrets(build_secret: SymmetricKey, module_name: str) -> (SymmetricKey, SymmetricKey):
    module_secret = derive_from_secret(build_secret, build_secret.tag + ':' + module_name, ITERATIONS=150_000)
    module_tag = derive_from_secret(build_secret, module_name, ITERATIONS=1_000)
    return module_secret, module_tag


def derive_license_secret(private_key: PrivateKey, public_key: PublicKey, build_name: str) -> SymmetricKey:
    shared_secret = derive_shared_secret(private_key, public_key, build_name)
    return derive_from_secret(shared_secret, build_name)


def derive_license_user_secret(private_key: PrivateKey, public_key: PublicKey, build_name: str) -> SymmetricKey:
    shared_secret = derive_shared_secret(private_key, public_key, build_name)
    return derive_from_secret(shared_secret, build_name)

__signature__ = "MGUCMELsc6WehIO8kBiPGUd09657TmfoZqNLbeKJYGYoSoCdTWvZ6ktrm8mWeG8sS/ztzQIxAI0D6OBGw3JW9v5+qPQYy694Fk+iuggAcgUXKpvpxeiJg7QCkRwN5zlmLSmA2vCFbA=="
