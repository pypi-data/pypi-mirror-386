import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.events.unmanned_systems.unmanned_systems import UnmannedSystems
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


class AuthProtocolId(IntEnum):
    UNKNOWN = 0
    NONE = 1
    UAS_ID_SIGNATURE = 2
    OPERATOR_ID_SIGNATURE = 3
    MESSAGE_SET_SIGNATURE = 4
    AUTHENTICATION_PROVIDED_BY_NETWORK_REMOTE_ID = 5
    SPECIFIC_AUTHENTICATION_METHOD = 6
    RESERVED = 7
    PRIVATE_USER = 8
    EAP = 9
    RADIUS = 10
    BASIC_AUTHENTICATION = 11
    LDAP = 12
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return AuthProtocolId[obj]
        else:
            return AuthProtocolId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "NONE": "None",
            "UAS_ID_SIGNATURE": "UAS ID Signature",
            "OPERATOR_ID_SIGNATURE": "Operator ID Signature",
            "MESSAGE_SET_SIGNATURE": "Message Set Signature",
            "AUTHENTICATION_PROVIDED_BY_NETWORK_REMOTE_ID": "Authentication Provided by Network Remote ID",
            "SPECIFIC_AUTHENTICATION_METHOD": "Specific Authentication Method",
            "RESERVED": "Reserved",
            "PRIVATE_USER": "Private User",
            "EAP": "EAP",
            "RADIUS": "RADIUS",
            "BASIC_AUTHENTICATION": "Basic Authentication",
            "LDAP": "LDAP",
            "OTHER": "Other",
        }
        return name_map[super().name]


class StatusId(IntEnum):
    UNKNOWN = 0
    UNDECLARED = 1
    GROUND = 2
    AIRBORNE = 3
    EMERGENCY = 4
    REMOTE_ID_SYSTEM_FAILURE = 5
    RESERVED = 6
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return StatusId[obj]
        else:
            return StatusId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "UNDECLARED": "Undeclared",
            "GROUND": "Ground",
            "AIRBORNE": "Airborne",
            "EMERGENCY": "Emergency",
            "REMOTE_ID_SYSTEM_FAILURE": "Remote ID System Failure",
            "RESERVED": "Reserved",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DroneFlightsActivity(UnmannedSystems):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Drone Flights Activity"
    class_uid: int = 8001
    schema_name: ClassVar[str] = "drone_flights_activity"

    # Required
    activity_id: ActivityId
    unmanned_aerial_system: UnmannedAerialSystem
    unmanned_system_operator: User

    # Recommended
    status_id: StatusId | None = None
    unmanned_system_operating_area: UnmannedSystemOperatingArea | None = None

    # Optional
    auth_protocol_id: AuthProtocolId | None = None
    classification: str | None = None
    comment: str | None = None
    protocol_name: str | None = None
    src_endpoint: NetworkEndpoint | None = None
    traffic: NetworkTraffic | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def auth_protocol(self) -> str | None:
        if self.auth_protocol_id is None:
            return None
        return self.auth_protocol_id.name

    @auth_protocol.setter
    def auth_protocol(self, value: str | None) -> None:
        if value is None:
            self.auth_protocol_id = None
        else:
            self.auth_protocol_id = AuthProtocolId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_auth_protocol_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "auth_protocol" in data and "auth_protocol_id" not in data:
            auth_protocol = re.sub(r"\W", "_", data.pop("auth_protocol").upper())
            data["auth_protocol_id"] = AuthProtocolId[auth_protocol]
        return data

    @model_validator(mode="after")
    def validate_auth_protocol_after(self) -> Self:
        if self.__pydantic_extra__ and "auth_protocol" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("auth_protocol")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def status(self) -> str | None:
        if self.status_id is None:
            return None
        return self.status_id.name

    @status.setter
    def status(self, value: str | None) -> None:
        if value is None:
            self.status_id = None
        else:
            self.status_id = StatusId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_status_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "status" in data and "status_id" not in data:
            status = re.sub(r"\W", "_", data.pop("status").upper())
            data["status_id"] = StatusId[status]
        return data

    @model_validator(mode="after")
    def validate_status_after(self) -> Self:
        if self.__pydantic_extra__ and "status" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("status")
        return self

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(
            getattr(self, field) is None
            for field in [
                "src_endpoint",
                "unmanned_aerial_system",
                "unmanned_system_operator",
                "unmanned_system_operating_area",
            ]
        ):
            raise ValueError(
                "At least one of `src_endpoint`, `unmanned_aerial_system`, `unmanned_system_operator`, `unmanned_system_operating_area` must be provided"
            )
        return self
