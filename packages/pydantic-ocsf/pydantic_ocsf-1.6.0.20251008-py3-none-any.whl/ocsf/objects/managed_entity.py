import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects._entity import Entity
from ocsf.objects.device import Device
from ocsf.objects.email import Email
from ocsf.objects.group import Group
from ocsf.objects.location import Location
from ocsf.objects.organization import Organization
from ocsf.objects.policy import Policy
from ocsf.objects.user import User


class TypeId(IntEnum):
    UNKNOWN = 0
    DEVICE = 1
    USER = 2
    GROUP = 3
    ORGANIZATION = 4
    POLICY = 5
    EMAIL = 6
    NETWORK_ZONE = 7
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
            "DEVICE": "Device",
            "USER": "User",
            "GROUP": "Group",
            "ORGANIZATION": "Organization",
            "POLICY": "Policy",
            "EMAIL": "Email",
            "NETWORK_ZONE": "Network Zone",
            "OTHER": "Other",
        }
        return name_map[super().name]


class ManagedEntity(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "managed_entity"

    # Recommended
    device: Device | None = None
    email: Email | None = None
    group: Group | None = None
    name: str | None = None
    org: Organization | None = None
    policy: Policy | None = None
    type_id: TypeId | None = None
    uid: str | None = None
    user: User | None = None
    version: str | None = None

    # Optional
    data: dict[str, Any] | None = None
    location: Location | None = None

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

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(getattr(self, field) is None for field in ["name", "uid", "device", "group", "org", "policy", "user"]):
            raise ValueError(
                "At least one of `name`, `uid`, `device`, `group`, `org`, `policy`, `user` must be provided"
            )
        return self
