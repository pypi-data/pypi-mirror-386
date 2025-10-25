import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import AnyUrl, computed_field, model_validator

from ocsf.objects.fingerprint import Fingerprint
from ocsf.objects.object import Object


class TypeId(IntEnum):
    UNKNOWN = 0
    APPLICATION = 1
    OPERATING_SYSTEM = 2
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
            "APPLICATION": "Application",
            "OPERATING_SYSTEM": "Operating System",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Package(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "package"

    # Required
    name: str
    version: str

    # Recommended
    architecture: str | None = None
    type_id: TypeId | None = None

    # Optional
    cpe_name: str | None = None
    epoch: int | None = None
    hash: Fingerprint | None = None
    license: str | None = None
    license_url: AnyUrl | None = None
    package_manager: str | None = None
    package_manager_url: AnyUrl | None = None
    purl: str | None = None
    release: str | None = None
    src_url: AnyUrl | None = None
    uid: str | None = None
    vendor_name: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def type(self) -> str | None:
        if self.type_id is None:
            return None
        return self.type_id.name

    @type.setter
    def type(self, value: str | None) -> None:
        if value is None:
            self.type_id = None
        else:
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
