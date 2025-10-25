from enum import IntEnum, property as enum_property
from typing import Annotated, Any, ClassVar

from annotated_types import Ge, Lt

from ocsf.events.network.network import Network
from ocsf.objects.file import File


class ActivityId(IntEnum):
    UNKNOWN = 0
    PUT = 1
    GET = 2
    POLL = 3
    DELETE = 4
    RENAME = 5
    LIST = 6
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
            "PUT": "Put",
            "GET": "Get",
            "POLL": "Poll",
            "DELETE": "Delete",
            "RENAME": "Rename",
            "LIST": "List",
            "OTHER": "Other",
        }
        return name_map[super().name]


class FtpActivity(Network):
    allowed_profiles: ClassVar[list[str]] = [
        "network_proxy",
        "load_balancer",
        "cloud",
        "datetime",
        "host",
        "osint",
        "security_control",
    ]
    class_name: str = "FTP Activity"
    class_uid: int = 4008
    schema_name: ClassVar[str] = "ftp_activity"

    # Required
    activity_id: ActivityId

    # Recommended
    codes: list[int] | None = None
    command: str | None = None
    command_responses: list[str] | None = None
    name: str | None = None
    port: Annotated[int, Ge(0), Lt(65536)] | None = None
    type_: str | None = None

    # Optional
    file: File | None = None
