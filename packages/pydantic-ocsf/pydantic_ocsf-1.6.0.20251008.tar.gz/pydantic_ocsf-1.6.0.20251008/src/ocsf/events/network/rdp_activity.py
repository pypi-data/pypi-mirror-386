from enum import IntEnum, property as enum_property
from typing import Any, ClassVar

from ocsf.events.network.network import Network
from ocsf.objects.device import Device
from ocsf.objects.display import Display
from ocsf.objects.file import File
from ocsf.objects.keyboard_info import KeyboardInfo
from ocsf.objects.network_connection_info import NetworkConnectionInfo
from ocsf.objects.request import Request
from ocsf.objects.response import Response
from ocsf.objects.user import User


class ActivityId(IntEnum):
    UNKNOWN = 0
    INITIAL_REQUEST = 1
    INITIAL_RESPONSE = 2
    CONNECT_REQUEST = 3
    CONNECT_RESPONSE = 4
    TLS_HANDSHAKE = 5
    TRAFFIC = 6
    DISCONNECT = 7
    RECONNECT = 8
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
            "INITIAL_REQUEST": "Initial Request",
            "INITIAL_RESPONSE": "Initial Response",
            "CONNECT_REQUEST": "Connect Request",
            "CONNECT_RESPONSE": "Connect Response",
            "TLS_HANDSHAKE": "TLS Handshake",
            "TRAFFIC": "Traffic",
            "DISCONNECT": "Disconnect",
            "RECONNECT": "Reconnect",
            "OTHER": "Other",
        }
        return name_map[super().name]


class RdpActivity(Network):
    allowed_profiles: ClassVar[list[str]] = [
        "network_proxy",
        "load_balancer",
        "cloud",
        "datetime",
        "host",
        "osint",
        "security_control",
    ]
    class_name: str = "RDP Activity"
    class_uid: int = 4005
    schema_name: ClassVar[str] = "rdp_activity"

    # Required
    activity_id: ActivityId

    # Recommended
    certificate_chain: list[str] | None = None
    connection_info: NetworkConnectionInfo | None = None
    protocol_ver: str | None = None
    request: Request | None = None
    response: Response | None = None
    user: User | None = None

    # Optional
    capabilities: list[str] | None = None
    device: Device | None = None
    file: File | None = None
    identifier_cookie: str | None = None
    keyboard_info: KeyboardInfo | None = None
    remote_display: Display | None = None
