# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

import base64
import secrets
import typing


class SymmetricKey:
    def __init__(self, key: bytes, *, tag: str | None = None, derived_from: typing.Any = None):
        self._key = key
        self.tag = tag
        self.derived_from = derived_from

    def __eq__(self, other: typing.Self) -> bool:
        return self._key == other._key

    @property
    def key(self) -> bytes:
        return self._key

    @property
    def b64bytes(self) -> bytes:
        return base64.b64encode(self.key)

    @property
    def hexstr(self) -> str:
        return self.key.hex('-', 4)


class Nonce(SymmetricKey):
    def __init__(self, *, tag: str | None = None, length: int = 12):
        super().__init__(secrets.token_bytes(length), tag=tag)

__signature__ = "MGYCMQCY6EmTQ7sEmp20EmaTb2htFS3M9oVZq9gBxFzd8wuM0Q4jDkN9OoiRCedpxIfUsR8CMQCmtY8CUiOb2KhF8Qvr1+MUBJbPTf85mbP0ppYb/oFktI9nAfAr1a3CwC9iLbKHLBk="
