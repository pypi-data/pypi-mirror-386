# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

import collections.abc
import getpass
import typing

from .symmetric_key import SymmetricKey


class Password(SymmetricKey):
    _DEFAULT_PROMPT = "Enter password for {tag}"

    @classmethod
    def from_str(cls, password: str, *, tag: str | None = None) -> typing.Self:
        return cls(password.encode('utf-8'), tag=tag)

    @classmethod
    def from_input(cls, *, tag: str | None = None, prompt: str | None = None) -> typing.Self:
        prompt = (prompt or cls._DEFAULT_PROMPT).format(tag=tag)
        password = getpass.getpass(prompt)
        return cls.from_str(password, tag=tag)


class DelayedPassword(Password):
    def __init__(self, prompt: str, *, tag: str | None = None, derived_from: typing.Any = None, retain: bool | int = False):
        super().__init__(b'', tag=tag, derived_from=derived_from)

        self.prompt = prompt
        self.cache = None
        self.retain = retain

    @property
    def key(self):
        if self.cache is None:
            cache, retain = Password.from_input(tag=self.tag, prompt=self.prompt), self.retain
        else:
            cache, retain = self.cache

        if isinstance(retain, int):
            retain -= 1
        if retain:
            self.cache = cache, retain
        else:
            self.cache = None

        return cache.key

    @classmethod
    def ask(cls, name: str, prompt: str = "Enter password for {tag}:"):
        return cls(prompt, tag=name)


PasswordInput = typing.Union[
    None,
    Password,
    collections.abc.Callable[[str, typing.Optional[str]], Password]
]

__signature__ = "MGQCMDXLj+/OEvGuiC/eTb5kYC3ZPtRsefdRhMGaQtp2qWoWhN35tf2J4zEls3E0AvLAOwIwP838WRqdAOh9aeTCWv3rEP4SJZjO/baMhTygwiEEOTxqHipV7+wprJ5e7C5ttvyr"
