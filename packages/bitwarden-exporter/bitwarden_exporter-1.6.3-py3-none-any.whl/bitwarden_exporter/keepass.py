"""
Utilities to transform Bitwarden vault data structures into a KeePass (.kdbx) database.

This module contains a thin abstraction (KeePassStorage) over pykeepass that maps Bitwarden
organizations, collections, folders, and items (including fields, URIs, OTP, SSH keys, and
attachments) to KeePass groups, entries, custom properties, and binaries.
"""

import json
import logging
import os
import urllib.parse
from types import TracebackType
from typing import Any, Dict, List, Optional, Type, Union

from pykeepass import PyKeePass, create_database  # type: ignore
from pykeepass.entry import Entry  # type: ignore
from pykeepass.group import Group  # type: ignore

from . import BitwardenException
from .bw_models import BwField, BwFolder, BwItem, BwOrganization

LOGGER = logging.getLogger(__name__)


class KeePassStorage:
    """
    Adapter that creates and populates a KeePass database using Bitwarden data models.

    This context manager creates a new KDBX database on entering and saves it on exit.

    Attributes:
        _KeePassStorage__py_kee_pass: Internal PyKeePass instance for DB operations.
        _KeePassStorage__my_vault_group: Root group under which personal items are added.
    """

    __py_kee_pass: PyKeePass
    __my_vault_group: Group

    def __init__(self, kdbx_file: str, kdbx_password: str) -> None:
        """
        Initialize a new KeePassStorage context.

        Args:
            kdbx_file: Destination path for the KeePass database file (.kdbx). Must not already exist.
            kdbx_password: Password used to protect the KeePass database.

        Raises:
            BitwardenException: If a file already exists at the given kdbx_file path.
        """
        self.__kdbx_file = os.path.abspath(kdbx_file)
        self.__kdbx_password = kdbx_password
        if os.path.exists(self.__kdbx_file):
            raise BitwardenException(f"KeePass Database already exists at {self.__kdbx_file}")

    def __enter__(self) -> "KeePassStorage":
        """
        Create the KeePass database and initial structure.

        Returns:
            KeePassStorage: The initialized context manager instance.
        """
        LOGGER.warning("Initialization: application is creating a new KeePass database file")
        LOGGER.info("Creating Keepass Database: %s", self.__kdbx_file)
        __kdbx_dir = os.path.dirname(self.__kdbx_file)
        if not os.path.exists(__kdbx_dir):
            LOGGER.warning("Initialization: application is creating destination directory for KeePass file")
            LOGGER.info("Creating Directory %s", __kdbx_dir)
            os.makedirs(__kdbx_dir)
        self.__py_kee_pass = create_database(self.__kdbx_file, password=self.__kdbx_password)

        LOGGER.warning("Initialization: application is creating the root 'My Vault' group in KeePass")
        LOGGER.info("Creating Keepass group My Vault")
        self.__my_vault_group = self.__add_group_recursive(group_path="My Vault")
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        """
        Save the database and translate exceptions to BitwardenException.

        Args:
            exc_type: Exception type, if any, raised within the context.
            exc_value: Exception instance raised within the context.
            traceback: Traceback object for the exception.

        Returns:
            bool | None: True to suppress further exception handling if no error occurred; None otherwise.

        Raises:
            BitwardenException: If saving the database fails, or if an error occurred during processing.
        """
        try:
            self.__py_kee_pass.save()
            LOGGER.warning("Finalization: application saved the KeePass database to disk")
            LOGGER.info("Keepass Database Saved")
        except Exception as e:  # pylint: disable=broad-except
            LOGGER.error("Error in saving Keepass Database %s", e)
            raise BitwardenException("Error in saving Keepass Database") from e

        if exc_type is not None:
            LOGGER.error("Error in processing %s", exc_value)
            raise BitwardenException("Error in processing") from exc_value

        return True

    def __add_group_recursive(self, group_path: str, parent_group: Optional[Group] = None) -> Group:
        """
        Recursively add a group to Keepass
        """
        if not parent_group:
            parent_group = self.__py_kee_pass.root_group

        if group_path.startswith("/"):
            group_path = group_path[1:]

        if group_path.endswith("/"):
            group_path = group_path[:-1]

        if group_path == "":
            raise BitwardenException("Group Path is empty")

        existing_subgroups: List[Group] = parent_group.subgroups
        if "/" in group_path:
            group_name = group_path.split("/")[0]
            for subgroup in existing_subgroups:
                if subgroup.name == group_name:
                    return self.__add_group_recursive(
                        group_path="/".join(group_path.split("/")[1:]), parent_group=subgroup
                    )
            new_group = self.__py_kee_pass.add_group(parent_group, group_name=group_name)
            return self.__add_group_recursive(group_path="/".join(group_path.split("/")[1:]), parent_group=new_group)
        for subgroup in existing_subgroups:
            if subgroup.name == group_path:
                return subgroup
        return self.__py_kee_pass.add_group(parent_group, group_name=group_path)

    def __add_entry(self, group: Group, bw_item: BwItem) -> Entry:
        """
        Add an entry to Keepass
        """
        entry: Union[Entry | Group] = self.__py_kee_pass.add_entry(
            destination_group=group,
            title=bw_item.name,
            username="" if (not bw_item.login) or (not bw_item.login.username) else bw_item.login.username,
            password="" if (not bw_item.login) or (not bw_item.login.password) else bw_item.login.password,
        )
        LOGGER.warning("KeePass write: application is creating a new entry in the database")
        LOGGER.info("Adding Entry %s", bw_item.name)

        if bw_item.login and bw_item.login.fido2Credentials and len(bw_item.login.fido2Credentials) > 0:
            LOGGER.warning("There is an item with Fido2Credentials. Enable debug logging for more information")
            LOGGER.info("Fido2Credentials are not supported in Keepass for %s", bw_item.name)
            fido2credentials_dict: List[Dict[str, Any]] = [
                fido2Credentials.model_dump() for fido2Credentials in bw_item.login.fido2Credentials
            ]
            fido2field = BwField(name="Fido2Credentials", value=json.dumps(fido2credentials_dict, indent=4), type=1)
            bw_item.fields.append(fido2field)

        if bw_item.sshKey:
            fingerprint = BwField(name="SSHKey fingerprint", value=bw_item.sshKey.keyFingerprint, type=1)
            bw_item.fields.append(fingerprint)

        card_fields = self.__add_card_details_to_item_fields(bw_item)
        bw_item.fields.extend(card_fields)

        identity_fields = self.__add_identity_to_item_fields(bw_item)
        bw_item.fields.extend(identity_fields)

        bw_item.fields += self.__add_uri(entry, bw_item)
        self.__add_fields(entry, bw_item)
        self.__add_attachment(entry, bw_item)
        self.__add_otp(entry, bw_item)

        if bw_item.notes:
            entry.notes = bw_item.notes

        return entry

    @staticmethod
    def __add_card_details_to_item_fields(bw_item: BwItem) -> List[BwField]:
        """
        Add Card to Keepass.
        """
        if bw_item.card:
            card_holder_name = BwField(name="Card-cardholderName", value=bw_item.card.cardholderName or "", type=1)
            card_brand = BwField(name="Card-brand", value=bw_item.card.brand, type=1)
            card_number = BwField(name="Card-number", value=bw_item.card.number or "", type=1)
            card_exp_month = BwField(name="Card-expMonth", value=bw_item.card.expMonth or "", type=1)
            card_exp_year = BwField(name="Card-expYear", value=bw_item.card.expYear or "", type=1)
            card_code = BwField(name="Card-code", value=bw_item.card.code or "", type=1)
            return [card_holder_name, card_brand, card_number, card_exp_month, card_exp_year, card_code]
        return []

    @staticmethod
    def __add_identity_to_item_fields(bw_item: BwItem) -> List[BwField]:
        """
        Add Identity to Keepass.
        """
        if bw_item.identity:
            identity_fields = []
            for key, value in bw_item.identity.model_dump().items():
                if value:
                    identity_fields.append(BwField(name=f"identity-{key}", value=value, type=1))
            return identity_fields
        return []

    @staticmethod
    def __add_uri(entry: Entry, bw_item: BwItem) -> List[BwField]:
        """
        Add URI to Keepass
        """
        if (not bw_item.login) or (not bw_item.login.uris) or len(bw_item.login.uris) == 0:
            return []

        LOGGER.warning("KeePass write: application is adding primary URL and storing extra URIs as fields if needed")
        LOGGER.info("Adding URI for %s", bw_item.name)
        entry.url = bw_item.login.uris[0].uri
        if len(bw_item.login.uris) > 1:
            LOGGER.warning("Multiple URIs are not supported in Keepass. Enable debug logging for more information")
            LOGGER.info(
                "Multiple URIs are not supported in Keepass for %s. Only the first URI will be added; "
                "the rest will be added as fields.",
                bw_item.name,
            )
        uri_list: List[BwField] = []
        for uri in bw_item.login.uris:
            field_name = "URI"
            if uri.match:
                field_name = f"URI-type-{uri.match}"
            uri_item = BwField(name=field_name, value=uri.uri, type=0)
            uri_list.append(uri_item)
        return uri_list

    @staticmethod
    def __add_otp(entry: Entry, bw_item: BwItem) -> None:
        """
        Add OTP to Keepass
        """
        if (not bw_item.login) or (not bw_item.login.totp):
            return None

        LOGGER.warning("KeePass write: application is attaching TOTP/OTP configuration to the entry")
        LOGGER.info("Adding OTP for %s", bw_item.name)
        if not bw_item.login.totp.startswith("otpauth://"):
            url_safe_totp = bw_item.login.totp.replace(" ", "").lower()
            url_safe_name = urllib.parse.quote_plus(bw_item.name)
            bw_item.login.totp = (
                f"otpauth://totp/{url_safe_name}?secret={url_safe_totp}"
                f"&issuer={url_safe_name}&algorithm=SHA1&digits=6&period=30"
            )
            bw_item.login.totp = bw_item.login.totp
        entry.otp = bw_item.login.totp
        return None

    def __fix_duplicate_field_names(self, entry: Entry, item: BwItem) -> None:
        """
        Fix duplicate field names
        """
        all_field_names = [] + list(entry.custom_properties.keys())
        for field in item.fields:
            if field.name in all_field_names:
                LOGGER.warning("Duplicate field name detected. Enable debug logging for more information")
                LOGGER.info('%s: Field with name "%s" already exists, Adding -1', item.name, field.name)
                field.name = f"{field.name}-1"
                self.__fix_duplicate_field_names(entry, item)
            if field.name == "otp":
                LOGGER.warning("Reserved field name detected. Enable debug logging for more information")
                LOGGER.info("%s: Field with name otp is reserved in keepass, Changing to otp-1", item.name)
                field.name = "otp-1"
                self.__fix_duplicate_field_names(entry, item)
            all_field_names.append(field.name)

    def __add_fields(self, entry: Entry, item: BwItem) -> None:  # pylint: disable=too-many-branches
        """
        Add fields to Keepass
        """
        LOGGER.warning("KeePass write: application is adding Bitwarden custom fields into KeePass custom properties")
        LOGGER.info("%s: Adding Custom Fields to custom_properties", item.name)
        self.__fix_duplicate_field_names(entry, item)
        for field in item.fields:
            if field.type == 0:
                if field.value:
                    entry.set_custom_property(field.name, field.value, protect=False)
                else:
                    entry.set_custom_property(field.name, "", protect=False)
            elif field.type == 1:
                if field.value:
                    entry.set_custom_property(field.name, field.value, protect=True)
                else:
                    entry.set_custom_property(field.name, "", protect=True)
            elif field.type == 2:
                entry.set_custom_property(field.name, field.value, protect=False)
            elif field.type == 3 and field.linkedId:
                if field.linkedId == 100:
                    entry.set_custom_property(field.name, "Linked to Username", protect=False)
                elif field.linkedId == 101:
                    entry.set_custom_property(field.name, "Linked to Password", protect=False)
                else:
                    raise BitwardenException(f"{item.name}:: {field.name}:: Unknown linkedId {field.linkedId}")
            else:
                raise BitwardenException(f"{item.name}:: {field.name}:: Unknown Field Type {field.type}")

    def __fix_duplicate_attachment_names(self, entry: Entry, item: BwItem) -> None:
        """
        Fix duplicate attachment names
        """
        all_attachment_names = [] + [attachment.fileName for attachment in entry.attachments]
        for attachment in item.attachments:
            if attachment.fileName in all_attachment_names:
                LOGGER.warning("Duplicate attachment name detected. Enable debug logging for more information")
                LOGGER.info('%s: Attachment with name "%s" already exists, Adding -1', item.name, attachment.fileName)
                attachment.fileName = f"{attachment.fileName}-1"
                self.__fix_duplicate_attachment_names(entry, item)
            all_attachment_names.append(attachment.fileName)

    def __add_attachment(self, entry: Entry, item: BwItem) -> None:
        """
        Add an attachment to Keepass
        """
        LOGGER.warning("KeePass write: application is attaching downloaded Bitwarden files to the entry")
        LOGGER.info("%s: Adding Attachments", item.name)
        self.__fix_duplicate_attachment_names(entry, item)
        for attachment in item.attachments:
            LOGGER.warning("KeePass write: application is embedding an attachment binary into the KeePass entry")
            LOGGER.info('%s: Adding Attachment to keepass "%s"', item.name, attachment.fileName)
            with open(attachment.local_file_path, "rb") as file_attach:
                binary_id = self.__py_kee_pass.add_binary(data=file_attach.read(), protected=True, compressed=False)
                entry.add_attachment(binary_id, attachment.fileName)

    def process_organizations(self, bw_organizations: Dict[str, BwOrganization]) -> None:
        """
        Function to write to Keepass
        """

        for organization in bw_organizations.values():
            LOGGER.warning("KeePass write: application is creating groups for a Bitwarden organization")
            LOGGER.info("Processing Organization %s", organization.name)
            organization_group: Group = self.__add_group_recursive(group_path=organization.name)
            collections = organization.collections
            organization.collections = {}
            organization_group.notes = json.dumps(organization.model_dump(), indent=4)
            for collection in collections.values():
                LOGGER.warning("KeePass write: application is creating a collection group under the organization")
                LOGGER.info("%s:: Processing Collection %s", organization.name, collection.name)
                collection_group = self.__add_group_recursive(
                    group_path=collection.name, parent_group=organization_group
                )
                items = collection.items
                collection.items = {}
                collection_group.notes = json.dumps(collection.model_dump(), indent=4)
                for item in items.values():
                    LOGGER.warning("KeePass write: application is converting a Bitwarden item into a KeePass entry")
                    LOGGER.info("%s::%s:: Processing Item %s", organization.name, collection.name, item.name)
                    try:
                        self.__add_entry(collection_group, item)
                    except Exception as e:  # pylint: disable=broad-except
                        LOGGER.error("Error adding entry %s", e)
                        raise BitwardenException("Error adding entry") from e

    def process_folders(self, bw_folders: Dict[str, BwFolder]) -> None:
        """
        Function to write to Keepass
        """

        for folder in bw_folders.values():
            if folder.name == "No Folder":
                continue
            LOGGER.warning("KeePass write: application is creating a personal folder group in 'My Vault'")
            LOGGER.info("Processing Folder %s", folder.name)
            folder_group: Group = self.__add_group_recursive(group_path=folder.name, parent_group=self.__my_vault_group)
            items = folder.items
            folder.items = {}
            folder_group.notes = json.dumps(folder.model_dump(), indent=4)
            for item in items.values():
                LOGGER.warning("KeePass write: application is adding an item from a personal folder into KeePass")
                LOGGER.info("%s:: Processing Item %s", folder.name, item.name)
                try:
                    self.__add_entry(folder_group, item)
                except Exception as e:  # pylint: disable=broad-except
                    LOGGER.error("Error adding entry %s", e)
                    raise BitwardenException("Error adding entry") from e

    def process_no_folder_items(self, no_folder_items: List[BwItem]) -> None:
        """
        Function to write to Keepass
        """

        LOGGER.warning("KeePass write: application is adding items that are not assigned to any folder")
        LOGGER.info("Processing Items with no Folder")
        for item in no_folder_items:
            LOGGER.warning("KeePass write: application is adding an ungrouped item into 'My Vault'")
            LOGGER.info("Processing Item %s", item.name)
            try:
                self.__add_entry(self.__my_vault_group, item)
            except Exception as e:
                LOGGER.error("Error adding entry %s", e)
                raise BitwardenException("Error adding entry") from e

    def process_bw_exports(self, raw_items: Dict[str, Any]) -> None:
        """
        Function to write to Keepass
        """
        entry: Union[Entry | Group] = self.__py_kee_pass.add_entry(
            destination_group=self.__py_kee_pass.root_group,
            title="Bitwarden Export",
            username="",
            password="",  # nosec CWE-259
        )
        for key, value in raw_items.items():
            binary_id = self.__py_kee_pass.add_binary(
                data=json.dumps(value, indent=4).encode(), protected=True, compressed=False
            )
            entry.add_attachment(binary_id, key)
