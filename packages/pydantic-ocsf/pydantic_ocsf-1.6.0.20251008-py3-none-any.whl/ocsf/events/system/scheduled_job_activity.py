from enum import IntEnum, property as enum_property
from typing import Any, ClassVar

from ocsf.events.system.system import System
from ocsf.objects.actor import Actor
from ocsf.objects.job import Job


class ActivityId(IntEnum):
    UNKNOWN = 0
    CREATE = 1
    UPDATE = 2
    DELETE = 3
    ENABLE = 4
    DISABLE = 5
    START = 6
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
            "CREATE": "Create",
            "UPDATE": "Update",
            "DELETE": "Delete",
            "ENABLE": "Enable",
            "DISABLE": "Disable",
            "START": "Start",
            "OTHER": "Other",
        }
        return name_map[super().name]


class ScheduledJobActivity(System):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Scheduled Job Activity"
    class_uid: int = 1006
    schema_name: ClassVar[str] = "scheduled_job_activity"

    # Required
    activity_id: ActivityId
    job: Job

    # Optional
    actor: Actor | None = None
