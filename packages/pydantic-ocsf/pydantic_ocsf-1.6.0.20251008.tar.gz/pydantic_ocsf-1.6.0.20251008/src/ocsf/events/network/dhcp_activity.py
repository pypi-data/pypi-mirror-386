from enum import IntEnum, property as enum_property
from typing import Any, ClassVar

from ocsf.events.network.network import Network
from ocsf.objects.network_endpoint import NetworkEndpoint
from ocsf.objects.network_interface import NetworkInterface


class ActivityId(IntEnum):
    UNKNOWN = 0
    DISCOVER = 1
    OFFER = 2
    REQUEST = 3
    DECLINE = 4
    ACK = 5
    NAK = 6
    RELEASE = 7
    INFORM = 8
    EXPIRE = 9
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
            "DISCOVER": "Discover",
            "OFFER": "Offer",
            "REQUEST": "Request",
            "DECLINE": "Decline",
            "ACK": "Ack",
            "NAK": "Nak",
            "RELEASE": "Release",
            "INFORM": "Inform",
            "EXPIRE": "Expire",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DhcpActivity(Network):
    allowed_profiles: ClassVar[list[str]] = [
        "network_proxy",
        "load_balancer",
        "cloud",
        "datetime",
        "host",
        "osint",
        "security_control",
    ]
    class_name: str = "DHCP Activity"
    class_uid: int = 4004
    schema_name: ClassVar[str] = "dhcp_activity"

    # Required
    activity_id: ActivityId

    # Recommended
    dst_endpoint: NetworkEndpoint | None = None
    is_renewal: bool | None = None
    lease_dur: int | None = None
    relay: NetworkInterface | None = None
    src_endpoint: NetworkEndpoint | None = None
    transaction_uid: str | None = None
