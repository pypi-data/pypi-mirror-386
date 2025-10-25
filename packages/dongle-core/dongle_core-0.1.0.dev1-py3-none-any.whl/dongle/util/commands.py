# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

import argparse

from dongle.lib import protocol
from dongle.lib.primitives import Password, DelayedPassword
from dongle.runtime.license import License
from .cli import CLI


cli = CLI()


@cli.command(
    (("-r", "--role", ), dict(action="store", default="vendor")),
    (("name", ), dict(action="store")),
    (("path", ), dict(type=argparse.FileType(encoding="utf-8"))),
)
def keyring_import(args: argparse.Namespace):
    key_file = License.keyring.find_key_file(args.role, args.name)
    key_file.write_text(args.path.read(), encoding="utf-8")


@cli.command(
    (("-r", "--role", ), dict(action="store", default="user")),
    (("-w", "--password"), dict(dest="password", action="store", type=Password.from_str)),
    (("-W", "--ask-passw"), dict(dest="password", action="store_const", const=DelayedPassword.ask)),
    (("name", ), dict(action="store")),
)
def keyring_generate(args: argparse.Namespace):
    private_key = protocol.generate_key(tag=args.name)
    private_key_file = License.keyring.find_key_file(args.role, args.name, private=True)
    private_key_file.write_bytes(private_key.export_pem(password=args.password))

    public_key_file = License.keyring.find_key_file(args.role, args.name)
    public_key_file.write_bytes(private_key.public_key.export_pem())


@cli.command(
    (("-r", "--role", ), dict(action="store", default="user")),
    (("name", ), dict(action="store")),
    (("path", ), dict(type=argparse.FileType("w", encoding="utf-8"))),
)
def keyring_export(args: argparse.Namespace):
    key_file = License.keyring.find_key_file(args.role, args.name)
    args.path.write(key_file.read_text(encoding="utf-8"))

__signature__ = "MGYCMQDati2pSx8TtGDtQp+joMx9uSak8xB2sujwJ53HNUqMjNeSICVnOiH8c13LIikHv9YCMQD/bRZsXSjG/p3Lkl5UXEWLRMLEZ80J7gKSgmfyoIjLH7Dp2ybBKSfdC4+WNQj6rY8="
