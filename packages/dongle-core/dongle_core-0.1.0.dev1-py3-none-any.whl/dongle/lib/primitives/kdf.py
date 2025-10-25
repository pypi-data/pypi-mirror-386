# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

import abc
import typing

from cryptography.hazmat.primitives import hashes, kdf


class KDF(metaclass=abc.ABCMeta):
    LENGTH = 32
    HASH_ALGORITHM = hashes.SHA256()

    def __class_getitem__(cls, class_dict: dict) -> typing.Type[typing.Self]:
        if class_dict:
            return type(f"{cls.__name__}[{repr(class_dict)}]", (cls, ), class_dict)
        else:
            return cls

    @classmethod
    @abc.abstractmethod
    def get_kdf(cls, salt: bytes) -> kdf.KeyDerivationFunction:
        pass


class PBKDF2(KDF):
    ITERATIONS = 1_200_000

    @classmethod
    def get_kdf(cls, salt: bytes) -> kdf.KeyDerivationFunction:
        from cryptography.hazmat.primitives.kdf import pbkdf2

        return pbkdf2.PBKDF2HMAC(cls.HASH_ALGORITHM, cls.LENGTH, salt, cls.ITERATIONS)


class Scrypt(KDF):
    _CPU_COST = 2**10
    _BLOCK_SIZE = 8
    _PARALLEL = 1

    @classmethod
    def get_kdf(cls, salt: bytes):
        from cryptography.hazmat.primitives.kdf import scrypt

        return scrypt.Scrypt(salt, cls.LENGTH, cls._CPU_COST, cls._BLOCK_SIZE, cls._PARALLEL)

__signature__ = "MGYCMQCUvlSY0OtQuK486GlKjoLurFCrRS/9G2o5tJ/gKPFkc75jmGd1osV1yaaF6SchA3ACMQDmNVQumOl68yJUElY9jvOJqg+fkDCXSRqiTupLMq3GElu9O07SMMW/gJOCHNJ3650="
