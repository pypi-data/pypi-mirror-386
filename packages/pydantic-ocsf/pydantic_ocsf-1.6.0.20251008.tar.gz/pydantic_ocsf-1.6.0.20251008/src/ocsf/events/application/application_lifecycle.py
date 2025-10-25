from enum import IntEnum, property as enum_property
from typing import Any, ClassVar

from ocsf.events.application.application import Application
from ocsf.objects.product import Product


class ActivityId(IntEnum):
    UNKNOWN = 0
    INSTALL = 1
    REMOVE = 2
    START = 3
    STOP = 4
    RESTART = 5
    ENABLE = 6
    DISABLE = 7
    UPDATE = 8
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
            "INSTALL": "Install",
            "REMOVE": "Remove",
            "START": "Start",
            "STOP": "Stop",
            "RESTART": "Restart",
            "ENABLE": "Enable",
            "DISABLE": "Disable",
            "UPDATE": "Update",
            "OTHER": "Other",
        }
        return name_map[super().name]


class ApplicationLifecycle(Application):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Application Lifecycle"
    class_uid: int = 6002
    schema_name: ClassVar[str] = "application_lifecycle"

    # Required
    activity_id: ActivityId
    app: Product
