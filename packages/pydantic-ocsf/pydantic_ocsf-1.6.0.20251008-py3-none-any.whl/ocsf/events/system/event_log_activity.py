import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.events.system.system import System
from ocsf.objects.actor import Actor
from ocsf.objects.device import Device
from ocsf.objects.file import File
from ocsf.objects.network_endpoint import NetworkEndpoint


class ActivityId(IntEnum):
    UNKNOWN = 0
    CLEAR = 1
    DELETE = 2
    EXPORT = 3
    ARCHIVE = 4
    ROTATE = 5
    START = 6
    STOP = 7
    RESTART = 8
    ENABLE = 9
    DISABLE = 10
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return ActivityId[obj]
        else:
            return ActivityId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "CLEAR": "Clear",
            "DELETE": "Delete",
            "EXPORT": "Export",
            "ARCHIVE": "Archive",
            "ROTATE": "Rotate",
            "START": "Start",
            "STOP": "Stop",
            "RESTART": "Restart",
            "ENABLE": "Enable",
            "DISABLE": "Disable",
            "OTHER": "Other",
        }
        return name_map[super().name]


class LogTypeId(IntEnum):
    UNKNOWN = 0
    OS = 1
    APPLICATION = 2
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return LogTypeId[obj]
        else:
            return LogTypeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "OS": "OS",
            "APPLICATION": "Application",
            "OTHER": "Other",
        }
        return name_map[super().name]


class EventLogActivity(System):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Event Log Activity"
    class_uid: int = 1008
    schema_name: ClassVar[str] = "event_log_activity"

    # Required
    activity_id: ActivityId

    # Recommended
    actor: Actor | None = None
    device: Device | None = None
    dst_endpoint: NetworkEndpoint | None = None
    file: File | None = None
    log_name: str | None = None
    log_provider: str | None = None
    log_type_id: LogTypeId | None = None
    src_endpoint: NetworkEndpoint | None = None
    status_code: str | None = None
    status_detail: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def log_type(self) -> str | None:
        if self.log_type_id is None:
            return None
        return self.log_type_id.name

    @log_type.setter
    def log_type(self, value: str | None) -> None:
        if value is None:
            self.log_type_id = None
        else:
            self.log_type_id = LogTypeId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_log_type_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "log_type" in data and "log_type_id" not in data:
            log_type = re.sub(r"\W", "_", data.pop("log_type").upper())
            data["log_type_id"] = LogTypeId[log_type]
        return data

    @model_validator(mode="after")
    def validate_log_type_after(self) -> Self:
        if self.__pydantic_extra__ and "log_type" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("log_type")
        return self

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(
            getattr(self, field) is None
            for field in ["log_file", "log_name", "log_provider", "log_type", "log_type_id"]
        ):
            raise ValueError(
                "At least one of `log_file`, `log_name`, `log_provider`, `log_type`, `log_type_id` must be provided"
            )
        return self
