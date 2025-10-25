import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects.object import Object
from ocsf.objects.session import Session


class BoundaryId(IntEnum):
    UNKNOWN = 0
    LOCALHOST = 1
    INTERNAL = 2
    EXTERNAL = 3
    SAME_VPC = 4
    INTERNET_VPC_GATEWAY = 5
    VIRTUAL_PRIVATE_GATEWAY = 6
    INTRA_REGION_VPC = 7
    INTER_REGION_VPC = 8
    LOCAL_GATEWAY = 9
    GATEWAY_VPC = 10
    INTERNET_GATEWAY = 11
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return BoundaryId[obj]
        else:
            return BoundaryId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "LOCALHOST": "Localhost",
            "INTERNAL": "Internal",
            "EXTERNAL": "External",
            "SAME_VPC": "Same VPC",
            "INTERNET_VPC_GATEWAY": "Internet/VPC Gateway",
            "VIRTUAL_PRIVATE_GATEWAY": "Virtual Private Gateway",
            "INTRA_REGION_VPC": "Intra-region VPC",
            "INTER_REGION_VPC": "Inter-region VPC",
            "LOCAL_GATEWAY": "Local Gateway",
            "GATEWAY_VPC": "Gateway VPC",
            "INTERNET_GATEWAY": "Internet Gateway",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DirectionId(IntEnum):
    UNKNOWN = 0
    INBOUND = 1
    OUTBOUND = 2
    LATERAL = 3
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return DirectionId[obj]
        else:
            return DirectionId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "INBOUND": "Inbound",
            "OUTBOUND": "Outbound",
            "LATERAL": "Lateral",
            "OTHER": "Other",
        }
        return name_map[super().name]


class ProtocolVerId(IntEnum):
    UNKNOWN = 0
    INTERNET_PROTOCOL_VERSION_4__IPV4_ = 4
    INTERNET_PROTOCOL_VERSION_6__IPV6_ = 6
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return ProtocolVerId[obj]
        else:
            return ProtocolVerId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "INTERNET_PROTOCOL_VERSION_4__IPV4_": "Internet Protocol version 4 (IPv4)",
            "INTERNET_PROTOCOL_VERSION_6__IPV6_": "Internet Protocol version 6 (IPv6)",
            "OTHER": "Other",
        }
        return name_map[super().name]


class NetworkConnectionInfo(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "network_connection_info"

    # Required
    direction_id: DirectionId

    # Recommended
    boundary_id: BoundaryId | None = None
    protocol_name: str | None = None
    protocol_num: int | None = None
    protocol_ver_id: ProtocolVerId | None = None
    uid: str | None = None

    # Optional
    community_uid: str | None = None
    flag_history: str | None = None
    session: Session | None = None
    tcp_flags: int | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def boundary(self) -> str | None:
        if self.boundary_id is None:
            return None
        return self.boundary_id.name

    @boundary.setter
    def boundary(self, value: str | None) -> None:
        if value is None:
            self.boundary_id = None
        else:
            self.boundary_id = BoundaryId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_boundary_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "boundary" in data and "boundary_id" not in data:
            boundary = re.sub(r"\W", "_", data.pop("boundary").upper())
            data["boundary_id"] = BoundaryId[boundary]
        return data

    @model_validator(mode="after")
    def validate_boundary_after(self) -> Self:
        if self.__pydantic_extra__ and "boundary" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("boundary")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def direction(self) -> str:
        return self.direction_id.name

    @direction.setter
    def direction(self, value: str) -> None:
        self.direction_id = DirectionId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_direction_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "direction" in data and "direction_id" not in data:
            direction = re.sub(r"\W", "_", data.pop("direction").upper())
            data["direction_id"] = DirectionId[direction]
        return data

    @model_validator(mode="after")
    def validate_direction_after(self) -> Self:
        if self.__pydantic_extra__ and "direction" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("direction")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def protocol_ver(self) -> str | None:
        if self.protocol_ver_id is None:
            return None
        return self.protocol_ver_id.name

    @protocol_ver.setter
    def protocol_ver(self, value: str | None) -> None:
        if value is None:
            self.protocol_ver_id = None
        else:
            self.protocol_ver_id = ProtocolVerId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_protocol_ver_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "protocol_ver" in data and "protocol_ver_id" not in data:
            protocol_ver = re.sub(r"\W", "_", data.pop("protocol_ver").upper())
            data["protocol_ver_id"] = ProtocolVerId[protocol_ver]
        return data

    @model_validator(mode="after")
    def validate_protocol_ver_after(self) -> Self:
        if self.__pydantic_extra__ and "protocol_ver" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("protocol_ver")
        return self
