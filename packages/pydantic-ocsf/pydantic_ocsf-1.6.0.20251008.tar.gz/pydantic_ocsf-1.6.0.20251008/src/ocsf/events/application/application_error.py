from enum import IntEnum, property as enum_property
from typing import Any, ClassVar

from ocsf.events.application.application import Application


class ActivityId(IntEnum):
    UNKNOWN = 0
    GENERAL_ERROR = 1
    TRANSLATION_ERROR = 2
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
            "GENERAL_ERROR": "General Error",
            "TRANSLATION_ERROR": "Translation Error",
            "OTHER": "Other",
        }
        return name_map[super().name]


class ApplicationError(Application):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Application Error"
    class_uid: int = 6008
    schema_name: ClassVar[str] = "application_error"

    # Required
    activity_id: ActivityId

    # Recommended
    message: str | None = None
