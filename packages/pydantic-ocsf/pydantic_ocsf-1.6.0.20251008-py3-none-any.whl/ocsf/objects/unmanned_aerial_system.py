import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self
from uuid import UUID

from pydantic import computed_field, model_validator

from ocsf.objects.aircraft import Aircraft
from ocsf.objects.device_hw_info import DeviceHwInfo
from ocsf.objects.location import Location


class TypeId(IntEnum):
    UNKNOWN_UNDECLARED = 0
    AIRPLANE = 1
    HELICOPTER = 2
    GYROPLANE = 3
    HYBRID_LIFT = 4
    ORNITHOPTER = 5
    GLIDER = 6
    KITE = 7
    FREE_BALLOON = 8
    CAPTIVE_BALLOON = 9
    AIRSHIP = 10
    FREE_FALL_PARACHUTE = 11
    ROCKET = 12
    TETHERED_POWERED_AIRCRAFT = 13
    GROUND_OBSTACLE = 14
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
            "UNKNOWN_UNDECLARED": "Unknown/Undeclared",
            "AIRPLANE": "Airplane",
            "HELICOPTER": "Helicopter",
            "GYROPLANE": "Gyroplane",
            "HYBRID_LIFT": "Hybrid Lift",
            "ORNITHOPTER": "Ornithopter",
            "GLIDER": "Glider",
            "KITE": "Kite",
            "FREE_BALLOON": "Free Balloon",
            "CAPTIVE_BALLOON": "Captive Balloon",
            "AIRSHIP": "Airship",
            "FREE_FALL_PARACHUTE": "Free Fall/Parachute",
            "ROCKET": "Rocket",
            "TETHERED_POWERED_AIRCRAFT": "Tethered Powered Aircraft",
            "GROUND_OBSTACLE": "Ground Obstacle",
            "OTHER": "Other",
        }
        return name_map[super().name]


class UnmannedAerialSystem(Aircraft):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "unmanned_aerial_system"

    # Recommended
    location: Location | None = None
    serial_number: str | None = None
    type_id: TypeId | None = None
    uid: str | None = None
    uid_alt: str | None = None
    uuid: UUID | None = None

    # Optional
    hw_info: DeviceHwInfo | None = None
    name: str | None = None

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
