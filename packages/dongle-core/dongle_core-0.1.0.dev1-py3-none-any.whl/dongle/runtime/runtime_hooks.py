# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

from dongle.runtime.formats import ModuleVerifier, ModuleDecryptor


class RuntimeHook:
    @classmethod
    def init(cls, config: dict, target: object):
        scope_init = getattr(cls, f"init_{config['scope']}", None)
        if scope_init is not None:
            scope_init(config, target)
        else:
            raise AttributeError(f"{config['scope']} not implemented by {cls.__name__}")


class RuntimeAPI(RuntimeHook):
    @staticmethod
    def _dongle_is_encrypted(encrypted):
        def is_encrypted(fullname: str) -> bool:
            parts = fullname.split(".")
            while parts:
                if ".".join(parts) in encrypted:
                    return True
                parts.pop()
            return False
        return is_encrypted

    @staticmethod
    def _dongle_verify(app_key):
        def verify(module_data: bytes) -> bytes:
            return ModuleVerifier(app_key).verify_module(module_data)
        return verify

    @staticmethod
    def _dongle_decrypt(build_secret):
        def decrypt(module_data: bytes) -> bytes:
            return ModuleDecryptor(build_secret()).load_encrypted_module(module_data)
        return decrypt

    @classmethod
    def init_dongle(cls, config, package_dongle):
        package_dongle.encrypted = config.get("encrypted", [])
        package_dongle.suppress_imports = config.get("suppress_imports", [])
        package_dongle.verify = cls._dongle_verify(package_dongle.app_key)
        package_dongle.is_encrypted = cls._dongle_is_encrypted(package_dongle.encrypted)

        if package_dongle.encrypted:
            package_dongle.decrypt = cls._dongle_decrypt(package_dongle.build_secret)


class DeveloperAPI(RuntimeHook):
    @classmethod
    def init_api(cls, config, module_dongle):
        def dump(_self):
            print(_self, module_dongle.module)

        module_dongle.dump = dump


class OptionalFeature(RuntimeHook):
    callbacks = {}

    @classmethod
    def _api_has_feature(cls, all_features, callback):
        def has_feature(self, name):
            return name in all_features and callback(name)
        return has_feature

    @classmethod
    def init_api(cls, config, module_dongle):
        if module_dongle.build_name in cls.callbacks:
            all_features = config.get("optional_features", [])
            module_dongle.has_feature = cls._api_has_feature(all_features, cls.callbacks[module_dongle.build_name])

    @classmethod
    def _license_dongle_callback(cls, license_tag, features):
        def has_feature(name):
            from dongle.lib import protocol
            feature_tag = protocol.derive_from_secret(license_tag, name, LENGTH=12, ITERATIONS=850_000).hexstr
            return feature_tag in features
        return has_feature

    @classmethod
    def init_license(cls, config, license):
        features = license.options.get("addons", [])
        cls.callbacks[license.build_info.build_name] = cls._license_dongle_callback(license.license_tag, features)


class RedistLicense(RuntimeHook):
    pass

__signature__ = "MGYCMQC95e/xE4psS20QknbdbTmH4YFRYVTWvivOBz0x8WSIYTdNmd9+ZTvh+dJi604XajECMQDCT/iIEUG4TGU6T8zJvYPvioDAyKCp2VYq4YPg45NLmw5S0+hDWnkw18VSvq3U8vk="
