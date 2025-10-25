# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

import base64
import pathlib
import types
import typing
from importlib import metadata

from dongle.lib import protocol
from dongle.lib.primitives import PrivateKey, PublicKey, SymmetricKey
from dongle.runtime.formats.ascii_armor import ASCIIArmoredFile
from dongle.runtime.keyring import Keyring


class BuildInfo:
    def __init__(self, app_key: PublicKey, vendor_key: PublicKey, build_name: str):
        self.app_key = app_key
        self.vendor_key = vendor_key
        self.build_name = build_name

    def __str__(self):
        return f"<BuildInfo {self.build_name} for {self.app_name} by {self.vendor_name}>"

    @property
    def app_name(self):
        return self.app_key.tag

    @property
    def vendor_name(self):
        return self.vendor_key.tag

    @classmethod
    def from_package_dongle(cls, package_dongle: types.ModuleType) -> typing.Self:
        return cls(
            package_dongle.app_key,
            package_dongle.vendor_key,
            package_dongle.build_name
        )

    @classmethod
    def from_python_file(cls, dist: metadata.Distribution, dongle_path: pathlib.Path) -> typing.Self:
        # Load file as seperate lines and select keys to extract
        lines = dongle_path.read_text("utf-8").splitlines()
        args = {"vendor_name": None, "build_name": None}

        # Process file line by line and extract key-value-pairs
        for line in lines:
            # Skip lines without assignment.
            if "=" not in line:
                continue

            # Split key and value, unwrap value from quotes
            key, value = line.split(" = ", 1)
            if key in args:
                args[key] = value[1:-1]

            # If all keys were parsed, stop processing
            if all(args.values()):
                break

        # Load keys according to the extracted information
        app_key = License.keyring.load_key("app", dist.name)
        vendor_key = License.keyring.load_key("vendor", args["vendor_name"])

        return cls(vendor_key, app_key, args["build_name"])

    @classmethod
    def from_license(cls, app_info: dict) -> typing.Self:
        return cls(
            PublicKey.import_pem(app_info["key"].encode("ascii"), tag=app_info["name"]),
            License.keyring.load_key("vendor", app_info["vendor"]),
            app_info["build"]
        )


class License:
    keyring = Keyring()

    DONGLE_LICENSE = "DONGLE LICENSE"
    PUBLIC_KEY = "PUBLIC KEY"
    ENCRYPTED_DATA = "ENCRYPTED LICENSE DATA"

    def __init__(self, build_info: BuildInfo, build_secret: SymmetricKey, license_tag: SymmetricKey, options: dict = None):
        self.build_info = build_info
        self.build_secret = build_secret
        self.license_tag = license_tag
        self.options = options

    @classmethod
    def load_license(cls, file_data: [str]) -> (str, [str]):
        license_header, license_data, _ = ASCIIArmoredFile.load_block(cls.DONGLE_LICENSE, file_data)
        license_build = license_header.pop("Build")
        return license_build, license_data

    @classmethod
    def load_key(cls, license_data: [str], build_name: str) -> PublicKey:
        key_header, key_data, (key_start, key_stop) = ASCIIArmoredFile.load_block(cls.PUBLIC_KEY, license_data)
        key_bytes = "\n".join(license_data[key_start:key_stop + 1]).encode("utf-8")
        return PublicKey.import_pem(key_bytes, tag=build_name)

    @classmethod
    def load_encrypted_data(cls, license_data: [str]) -> (bytes, SymmetricKey):
        encrypted_header, encrypted_data, encrypted_range = ASCIIArmoredFile.load_block(
            "ENCRYPTED LICENSE DATA",
            license_data
        )
        encrypted_bytes = base64.b64decode("".join(encrypted_data))
        encrypted_nonce = SymmetricKey(base64.b64decode(encrypted_header.pop("Nonce")))
        return encrypted_bytes, encrypted_nonce

    @classmethod
    def load_user_license(cls, user_key: PrivateKey, vendor_key: PublicKey, build_name: str) -> typing.Self:
        license_file = cls.keyring.find_key_file("license", build_name, private=True)
        if not license_file.is_file():
            from dongle.exceptions import NoLicenseError
            raise NoLicenseError(build_name)

        # Load parameters needed for decryption.
        license_build, license_block = cls.load_license(license_file.read_text("utf-8").splitlines())
        license_key = cls.load_key(license_block, license_build)
        license_crypt, license_nonce = cls.load_encrypted_data(license_block)

        # Run decryption protocol.
        license_secret = protocol.derive_license_secret(user_key, license_key, license_build)
        license_tag = protocol.derive_license_user_secret(user_key, vendor_key, license_build)
        license_bytes = protocol.decrypt_data(license_secret, license_nonce, license_crypt, license_tag)

        # Decode and verify signed JSON data.
        license_info = protocol.verify_json(vendor_key, license_bytes)

        # Create BuildInfo and load build_secret from license data.
        build_info = BuildInfo.from_license(license_info["app"])
        build_secret = SymmetricKey(base64.b64decode(license_info["secret"]), tag=build_info.build_name)
        options = license_info.get("options", {})

        return cls(build_info, build_secret, license_tag, options)

__signature__ = "MGQCMFIFtaPu4AyXMUjnWlmGOAXXBA3vQtgEvn4HOOtdpsNcIiVAQwS2Fb2JIGFQP4fBlQIwZatiO1RwPTfO6WrVh9U48wJUzd8jfZxSxCibzw1jfR5yl1+KNG527IPGMs0KG2FV"
