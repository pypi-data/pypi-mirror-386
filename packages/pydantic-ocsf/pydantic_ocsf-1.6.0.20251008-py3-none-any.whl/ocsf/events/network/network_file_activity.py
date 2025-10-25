from enum import IntEnum, property as enum_property
from typing import Any, ClassVar

from ocsf.datatypes.timestamp import Timestamp
from ocsf.events.network.network import Network
from ocsf.objects.actor import Actor
from ocsf.objects.file import File
from ocsf.objects.network_connection_info import NetworkConnectionInfo
from ocsf.objects.network_endpoint import NetworkEndpoint


class ActivityId(IntEnum):
    UNKNOWN = 0
    UPLOAD = 1
    DOWNLOAD = 2
    UPDATE = 3
    DELETE = 4
    RENAME = 5
    COPY = 6
    MOVE = 7
    RESTORE = 8
    PREVIEW = 9
    LOCK = 10
    UNLOCK = 11
    SHARE = 12
    UNSHARE = 13
    OPEN = 14
    SYNC = 15
    UNSYNC = 16
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
            "UPLOAD": "Upload",
            "DOWNLOAD": "Download",
            "UPDATE": "Update",
            "DELETE": "Delete",
            "RENAME": "Rename",
            "COPY": "Copy",
            "MOVE": "Move",
            "RESTORE": "Restore",
            "PREVIEW": "Preview",
            "LOCK": "Lock",
            "UNLOCK": "Unlock",
            "SHARE": "Share",
            "UNSHARE": "Unshare",
            "OPEN": "Open",
            "SYNC": "Sync",
            "UNSYNC": "Unsync",
            "OTHER": "Other",
        }
        return name_map[super().name]


class NetworkFileActivity(Network):
    allowed_profiles: ClassVar[list[str]] = [
        "network_proxy",
        "load_balancer",
        "cloud",
        "datetime",
        "host",
        "osint",
        "security_control",
    ]
    class_name: str = "Network File Activity"
    class_uid: int = 4010
    schema_name: ClassVar[str] = "network_file_activity"

    # Required
    activity_id: ActivityId
    actor: Actor
    file: File
    src_endpoint: NetworkEndpoint

    # Recommended
    dst_endpoint: NetworkEndpoint | None = None

    # Optional
    connection_info: NetworkConnectionInfo | None = None
    expiration_time: Timestamp | None = None
