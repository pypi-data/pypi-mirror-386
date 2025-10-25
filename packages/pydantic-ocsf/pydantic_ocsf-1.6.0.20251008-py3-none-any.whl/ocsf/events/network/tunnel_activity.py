import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.events.network.network import Network
from ocsf.objects.device import Device
from ocsf.objects.network_connection_info import NetworkConnectionInfo
from ocsf.objects.network_endpoint import NetworkEndpoint
from ocsf.objects.network_interface import NetworkInterface
from ocsf.objects.network_traffic import NetworkTraffic
from ocsf.objects.session import Session
from ocsf.objects.user import User


class ActivityId(IntEnum):
    UNKNOWN = 0
    OPEN = 1
    CLOSE = 2
    RENEW = 3
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
            "OPEN": "Open",
            "CLOSE": "Close",
            "RENEW": "Renew",
            "OTHER": "Other",
        }
        return name_map[super().name]


class TunnelTypeId(IntEnum):
    UNKNOWN = 0
    SPLIT_TUNNEL = 1
    FULL_TUNNEL = 2
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return TunnelTypeId[obj]
        else:
            return TunnelTypeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "SPLIT_TUNNEL": "Split Tunnel",
            "FULL_TUNNEL": "Full Tunnel",
            "OTHER": "Other",
        }
        return name_map[super().name]


class TunnelActivity(Network):
    allowed_profiles: ClassVar[list[str]] = [
        "network_proxy",
        "load_balancer",
        "cloud",
        "datetime",
        "host",
        "osint",
        "security_control",
    ]
    class_name: str = "Tunnel Activity"
    class_uid: int = 4014
    schema_name: ClassVar[str] = "tunnel_activity"

    # Required
    activity_id: ActivityId

    # Recommended
    device: Device | None = None
    dst_endpoint: NetworkEndpoint | None = None
    session: Session | None = None
    src_endpoint: NetworkEndpoint | None = None
    tunnel_interface: NetworkInterface | None = None
    tunnel_type_id: TunnelTypeId | None = None
    user: User | None = None

    # Optional
    connection_info: NetworkConnectionInfo | None = None
    protocol_name: str | None = None
    traffic: NetworkTraffic | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def tunnel_type(self) -> str | None:
        if self.tunnel_type_id is None:
            return None
        return self.tunnel_type_id.name

    @tunnel_type.setter
    def tunnel_type(self, value: str | None) -> None:
        if value is None:
            self.tunnel_type_id = None
        else:
            self.tunnel_type_id = TunnelTypeId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_tunnel_type_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "tunnel_type" in data and "tunnel_type_id" not in data:
            tunnel_type = re.sub(r"\W", "_", data.pop("tunnel_type").upper())
            data["tunnel_type_id"] = TunnelTypeId[tunnel_type]
        return data

    @model_validator(mode="after")
    def validate_tunnel_type_after(self) -> Self:
        if self.__pydantic_extra__ and "tunnel_type" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("tunnel_type")
        return self

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(
            getattr(self, field) is None
            for field in ["connection_info", "session", "src_endpoint", "traffic", "tunnel_interface", "tunnel_type_id"]
        ):
            raise ValueError(
                "At least one of `connection_info`, `session`, `src_endpoint`, `traffic`, `tunnel_interface`, `tunnel_type_id` must be provided"
            )
        return self
