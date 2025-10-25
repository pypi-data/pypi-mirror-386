import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects._entity import Entity


class TypeId(IntEnum):
    UNKNOWN = 0
    MANUAL = 1
    SCHEDULED = 2
    UPDATED_CONTENT = 3
    QUARANTINED_ITEMS = 4
    ATTACHED_MEDIA = 5
    USER_LOGON = 6
    ELAM = 7
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
            "MANUAL": "Manual",
            "SCHEDULED": "Scheduled",
            "UPDATED_CONTENT": "Updated Content",
            "QUARANTINED_ITEMS": "Quarantined Items",
            "ATTACHED_MEDIA": "Attached Media",
            "USER_LOGON": "User Logon",
            "ELAM": "ELAM",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Scan(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "scan"

    # Required
    type_id: TypeId

    # Recommended
    name: str | None = None
    uid: str | None = None

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
