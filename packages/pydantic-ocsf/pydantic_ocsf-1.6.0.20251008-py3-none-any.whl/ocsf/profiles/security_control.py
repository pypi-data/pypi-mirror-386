import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects.attack import Attack
from ocsf.objects.authorization import Authorization
from ocsf.objects.firewall_rule import FirewallRule
from ocsf.objects.malware import Malware
from ocsf.objects.malware_scan_info import MalwareScanInfo
from ocsf.objects.policy import Policy
from ocsf.profiles.base_profile import BaseProfile


class ActionId(IntEnum):
    UNKNOWN = 0
    ALLOWED = 1
    DENIED = 2
    OBSERVED = 3
    MODIFIED = 4
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return ActionId[obj]
        else:
            return ActionId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "ALLOWED": "Allowed",
            "DENIED": "Denied",
            "OBSERVED": "Observed",
            "MODIFIED": "Modified",
            "OTHER": "Other",
        }
        return name_map[super().name]


class ConfidenceId(IntEnum):
    UNKNOWN = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return ConfidenceId[obj]
        else:
            return ConfidenceId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "LOW": "Low",
            "MEDIUM": "Medium",
            "HIGH": "High",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DispositionId(IntEnum):
    UNKNOWN = 0
    ALLOWED = 1
    BLOCKED = 2
    QUARANTINED = 3
    ISOLATED = 4
    DELETED = 5
    DROPPED = 6
    CUSTOM_ACTION = 7
    APPROVED = 8
    RESTORED = 9
    EXONERATED = 10
    CORRECTED = 11
    PARTIALLY_CORRECTED = 12
    UNCORRECTED = 13
    DELAYED = 14
    DETECTED = 15
    NO_ACTION = 16
    LOGGED = 17
    TAGGED = 18
    ALERT = 19
    COUNT = 20
    RESET = 21
    CAPTCHA = 22
    CHALLENGE = 23
    ACCESS_REVOKED = 24
    REJECTED = 25
    UNAUTHORIZED = 26
    ERROR = 27
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return DispositionId[obj]
        else:
            return DispositionId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "ALLOWED": "Allowed",
            "BLOCKED": "Blocked",
            "QUARANTINED": "Quarantined",
            "ISOLATED": "Isolated",
            "DELETED": "Deleted",
            "DROPPED": "Dropped",
            "CUSTOM_ACTION": "Custom Action",
            "APPROVED": "Approved",
            "RESTORED": "Restored",
            "EXONERATED": "Exonerated",
            "CORRECTED": "Corrected",
            "PARTIALLY_CORRECTED": "Partially Corrected",
            "UNCORRECTED": "Uncorrected",
            "DELAYED": "Delayed",
            "DETECTED": "Detected",
            "NO_ACTION": "No Action",
            "LOGGED": "Logged",
            "TAGGED": "Tagged",
            "ALERT": "Alert",
            "COUNT": "Count",
            "RESET": "Reset",
            "CAPTCHA": "Captcha",
            "CHALLENGE": "Challenge",
            "ACCESS_REVOKED": "Access Revoked",
            "REJECTED": "Rejected",
            "UNAUTHORIZED": "Unauthorized",
            "ERROR": "Error",
            "OTHER": "Other",
        }
        return name_map[super().name]


class RiskLevelId(IntEnum):
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return RiskLevelId[obj]
        else:
            return RiskLevelId(obj)

    @enum_property
    def name(self):
        name_map = {
            "INFO": "Info",
            "LOW": "Low",
            "MEDIUM": "Medium",
            "HIGH": "High",
            "CRITICAL": "Critical",
            "OTHER": "Other",
        }
        return name_map[super().name]


class SecurityControl(BaseProfile):
    schema_name: ClassVar[str] = "security_control"

    # Recommended
    action_id: ActionId | None = None
    confidence_id: ConfidenceId | None = None
    disposition_id: DispositionId | None = None
    is_alert: bool | None = None

    # Optional
    attacks: list[Attack] | None = None
    authorizations: list[Authorization] | None = None
    confidence_score: int | None = None
    firewall_rule: FirewallRule | None = None
    malware: list[Malware] | None = None
    malware_scan_info: MalwareScanInfo | None = None
    policy: Policy | None = None
    risk_details: str | None = None
    risk_level_id: RiskLevelId | None = None
    risk_score: int | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def action(self) -> str | None:
        if self.action_id is None:
            return None
        return self.action_id.name

    @action.setter
    def action(self, value: str | None) -> None:
        if value is None:
            self.action_id = None
        else:
            self.action_id = ActionId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_action_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "action" in data and "action_id" not in data:
            action = re.sub(r"\W", "_", data.pop("action").upper())
            data["action_id"] = ActionId[action]
        return data

    @model_validator(mode="after")
    def validate_action_after(self) -> Self:
        if self.__pydantic_extra__ and "action" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("action")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def confidence(self) -> str | None:
        if self.confidence_id is None:
            return None
        return self.confidence_id.name

    @confidence.setter
    def confidence(self, value: str | None) -> None:
        if value is None:
            self.confidence_id = None
        else:
            self.confidence_id = ConfidenceId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_confidence_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "confidence" in data and "confidence_id" not in data:
            confidence = re.sub(r"\W", "_", data.pop("confidence").upper())
            data["confidence_id"] = ConfidenceId[confidence]
        return data

    @model_validator(mode="after")
    def validate_confidence_after(self) -> Self:
        if self.__pydantic_extra__ and "confidence" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("confidence")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def disposition(self) -> str | None:
        if self.disposition_id is None:
            return None
        return self.disposition_id.name

    @disposition.setter
    def disposition(self, value: str | None) -> None:
        if value is None:
            self.disposition_id = None
        else:
            self.disposition_id = DispositionId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_disposition_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "disposition" in data and "disposition_id" not in data:
            disposition = re.sub(r"\W", "_", data.pop("disposition").upper())
            data["disposition_id"] = DispositionId[disposition]
        return data

    @model_validator(mode="after")
    def validate_disposition_after(self) -> Self:
        if self.__pydantic_extra__ and "disposition" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("disposition")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def risk_level(self) -> str | None:
        if self.risk_level_id is None:
            return None
        return self.risk_level_id.name

    @risk_level.setter
    def risk_level(self, value: str | None) -> None:
        if value is None:
            self.risk_level_id = None
        else:
            self.risk_level_id = RiskLevelId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_risk_level_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "risk_level" in data and "risk_level_id" not in data:
            risk_level = re.sub(r"\W", "_", data.pop("risk_level").upper())
            data["risk_level_id"] = RiskLevelId[risk_level]
        return data

    @model_validator(mode="after")
    def validate_risk_level_after(self) -> Self:
        if self.__pydantic_extra__ and "risk_level" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("risk_level")
        return self
