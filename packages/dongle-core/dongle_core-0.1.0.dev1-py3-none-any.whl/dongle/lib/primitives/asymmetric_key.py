# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

import abc
import typing
import warnings

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from .symmetric_key import SymmetricKey
from .password import DelayedPassword, PasswordInput


class AsymmetricKey(abc.ABC):
    @abc.abstractmethod
    def export_pem(self, *, password: SymmetricKey | None = None) -> bytes:
        pass

    @classmethod
    @abc.abstractmethod
    def import_pem(cls, key_data: bytes, *, tag: str | None = None, password: SymmetricKey | None = None) -> typing.Self:
        pass


class EllipticCurveKey(AsymmetricKey):
    CURVE = ec.SECP384R1()


class PublicKey(EllipticCurveKey):
    def __init__(self, key: ec.EllipticCurvePublicKey, *, tag: str | None = None):
        self.key = key
        self.tag = tag

    def export_pem(self, *, password: SymmetricKey | None = None) -> bytes:
        return self.key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        )

    @classmethod
    def import_pem(cls, key_data: bytes, *, tag: str | None = None, password: SymmetricKey | None = None) -> typing.Self:
        key = serialization.load_pem_public_key(key_data)
        return cls(key, tag=tag)


class PrivateKey(EllipticCurveKey):
    def __init__(self, key: ec.EllipticCurvePrivateKey, *, tag: str | None = None):
        self.key = key
        self.tag = tag

    @property
    def public_key(self):
        return PublicKey(self.key.public_key(), tag=self.tag)

    def export_pem(self, *, password: PasswordInput = DelayedPassword.ask) -> bytes:
        if callable(password):
            new_password = password(self.tag, f"Enter new password for {self.tag}:")
            if not password(self.tag, f"Repeat password for {self.tag}:") == new_password:
                raise ValueError("Passwords mismatch.")
            password = new_password

        if password:
            _encryption = serialization.BestAvailableEncryption(password.key)
        else:
            warnings.warn(f"No password set for private key export of {self.tag}.")
            _encryption = serialization.NoEncryption()

        return self.key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            _encryption
        )

    @classmethod
    def import_pem(cls, key_data: bytes, *, tag: str | None = None, password: SymmetricKey | None = None) -> typing.Self:
        if password:
            password = password.key
        key = serialization.load_pem_private_key(key_data, password)
        return cls(key, tag=tag)

__signature__ = "MGQCME181Pak2lB4KrvvLhEiRcupDwb5hCxn9qvCH9ugIBn17Rj5qeq1xXRWiI7TBI8jdAIwbHTKRjCDu+e+oXYw1kqFa5FDYQy/sjPncxbxB7Ld1v1gPV0877xS46hs4EB0NJIr"
