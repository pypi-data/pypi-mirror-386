from enum import IntEnum, property as enum_property
from typing import Any, ClassVar

from ocsf.events.system.system import System
from ocsf.objects.kernel import Kernel


class ActivityId(IntEnum):
    UNKNOWN = 0
    CREATE = 1
    READ = 2
    DELETE = 3
    INVOKE = 4
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
            "READ": "Read",
            "DELETE": "Delete",
            "INVOKE": "Invoke",
            "OTHER": "Other",
        }
        return name_map[super().name]


class KernelActivity(System):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Kernel Activity"
    class_uid: int = 1003
    schema_name: ClassVar[str] = "kernel_activity"

    # Required
    activity_id: ActivityId
    kernel: Kernel
