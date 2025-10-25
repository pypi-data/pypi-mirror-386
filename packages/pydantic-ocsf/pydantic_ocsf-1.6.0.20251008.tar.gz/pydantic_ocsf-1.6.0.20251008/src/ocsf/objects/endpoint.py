import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import IPvAnyAddress, computed_field, model_validator
from pydantic_extra_types.mac_address import MacAddress

from ocsf.objects._entity import Entity
from ocsf.objects.agent import Agent
from ocsf.objects.device_hw_info import DeviceHwInfo
from ocsf.objects.location import Location
from ocsf.objects.os import Os
from ocsf.objects.user import User


class TypeId(IntEnum):
    UNKNOWN = 0
    SERVER = 1
    DESKTOP = 2
    LAPTOP = 3
    TABLET = 4
    MOBILE = 5
    VIRTUAL = 6
    IOT = 7
    BROWSER = 8
    FIREWALL = 9
    SWITCH = 10
    HUB = 11
    ROUTER = 12
    IDS = 13
    IPS = 14
    LOAD_BALANCER = 15
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
            "SERVER": "Server",
            "DESKTOP": "Desktop",
            "LAPTOP": "Laptop",
            "TABLET": "Tablet",
            "MOBILE": "Mobile",
            "VIRTUAL": "Virtual",
            "IOT": "IOT",
            "BROWSER": "Browser",
            "FIREWALL": "Firewall",
            "SWITCH": "Switch",
            "HUB": "Hub",
            "ROUTER": "Router",
            "IDS": "IDS",
            "IPS": "IPS",
            "LOAD_BALANCER": "Load Balancer",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Endpoint(Entity):
    allowed_profiles: ClassVar[list[str]] = ["container"]
    schema_name: ClassVar[str] = "endpoint"

    # Recommended
    hostname: str | None = None
    instance_uid: str | None = None
    interface_name: str | None = None
    interface_uid: str | None = None
    ip: IPvAnyAddress | None = None
    name: str | None = None
    owner: User | None = None
    type_id: TypeId | None = None
    uid: str | None = None

    # Optional
    agent_list: list[Agent] | None = None
    domain: str | None = None
    hw_info: DeviceHwInfo | None = None
    location: Location | None = None
    mac: MacAddress | None = None
    os: Os | None = None
    subnet_uid: str | None = None
    vlan_uid: str | None = None
    vpc_uid: str | None = None
    zone: str | None = None

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
        if all(
            getattr(self, field) is None
            for field in ["ip", "uid", "name", "hostname", "instance_uid", "interface_uid", "interface_name"]
        ):
            raise ValueError(
                "At least one of `ip`, `uid`, `name`, `hostname`, `instance_uid`, `interface_uid`, `interface_name` must be provided"
            )
        return self
