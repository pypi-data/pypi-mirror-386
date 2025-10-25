from enum import IntEnum, property as enum_property
from typing import Any, ClassVar

from ocsf.events.system.system import System
from ocsf.objects.script import Script


class ActivityId(IntEnum):
    UNKNOWN = 0
    EXECUTE = 1
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
            "EXECUTE": "Execute",
            "OTHER": "Other",
        }
        return name_map[super().name]


class ScriptActivity(System):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Script Activity"
    class_uid: int = 1009
    schema_name: ClassVar[str] = "script_activity"

    # Required
    activity_id: ActivityId
    script: Script
