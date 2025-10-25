# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

import os
import pathlib
import logging

from dongle.lib.primitives import PrivateKey, PublicKey, DelayedPassword, PasswordInput


_log = logging.getLogger(__name__)


class Keyring:
    PRIVATE_KEY_SUFFIX = ".priv"

    def __init__(self, base_dir: pathlib.Path = pathlib.Path(os.environ.get("DONGLE_KEYDIR", "keys"))):
        self.base_dir = base_dir

    def find_key_file(self, role: str, name: str, *, private: bool = False, create_dir: bool = True) -> pathlib.Path:
        if private:
            name = name + self.PRIVATE_KEY_SUFFIX

        key_file = self.base_dir / role / name

        if not key_file.parent.exists() and create_dir:
            _log.info("Create key directory for %s (role %s) at %s.", name, role, key_file.parent)
            key_file.parent.mkdir(0x644, parents=True)

        return key_file

    def generate_key(
            self,
            role: str,
            name: str,
            *,
            password: PasswordInput = DelayedPassword.ask,
            replace_existing: bool = False
    ) -> PrivateKey:
        private_key_file = self.find_key_file(role, name, private=True)
        public_key_file = self.find_key_file(role, name, create_dir=False)

        if not replace_existing:
            if existing_files := [key_file for key_file in (private_key_file, public_key_file) if key_file.exists()]:
                raise FileExistsError(existing_files[0])

        private_key = PrivateKey.generate(tag=name)
        public_key = private_key.public_key

        public_key_file.write_bytes(public_key.export_pem())
        if callable(password):
            password = password(private_key.tag)

        private_key_file.write_bytes(private_key.export_pem(password=password))

        return private_key

    def load_key(self, role: str, name: str, *, private: bool = False, password: PasswordInput = DelayedPassword.ask):
        key_file = self.find_key_file(role, name, private=private, create_dir=False)
        if not key_file.exists():
            raise FileNotFoundError(f"File for {'private' if private else 'public'} {role} key {name} not found.")

        if private:
            cls = PrivateKey
            if callable(password):
                password = password(name, f"Enter password for {role} {{tag}}:")
        else:
            cls = PublicKey

        return cls.import_pem(key_file.read_bytes(), tag=name, password=password)

    def load_or_create_key(
            self,
            role: str,
            name: str,
            *,
            password: PasswordInput = DelayedPassword.ask
    ) -> PrivateKey:
        try:
            private_key = self.load_key(role, name, private=True, password=password)
        except FileNotFoundError:
            private_key = self.generate_key(role, name, password=password)
        return private_key

__signature__ = "MGYCMQC+AKYScV/NFndcH00jsJMo7sg1QfA+lCSS2SCYLeq6Z1AdkgggBVfhhD5cznl1CfoCMQDHmiFxwxmovLMKsE10Bqr+eLR2jrxCj+RrKkj1l4O0S0MDjhUKLIQhmKTOpmG0Zww="
