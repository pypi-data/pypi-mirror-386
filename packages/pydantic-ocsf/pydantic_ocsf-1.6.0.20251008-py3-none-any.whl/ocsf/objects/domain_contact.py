import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import EmailStr, computed_field, model_validator

from ocsf.objects.location import Location
from ocsf.objects.object import Object


class TypeId(IntEnum):
    UNKNOWN = 0
    REGISTRANT = 1
    ADMINISTRATIVE = 2
    TECHNICAL = 3
    BILLING = 4
    ABUSE = 5
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
            "REGISTRANT": "Registrant",
            "ADMINISTRATIVE": "Administrative",
            "TECHNICAL": "Technical",
            "BILLING": "Billing",
            "ABUSE": "Abuse",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DomainContact(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "domain_contact"

    # Required
    type_id: TypeId

    # Recommended
    email_addr: EmailStr | None = None
    location: Location | None = None

    # Optional
    name: str | None = None
    phone_number: str | None = None
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
