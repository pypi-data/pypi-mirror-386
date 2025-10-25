import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import AnyUrl, computed_field, model_validator

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects._entity import Entity
from ocsf.objects.digital_signature import DigitalSignature
from ocsf.objects.encryption_details import EncryptionDetails
from ocsf.objects.fingerprint import Fingerprint
from ocsf.objects.key_value_object import KeyValueObject
from ocsf.objects.product import Product
from ocsf.objects.url import Url
from ocsf.objects.user import User


class ConfidentialityId(IntEnum):
    UNKNOWN = 0
    NOT_CONFIDENTIAL = 1
    CONFIDENTIAL = 2
    SECRET = 3
    TOP_SECRET = 4
    PRIVATE = 5
    RESTRICTED = 6
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return ConfidentialityId[obj]
        else:
            return ConfidentialityId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "NOT_CONFIDENTIAL": "Not Confidential",
            "CONFIDENTIAL": "Confidential",
            "SECRET": "Secret",
            "TOP_SECRET": "Top Secret",
            "PRIVATE": "Private",
            "RESTRICTED": "Restricted",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DriveTypeId(IntEnum):
    UNKNOWN = 0
    REMOVABLE = 1
    FIXED = 2
    REMOTE = 3
    CD_ROM = 4
    RAM_DISK = 5
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return DriveTypeId[obj]
        else:
            return DriveTypeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "REMOVABLE": "Removable",
            "FIXED": "Fixed",
            "REMOTE": "Remote",
            "CD_ROM": "CD-ROM",
            "RAM_DISK": "RAM Disk",
            "OTHER": "Other",
        }
        return name_map[super().name]


class TypeId(IntEnum):
    UNKNOWN = 0
    REGULAR_FILE = 1
    FOLDER = 2
    CHARACTER_DEVICE = 3
    BLOCK_DEVICE = 4
    LOCAL_SOCKET = 5
    NAMED_PIPE = 6
    SYMBOLIC_LINK = 7
    EXECUTABLE_FILE = 8
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return TypeId[obj]
        else:
            return TypeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "REGULAR_FILE": "Regular File",
            "FOLDER": "Folder",
            "CHARACTER_DEVICE": "Character Device",
            "BLOCK_DEVICE": "Block Device",
            "LOCAL_SOCKET": "Local Socket",
            "NAMED_PIPE": "Named Pipe",
            "SYMBOLIC_LINK": "Symbolic Link",
            "EXECUTABLE_FILE": "Executable File",
            "OTHER": "Other",
        }
        return name_map[super().name]


class File(Entity):
    allowed_profiles: ClassVar[list[str]] = ["data_classification"]
    schema_name: ClassVar[str] = "file"

    # Required
    name: str
    type_id: TypeId

    # Recommended
    ext: str | None = None
    hashes: list[Fingerprint] | None = None
    path: str | None = None

    # Optional
    accessed_time: Timestamp | None = None
    accessor: User | None = None
    attributes: int | None = None
    company_name: str | None = None
    confidentiality_id: ConfidentialityId | None = None
    created_time: Timestamp | None = None
    creator: User | None = None
    desc: str | None = None
    drive_type_id: DriveTypeId | None = None
    encryption_details: EncryptionDetails | None = None
    internal_name: str | None = None
    is_deleted: bool | None = None
    is_encrypted: bool | None = None
    is_public: bool | None = None
    is_readonly: bool | None = None
    is_system: bool | None = None
    mime_type: str | None = None
    modified_time: Timestamp | None = None
    modifier: User | None = None
    owner: User | None = None
    parent_folder: str | None = None
    product: Product | None = None
    security_descriptor: str | None = None
    signature: DigitalSignature | None = None
    size: int | None = None
    storage_class: str | None = None
    tags: list[KeyValueObject] | None = None
    uid: str | None = None
    uri: AnyUrl | None = None
    url: Url | None = None
    version: str | None = None
    volume: str | None = None
    xattributes: dict[str, Any] | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def confidentiality(self) -> str | None:
        if self.confidentiality_id is None:
            return None
        return self.confidentiality_id.name

    @confidentiality.setter
    def confidentiality(self, value: str | None) -> None:
        if value is None:
            self.confidentiality_id = None
        else:
            self.confidentiality_id = ConfidentialityId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_confidentiality_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "confidentiality" in data and "confidentiality_id" not in data:
            confidentiality = re.sub(r"\W", "_", data.pop("confidentiality").upper())
            data["confidentiality_id"] = ConfidentialityId[confidentiality]
        return data

    @model_validator(mode="after")
    def validate_confidentiality_after(self) -> Self:
        if self.__pydantic_extra__ and "confidentiality" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("confidentiality")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def drive_type(self) -> str | None:
        if self.drive_type_id is None:
            return None
        return self.drive_type_id.name

    @drive_type.setter
    def drive_type(self, value: str | None) -> None:
        if value is None:
            self.drive_type_id = None
        else:
            self.drive_type_id = DriveTypeId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_drive_type_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "drive_type" in data and "drive_type_id" not in data:
            drive_type = re.sub(r"\W", "_", data.pop("drive_type").upper())
            data["drive_type_id"] = DriveTypeId[drive_type]
        return data

    @model_validator(mode="after")
    def validate_drive_type_after(self) -> Self:
        if self.__pydantic_extra__ and "drive_type" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("drive_type")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def type(self) -> str:
        return self.type_id.name

    @type.setter
    def type(self, value: str) -> None:
        self.type_id = TypeId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_type_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "type" in data and "type_id" not in data:
            type = re.sub(r"\W", "_", data.pop("type").upper())
            data["type_id"] = TypeId[type]
        return data

    @model_validator(mode="after")
    def validate_type_after(self) -> Self:
        if self.__pydantic_extra__ and "type" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("type")
        return self
