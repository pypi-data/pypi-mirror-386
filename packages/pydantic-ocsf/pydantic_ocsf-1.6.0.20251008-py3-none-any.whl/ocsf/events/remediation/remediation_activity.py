from enum import IntEnum, property as enum_property
from typing import Annotated, Any, ClassVar, Literal

from pydantic import Field

from ocsf.events.base_event import BaseEvent
from ocsf.objects.d3fend import D3Fend
from ocsf.objects.remediation import Remediation
from ocsf.objects.scan import Scan


class ActivityId(IntEnum):
    UNKNOWN = 0
    ISOLATE = 1
    EVICT = 2
    RESTORE = 3
    HARDEN = 4
    DETECT = 5
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
            "ISOLATE": "Isolate",
            "EVICT": "Evict",
            "RESTORE": "Restore",
            "HARDEN": "Harden",
            "DETECT": "Detect",
            "OTHER": "Other",
        }
        return name_map[super().name]


class StatusId(IntEnum):
    UNKNOWN = 0
    SUCCESS = 1
    FAILURE = 2
    DOES_NOT_EXIST = 3
    PARTIAL = 4
    UNSUPPORTED = 5
    ERROR = 6
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return StatusId[obj]
        else:
            return StatusId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "SUCCESS": "Success",
            "FAILURE": "Failure",
            "DOES_NOT_EXIST": "Does Not Exist",
            "PARTIAL": "Partial",
            "UNSUPPORTED": "Unsupported",
            "ERROR": "Error",
            "OTHER": "Other",
        }
        return name_map[super().name]


class RemediationActivity(BaseEvent):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    category_name: Annotated[Literal["Remediation"], Field(frozen=True)] = "Remediation"
    category_uid: Annotated[Literal[7], Field(frozen=True)] = 7
    schema_name: ClassVar[str] = "remediation_activity"

    # Required
    activity_id: ActivityId
    command_uid: str

    # Recommended
    countermeasures: list[D3Fend] | None = None
    status_id: StatusId | None = None

    # Optional
    remediation: Remediation | None = None
    scan: Scan | None = None
