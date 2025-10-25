from enum import IntEnum, property as enum_property
from typing import Any, ClassVar

from ocsf.datatypes.timestamp import Timestamp
from ocsf.events.application.application import Application
from ocsf.objects.policy import Policy
from ocsf.objects.scan import Scan


class ActivityId(IntEnum):
    UNKNOWN = 0
    STARTED = 1
    COMPLETED = 2
    CANCELLED = 3
    DURATION_VIOLATION = 4
    PAUSE_VIOLATION = 5
    ERROR = 6
    PAUSED = 7
    RESUMED = 8
    RESTARTED = 9
    DELAYED = 10
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
            "STARTED": "Started",
            "COMPLETED": "Completed",
            "CANCELLED": "Cancelled",
            "DURATION_VIOLATION": "Duration Violation",
            "PAUSE_VIOLATION": "Pause Violation",
            "ERROR": "Error",
            "PAUSED": "Paused",
            "RESUMED": "Resumed",
            "RESTARTED": "Restarted",
            "DELAYED": "Delayed",
            "OTHER": "Other",
        }
        return name_map[super().name]


class ScanActivity(Application):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Scan Activity"
    class_uid: int = 6007
    schema_name: ClassVar[str] = "scan_activity"

    # Required
    activity_id: ActivityId
    scan: Scan

    # Recommended
    command_uid: str | None = None
    duration: int | None = None
    end_time: Timestamp | None = None
    num_detections: int | None = None
    num_files: int | None = None
    num_folders: int | None = None
    num_network_items: int | None = None
    num_processes: int | None = None
    num_registry_items: int | None = None
    num_resolutions: int | None = None
    num_skipped_items: int | None = None
    num_trusted_items: int | None = None
    policy: Policy | None = None
    schedule_uid: str | None = None
    start_time: Timestamp | None = None
    total: int | None = None
