import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.encryption_details import EncryptionDetails
from ocsf.objects.object import Object


class TypeId(IntEnum):
    UNKNOWN = 0
    TICKET_GRANTING_TICKET = 1
    SERVICE_TICKET = 2
    IDENTITY_TOKEN = 3
    REFRESH_TOKEN = 4
    SAML_ASSERTION = 5
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
            "TICKET_GRANTING_TICKET": "Ticket Granting Ticket",
            "SERVICE_TICKET": "Service Ticket",
            "IDENTITY_TOKEN": "Identity Token",
            "REFRESH_TOKEN": "Refresh Token",
            "SAML_ASSERTION": "SAML Assertion",
            "OTHER": "Other",
        }
        return name_map[super().name]


class AuthenticationToken(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "authentication_token"

    # Recommended
    created_time: Timestamp | None = None
    encryption_details: EncryptionDetails | None = None
    kerberos_flags: str | None = None
    type_id: TypeId | None = None

    # Optional
    expiration_time: Timestamp | None = None
    is_renewable: bool | None = None

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
