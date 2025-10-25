import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects.fingerprint import Fingerprint
from ocsf.objects.object import Object


class RelationshipId(IntEnum):
    UNKNOWN = 0
    DEPENDS_ON = 1
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return RelationshipId[obj]
        else:
            return RelationshipId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "DEPENDS_ON": "Depends On",
            "OTHER": "Other",
        }
        return name_map[super().name]


class TypeId(IntEnum):
    UNKNOWN = 0
    FRAMEWORK = 1
    LIBRARY = 2
    OPERATING_SYSTEM = 3
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
            "FRAMEWORK": "Framework",
            "LIBRARY": "Library",
            "OPERATING_SYSTEM": "Operating System",
            "OTHER": "Other",
        }
        return name_map[super().name]


class SoftwareComponent(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "software_component"

    # Required
    name: str
    version: str

    # Recommended
    author: str | None = None
    purl: str | None = None
    related_component: str | None = None
    relationship_id: RelationshipId | None = None
    type_id: TypeId | None = None

    # Optional
    hash: Fingerprint | None = None
    license: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def relationship(self) -> str | None:
        if self.relationship_id is None:
            return None
        return self.relationship_id.name

    @relationship.setter
    def relationship(self, value: str | None) -> None:
        if value is None:
            self.relationship_id = None
        else:
            self.relationship_id = RelationshipId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_relationship_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "relationship" in data and "relationship_id" not in data:
            relationship = re.sub(r"\W", "_", data.pop("relationship").upper())
            data["relationship_id"] = RelationshipId[relationship]
        return data

    @model_validator(mode="after")
    def validate_relationship_after(self) -> Self:
        if self.__pydantic_extra__ and "relationship" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("relationship")
        return self

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
