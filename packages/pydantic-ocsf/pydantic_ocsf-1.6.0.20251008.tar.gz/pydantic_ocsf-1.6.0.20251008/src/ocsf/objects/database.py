import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects._entity import Entity
from ocsf.objects.group import Group


class TypeId(IntEnum):
    UNKNOWN = 0
    RELATIONAL = 1
    NETWORK = 2
    OBJECT_ORIENTED = 3
    CENTRALIZED = 4
    OPERATIONAL = 5
    NOSQL = 6
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
            "RELATIONAL": "Relational",
            "NETWORK": "Network",
            "OBJECT_ORIENTED": "Object Oriented",
            "CENTRALIZED": "Centralized",
            "OPERATIONAL": "Operational",
            "NOSQL": "NoSQL",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Database(Entity):
    allowed_profiles: ClassVar[list[str]] = ["data_classification"]
    schema_name: ClassVar[str] = "database"

    # Required
    type_id: TypeId

    # Recommended
    name: str | None = None
    uid: str | None = None

    # Optional
    created_time: Timestamp | None = None
    desc: str | None = None
    groups: list[Group] | None = None
    modified_time: Timestamp | None = None
    size: int | None = None

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
