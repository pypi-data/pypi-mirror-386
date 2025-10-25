import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects.object import Object
from ocsf.objects.policy import Policy


class TypeId(IntEnum):
    UNKNOWN = 0
    ENDPOINT_DETECTION_AND_RESPONSE = 1
    DATA_LOSS_PREVENTION = 2
    BACKUP___RECOVERY = 3
    PERFORMANCE_MONITORING___OBSERVABILITY = 4
    VULNERABILITY_MANAGEMENT = 5
    LOG_FORWARDING = 6
    MOBILE_DEVICE_MANAGEMENT = 7
    CONFIGURATION_MANAGEMENT = 8
    REMOTE_ACCESS = 9
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
            "ENDPOINT_DETECTION_AND_RESPONSE": "Endpoint Detection and Response",
            "DATA_LOSS_PREVENTION": "Data Loss Prevention",
            "BACKUP___RECOVERY": "Backup & Recovery",
            "PERFORMANCE_MONITORING___OBSERVABILITY": "Performance Monitoring & Observability",
            "VULNERABILITY_MANAGEMENT": "Vulnerability Management",
            "LOG_FORWARDING": "Log Forwarding",
            "MOBILE_DEVICE_MANAGEMENT": "Mobile Device Management",
            "CONFIGURATION_MANAGEMENT": "Configuration Management",
            "REMOTE_ACCESS": "Remote Access",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Agent(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "agent"

    # Recommended
    name: str | None = None
    type_id: TypeId | None = None
    uid: str | None = None

    # Optional
    policies: list[Policy] | None = None
    uid_alt: str | None = None
    vendor_name: str | None = None
    version: str | None = None

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
        if all(getattr(self, field) is None for field in ["uid", "name"]):
            raise ValueError("At least one of `uid`, `name` must be provided")
        return self
