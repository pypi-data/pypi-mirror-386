import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.events.network.network import Network


class ActivityId(IntEnum):
    UNKNOWN = 0
    SYMMETRIC_ACTIVE_EXCHANGE = 1
    SYMMETRIC_PASSIVE_RESPONSE = 2
    CLIENT_SYNCHRONIZATION = 3
    SERVER_RESPONSE = 4
    BROADCAST = 5
    CONTROL = 6
    PRIVATE_USE_CASE = 7
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
            "SYMMETRIC_ACTIVE_EXCHANGE": "Symmetric Active Exchange",
            "SYMMETRIC_PASSIVE_RESPONSE": "Symmetric Passive Response",
            "CLIENT_SYNCHRONIZATION": "Client Synchronization",
            "SERVER_RESPONSE": "Server Response",
            "BROADCAST": "Broadcast",
            "CONTROL": "Control",
            "PRIVATE_USE_CASE": "Private Use Case",
            "OTHER": "Other",
        }
        return name_map[super().name]


class StratumId(IntEnum):
    UNKNOWN = 0
    PRIMARY_SERVER = 1
    SECONDARY_SERVER = 2
    UNSYNCHRONIZED = 16
    RESERVED = 17
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return StratumId[obj]
        else:
            return StratumId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "PRIMARY_SERVER": "Primary Server",
            "SECONDARY_SERVER": "Secondary Server",
            "UNSYNCHRONIZED": "Unsynchronized",
            "RESERVED": "Reserved",
            "OTHER": "Other",
        }
        return name_map[super().name]


class NtpActivity(Network):
    allowed_profiles: ClassVar[list[str]] = [
        "network_proxy",
        "load_balancer",
        "cloud",
        "datetime",
        "host",
        "osint",
        "security_control",
    ]
    class_name: str = "NTP Activity"
    class_uid: int = 4013
    schema_name: ClassVar[str] = "ntp_activity"

    # Required
    activity_id: ActivityId
    version: str

    # Recommended
    delay: int | None = None
    dispersion: int | None = None
    precision: int | None = None
    stratum_id: StratumId | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def stratum(self) -> str | None:
        if self.stratum_id is None:
            return None
        return self.stratum_id.name

    @stratum.setter
    def stratum(self, value: str | None) -> None:
        if value is None:
            self.stratum_id = None
        else:
            self.stratum_id = StratumId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_stratum_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "stratum" in data and "stratum_id" not in data:
            stratum = re.sub(r"\W", "_", data.pop("stratum").upper())
            data["stratum_id"] = StratumId[stratum]
        return data

    @model_validator(mode="after")
    def validate_stratum_after(self) -> Self:
        if self.__pydantic_extra__ and "stratum" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("stratum")
        return self
