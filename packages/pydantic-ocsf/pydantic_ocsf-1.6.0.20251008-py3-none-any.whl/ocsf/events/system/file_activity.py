from enum import IntEnum, property as enum_property
from typing import Any, ClassVar

from ocsf.events.system.system import System
from ocsf.objects.actor import Actor
from ocsf.objects.file import File


class ActivityId(IntEnum):
    UNKNOWN = 0
    CREATE = 1
    READ = 2
    UPDATE = 3
    DELETE = 4
    RENAME = 5
    SET_ATTRIBUTES = 6
    SET_SECURITY = 7
    GET_ATTRIBUTES = 8
    GET_SECURITY = 9
    ENCRYPT = 10
    DECRYPT = 11
    MOUNT = 12
    UNMOUNT = 13
    OPEN = 14
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
            "UPDATE": "Update",
            "DELETE": "Delete",
            "RENAME": "Rename",
            "SET_ATTRIBUTES": "Set Attributes",
            "SET_SECURITY": "Set Security",
            "GET_ATTRIBUTES": "Get Attributes",
            "GET_SECURITY": "Get Security",
            "ENCRYPT": "Encrypt",
            "DECRYPT": "Decrypt",
            "MOUNT": "Mount",
            "UNMOUNT": "Unmount",
            "OPEN": "Open",
            "OTHER": "Other",
        }
        return name_map[super().name]


class FileActivity(System):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "File System Activity"
    class_uid: int = 1001
    schema_name: ClassVar[str] = "file_activity"

    # Required
    activity_id: ActivityId
    actor: Actor
    file: File

    # Recommended
    component: str | None = None
    create_mask: str | None = None
    file_diff: str | None = None
    file_result: File | None = None

    # Optional
    access_mask: int | None = None
    connection_uid: str | None = None
