from enum import IntEnum, property as enum_property
from typing import Any, ClassVar

from pydantic import model_validator

from ocsf.events.unmanned_systems.unmanned_systems import UnmannedSystems
from ocsf.objects.aircraft import Aircraft
from ocsf.objects.network_endpoint import NetworkEndpoint
from ocsf.objects.network_traffic import NetworkTraffic
from ocsf.objects.unmanned_aerial_system import UnmannedAerialSystem
from ocsf.objects.unmanned_system_operating_area import UnmannedSystemOperatingArea
from ocsf.objects.user import User


class ActivityId(IntEnum):
    UNKNOWN = 0
    CAPTURE = 1
    RECORD = 2
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
            "CAPTURE": "Capture",
            "RECORD": "Record",
            "OTHER": "Other",
        }
        return name_map[super().name]


class AirborneBroadcastActivity(UnmannedSystems):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Airborne Broadcast Activity"
    class_uid: int = 8002
    schema_name: ClassVar[str] = "airborne_broadcast_activity"

    # Required
    activity_id: ActivityId
    unmanned_aerial_system: UnmannedAerialSystem
    unmanned_system_operator: User

    # Recommended
    aircraft: Aircraft | None = None
    protocol_name: str | None = None
    unmanned_system_operating_area: UnmannedSystemOperatingArea | None = None

    # Optional
    dst_endpoint: NetworkEndpoint | None = None
    rssi: int | None = None
    src_endpoint: NetworkEndpoint | None = None
    traffic: NetworkTraffic | None = None

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(
            getattr(self, field) is None
            for field in ["aircraft", "unmanned_aerial_system", "unmanned_system_operating_area"]
        ):
            raise ValueError(
                "At least one of `aircraft`, `unmanned_aerial_system`, `unmanned_system_operating_area` must be provided"
            )
        return self
