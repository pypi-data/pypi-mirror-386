import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.events.discovery.discovery import Discovery
from ocsf.objects.actor import Actor
from ocsf.objects.device import Device
from ocsf.objects.security_state import SecurityState


class PrevSecurityLevelId(IntEnum):
    UNKNOWN = 0
    SECURE = 1
    AT_RISK = 2
    COMPROMISED = 3
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return PrevSecurityLevelId[obj]
        else:
            return PrevSecurityLevelId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "SECURE": "Secure",
            "AT_RISK": "At Risk",
            "COMPROMISED": "Compromised",
            "OTHER": "Other",
        }
        return name_map[super().name]


class SecurityLevelId(IntEnum):
    UNKNOWN = 0
    SECURE = 1
    AT_RISK = 2
    COMPROMISED = 3
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return SecurityLevelId[obj]
        else:
            return SecurityLevelId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "SECURE": "Secure",
            "AT_RISK": "At Risk",
            "COMPROMISED": "Compromised",
            "OTHER": "Other",
        }
        return name_map[super().name]


class StateId(IntEnum):
    UNKNOWN = 0
    DISABLED = 1
    ENABLED = 2
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return StateId[obj]
        else:
            return StateId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "DISABLED": "Disabled",
            "ENABLED": "Enabled",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DeviceConfigStateChange(Discovery):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Device Config State Change"
    class_uid: int = 5019
    schema_name: ClassVar[str] = "device_config_state_change"

    # Required
    device: Device

    # Recommended
    prev_security_level_id: PrevSecurityLevelId | None = None
    prev_security_states: list[SecurityState] | None = None
    security_level_id: SecurityLevelId | None = None
    security_states: list[SecurityState] | None = None
    state_id: StateId | None = None

    # Optional
    actor: Actor | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def prev_security_level(self) -> str | None:
        if self.prev_security_level_id is None:
            return None
        return self.prev_security_level_id.name

    @prev_security_level.setter
    def prev_security_level(self, value: str | None) -> None:
        if value is None:
            self.prev_security_level_id = None
        else:
            self.prev_security_level_id = PrevSecurityLevelId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_prev_security_level_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "prev_security_level" in data and "prev_security_level_id" not in data:
            prev_security_level = re.sub(r"\W", "_", data.pop("prev_security_level").upper())
            data["prev_security_level_id"] = PrevSecurityLevelId[prev_security_level]
        return data

    @model_validator(mode="after")
    def validate_prev_security_level_after(self) -> Self:
        if self.__pydantic_extra__ and "prev_security_level" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("prev_security_level")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def security_level(self) -> str | None:
        if self.security_level_id is None:
            return None
        return self.security_level_id.name

    @security_level.setter
    def security_level(self, value: str | None) -> None:
        if value is None:
            self.security_level_id = None
        else:
            self.security_level_id = SecurityLevelId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_security_level_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "security_level" in data and "security_level_id" not in data:
            security_level = re.sub(r"\W", "_", data.pop("security_level").upper())
            data["security_level_id"] = SecurityLevelId[security_level]
        return data

    @model_validator(mode="after")
    def validate_security_level_after(self) -> Self:
        if self.__pydantic_extra__ and "security_level" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("security_level")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def state(self) -> str | None:
        if self.state_id is None:
            return None
        return self.state_id.name

    @state.setter
    def state(self, value: str | None) -> None:
        if value is None:
            self.state_id = None
        else:
            self.state_id = StateId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_state_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "state" in data and "state_id" not in data:
            state = re.sub(r"\W", "_", data.pop("state").upper())
            data["state_id"] = StateId[state]
        return data

    @model_validator(mode="after")
    def validate_state_after(self) -> Self:
        if self.__pydantic_extra__ and "state" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("state")
        return self
