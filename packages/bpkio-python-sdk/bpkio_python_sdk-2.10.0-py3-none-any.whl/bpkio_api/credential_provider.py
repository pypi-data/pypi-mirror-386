import configparser
import functools
import json
import os
import subprocess
from abc import ABC, abstractmethod
from configparser import SectionProxy
from dataclasses import dataclass
from os import environ, path
from pathlib import Path
from typing import Optional

from loguru import logger

from bpkio_api.defaults import DEFAULT_FQDN

DEFAULT_INI_FILE = path.join(path.expanduser("~"), ".bpkio/tenants")


class TenantCredentialProvider(ABC):
    def __init__(self, *args, **kwargs):
        self.source = "NA"

    @abstractmethod
    def get_api_key(self):
        pass

    @abstractmethod
    def get_username(self):
        pass

    @abstractmethod
    def get_password(self):
        pass

    @abstractmethod
    def store_info(self, info: dict) -> dict:
        """Store credentials and return the modified config to save in the tenant list"""
        pass


class TenantCredentialProviderFromConfigFile(TenantCredentialProvider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tenant_info: SectionProxy = kwargs.get("tenant_info")
        self.source = "config"

    def get_api_key(self):
        return self.tenant_info.get("api_key")

    def get_username(self):
        return self.tenant_info.get("username")

    def get_password(self):
        return self.tenant_info.get("password")

    def store_info(self, info: dict):
        # Just return the credentials as-is since we're storing directly in config
        return info


class TenantCredentialProviderFrom1Password(TenantCredentialProvider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_ref = kwargs.get("item_ref")
        self.item_ref = self.item_ref.strip('"')
        self.source = "1Password"

        self.item_id = self.item_ref.split("/")[3]
        self.vault_name = self.item_ref.split("/")[2]
        if "@" in self.vault_name:
            self.account_uuid = self.vault_name.split("@")[1]
            self.vault_name = self.vault_name.split("@")[0]
        else:
            self.account_uuid = None

        self.item = None

    def get_api_key(self):
        try:
            return self._get_item_field("api key")
        except Exception:
            return self._get_item_field("api_key")

    def get_username(self):
        return self._get_item_field("username")

    def get_password(self):
        return self._get_item_field("password")

    @functools.lru_cache(maxsize=10)
    def _get_item(self):
        if not self.item:
            op_credential = subprocess.run(
                [
                    "op",
                    "item",
                    "get",
                    self.item_id,
                    *(["--account", self.account_uuid] if self.account_uuid else []),
                    "--vault",
                    self.vault_name,
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
            )

            if op_credential.returncode != 0:
                raise Exception(op_credential.stderr)

            response = op_credential.stdout.strip()
            self.item = json.loads(response)

        return self.item

    def _get_item_field(self, field_name: str):
        item = self._get_item()
        fields = item.get("fields", [])

        for field in fields:
            if field.get("id") == field_name:
                return field.get("value")
            if field.get("label") == field_name:
                return field.get("value")

        raise ValueError(
            f"Field `{field_name}` not found in 1Password item `{item.get('title')}`"
        )

    def _get_op_path(self, op_path: str, key: str):
        op_path = op_path.strip('"')
        op_full_path = f"{op_path}/{key}"
        op_credential = subprocess.run(
            ["op", "read", op_full_path], capture_output=True, text=True
        )
        return op_credential.stdout.strip()

    def store_info(self, info: dict) -> dict:
        stored_fields = ["api_key", "username", "password"]

        item = self._get_item()

        for key, value in info.items():
            if key not in stored_fields:
                continue

            found = False
            for field in item["fields"]:
                if field["id"] == key:
                    field["value"] = value
                    found = True
                    break
                elif field["label"] == key:
                    field["value"] = value
                    found = True
                    break
            if not found:
                new_custom_field = {
                    "id": key,
                    "label": key,
                    "value": value,
                    "type": "CONCEALED",
                }
                item["fields"].append(new_custom_field)

        # Save as a temporary JSON file
        temp_file = f"/tmp/{self.item_id}.json"
        with open(temp_file, "w") as f:
            json.dump(item, f)

        op_credential = subprocess.run(
            [
                "op",
                "item",
                "edit",
                self.item_id,
                *(["--account", self.account_uuid] if self.account_uuid else []),
                "--vault",
                self.vault_name,
                "--template",
                temp_file,
            ],
            capture_output=True,
            text=True,
        )
        logger.debug(op_credential.stdout)

        if op_credential.returncode != 0:
            raise Exception(op_credential.stderr)

        # Remove the temporary JSON file
        os.remove(temp_file)

        # remove the keys from the info dict
        for key in stored_fields:
            if key in info:
                info.pop(key)

        return info


@dataclass
class TenantProfile:
    label: str
    id: int
    fqdn: Optional[str] = DEFAULT_FQDN

    provider: Optional[TenantCredentialProvider] = None

    @property
    def username(self):
        return self.provider.get_username()

    @property
    def password(self):
        return self.provider.get_password()

    @property
    def api_key(self):
        return self.provider.get_api_key()

    @property
    def credential_source(self):
        return self.provider.source


class TenantProfileProvider:
    config = configparser.ConfigParser(interpolation=None)

    def __init__(self, filename: Optional[str] = None) -> None:
        f = Path(filename or DEFAULT_INI_FILE)
        if not f.exists():
            f.parent.mkdir(exist_ok=True, parents=True)
            f.touch()

        self._filename = f
        self._read_ini_file()

    @property
    def inifile(self):
        return self._filename

    def get_tenant_profile(self, tenant_label: str):
        tenant_info = self._get_tenant_section(tenant_label)

        provider = tenant_info.get("provider")
        if not provider:
            credential_provider = TenantCredentialProviderFromConfigFile(
                tenant_info=tenant_info
            )
        elif provider.startswith(("op://", '"op://')):
            credential_provider = TenantCredentialProviderFrom1Password(
                item_ref=provider
            )
        else:
            raise NotImplementedError(f"Unsupported credential provider: {provider}")

        tp = TenantProfile(
            label=tenant_label,
            id=tenant_info.getint("id"),
            fqdn=tenant_info.get("fqdn", DEFAULT_FQDN),
            provider=credential_provider,
        )
        return tp

    def list_tenants(self):
        tenants = []
        for section in self.config.sections():
            tenants.append(self.get_tenant_profile(section))

        return tenants

    def has_tenant_label(self, tenant: str, fuzzy: bool = False):
        return tenant in self.config

    def find_matching_tenant_labels(self, tenant: str):
        candidates = []
        for section in self.config.sections():
            if tenant in section:
                candidates.append(section)

        return candidates

    def has_default_tenant(self):
        return self.has_tenant_label("default")

    # --- Core methods to read and write the `tenants` file ---

    def get_tenant_label_from_working_directory(self):
        try:
            with open(".tenant") as f:
                return f.read().strip()
        except Exception:
            return None

    def store_tenant_label_in_working_directory(self, tenant: str):
        with open(".tenant", "w") as f:
            f.write(tenant)

    def _get_tenant_section(self, tenant_label: str | None):
        tenant_section = None
        if tenant_label:
            if tenant_label in self.config:
                # tenant is the key in a section of the config file
                tenant_section = self.config[tenant_label]

            elif tenant_label.isdigit():
                # by tenant ID, in the first section that contains it
                for section in self.config.sections():
                    if (
                        "id" in self.config[section]
                        and self.config[section]["id"] == tenant_label
                    ):
                        tenant_section = self.config[section]

            if not tenant_section:
                raise NoTenantSectionError(
                    f"There is no tenant `{tenant_label}` in the file at {self._filename}"
                )

        if not tenant_section and "default" in self.config:
            # default section
            tenant_section = self.config["default"]

        if not tenant_section:
            raise NoTenantSectionError()

        # # Treat external credential providers
        # if tenant_section.get("api_key").strip('"').startswith("op://"):
        #     tenant_section['api_key'] = self._resolve_1password_credential(tenant_section.get("api_key"))
        #     tenant_section['_cred_source'] = "1Password"
        #     logger.debug(f"Resolved OP credential for tenant `{tenant}`")

        return tenant_section

    def _read_ini_file(self):
        # TODO - warning if the file does not exist
        self.config.read(DEFAULT_INI_FILE)

    def _from_config_file_section(self, tenant: str, key: str) -> str:
        return self.config[tenant][key]

    def _from_env(self, var) -> Optional[str]:
        return environ.get(var)

    def add_tenant(self, key: str, entries: dict):
        self.config[key] = entries
        with open(self._filename, "w") as ini:
            self.config.write(ini)

    def update_tenant(self, tenant_label: str, entries: dict):
        tenant = self.get_tenant_profile(tenant_label)
        remaining_entries = tenant.provider.store_info(entries)
        for key, value in remaining_entries.items():
            self.config[tenant_label][key] = value

        with open(self._filename, "w") as ini:
            self.config.write(ini)

    def remove_tenant(self, key: str):
        self.config.remove_section(key)
        with open(self._filename, "w") as ini:
            self.config.write(ini)

    @staticmethod
    def resolve_platform(platform):
        if platform == "prod":
            return "api.broadpeak.io"
        if platform == "staging":
            return "apidev.ridgeline.fr"
        return platform


class InvalidTenantError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class NoTenantSectionError(Exception):
    def __init__(
        self,
        message: str = "No valid tenant section could be found in the tenant config file",
    ) -> None:
        super().__init__(message)
