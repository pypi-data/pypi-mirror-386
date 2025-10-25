import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.events.system.system import System
from ocsf.objects.actor import Actor
from ocsf.objects.module import Module
from ocsf.objects.process import Process


class ActivityId(IntEnum):
    UNKNOWN = 0
    LAUNCH = 1
    TERMINATE = 2
    OPEN = 3
    INJECT = 4
    SET_USER_ID = 5
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
            "LAUNCH": "Launch",
            "TERMINATE": "Terminate",
            "OPEN": "Open",
            "INJECT": "Inject",
            "SET_USER_ID": "Set User ID",
            "OTHER": "Other",
        }
        return name_map[super().name]


class InjectionTypeId(IntEnum):
    UNKNOWN = 0
    REMOTE_THREAD = 1
    LOAD_LIBRARY = 2
    QUEUE_APC = 3
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return InjectionTypeId[obj]
        else:
            return InjectionTypeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "REMOTE_THREAD": "Remote Thread",
            "LOAD_LIBRARY": "Load Library",
            "QUEUE_APC": "Queue APC",
            "OTHER": "Other",
        }
        return name_map[super().name]


class ProcessActivity(System):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Process Activity"
    class_uid: int = 1007
    schema_name: ClassVar[str] = "process_activity"

    # Required
    activity_id: ActivityId
    actor: Actor
    process: Process

    # Recommended
    actual_permissions: int | None = None
    exit_code: int | None = None
    injection_type_id: InjectionTypeId | None = None
    module: Module | None = None
    requested_permissions: int | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def injection_type(self) -> str | None:
        if self.injection_type_id is None:
            return None
        return self.injection_type_id.name

    @injection_type.setter
    def injection_type(self, value: str | None) -> None:
        if value is None:
            self.injection_type_id = None
        else:
            self.injection_type_id = InjectionTypeId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_injection_type_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "injection_type" in data and "injection_type_id" not in data:
            injection_type = re.sub(r"\W", "_", data.pop("injection_type").upper())
            data["injection_type_id"] = InjectionTypeId[injection_type]
        return data

    @model_validator(mode="after")
    def validate_injection_type_after(self) -> Self:
        if self.__pydantic_extra__ and "injection_type" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("injection_type")
        return self
