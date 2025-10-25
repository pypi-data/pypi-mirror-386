from enum import IntEnum, property as enum_property
from typing import Annotated, Any, ClassVar, Literal

from pydantic import Field

from ocsf.events.base_event import BaseEvent


class ActivityId(IntEnum):
    UNKNOWN = 0
    LOG = 1
    COLLECT = 2
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
            "LOG": "Log",
            "COLLECT": "Collect",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Discovery(BaseEvent):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    category_name: Annotated[Literal["Discovery"], Field(frozen=True)] = "Discovery"
    category_uid: Annotated[Literal[5], Field(frozen=True)] = 5
    schema_name: ClassVar[str] = "discovery"

    # Required
    activity_id: ActivityId
