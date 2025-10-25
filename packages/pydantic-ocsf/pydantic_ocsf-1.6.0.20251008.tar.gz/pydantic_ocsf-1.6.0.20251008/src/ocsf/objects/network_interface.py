import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import IPvAnyAddress, computed_field, model_validator
from pydantic_extra_types.mac_address import MacAddress

from ocsf.objects._entity import Entity
from ocsf.objects.port_info import PortInfo


class TypeId(IntEnum):
    UNKNOWN = 0
    WIRED = 1
    WIRELESS = 2
    MOBILE = 3
    TUNNEL = 4
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return TypeId[obj]
        else:
            return TypeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "WIRED": "Wired",
            "WIRELESS": "Wireless",
            "MOBILE": "Mobile",
            "TUNNEL": "Tunnel",
            "OTHER": "Other",
        }
        return name_map[super().name]


class NetworkInterface(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "network_interface"

    # Recommended
    hostname: str | None = None
    ip: IPvAnyAddress | None = None
    mac: MacAddress | None = None
    name: str | None = None
    type_id: TypeId | None = None

    # Optional
    namespace: str | None = None
    open_ports: list[PortInfo] | None = None
    subnet_prefix: int | None = None
    uid: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def type(self) -> str | None:
        if self.type_id is None:
            return None
        return self.type_id.name

    @type.setter
    def type(self, value: str | None) -> None:
        if value is None:
            self.type_id = None
        else:
            self.type_id = TypeId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_type_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "type" in data and "type_id" not in data:
            type = re.sub(r"\W", "_", data.pop("type").upper())
            data["type_id"] = TypeId[type]
        return data

    @model_validator(mode="after")
    def validate_type_after(self) -> Self:
        if self.__pydantic_extra__ and "type" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("type")
        return self

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(getattr(self, field) is None for field in ["ip", "mac", "name", "hostname", "uid"]):
            raise ValueError("At least one of `ip`, `mac`, `name`, `hostname`, `uid` must be provided")
        return self
