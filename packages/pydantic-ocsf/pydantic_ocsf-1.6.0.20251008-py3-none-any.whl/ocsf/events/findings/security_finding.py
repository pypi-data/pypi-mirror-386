import re
from enum import IntEnum, property as enum_property
from typing import Annotated, Any, ClassVar, Literal, Self

from pydantic import Field, computed_field, model_validator

from ocsf.events.base_event import BaseEvent
from ocsf.objects.analytic import Analytic
from ocsf.objects.attack import Attack
from ocsf.objects.cis_csc import CisCsc
from ocsf.objects.compliance import Compliance
from ocsf.objects.finding import Finding
from ocsf.objects.kill_chain_phase import KillChainPhase
from ocsf.objects.malware import Malware
from ocsf.objects.process import Process
from ocsf.objects.resource_details import ResourceDetails
from ocsf.objects.vulnerability import Vulnerability


class ActivityId(IntEnum):
    UNKNOWN = 0
    CREATE = 1
    UPDATE = 2
    CLOSE = 3
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
            "CREATE": "Create",
            "UPDATE": "Update",
            "CLOSE": "Close",
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


class ImpactId(IntEnum):
    UNKNOWN = 0
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
            return ImpactId[obj]
        else:
            return ImpactId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "LOW": "Low",
            "MEDIUM": "Medium",
            "HIGH": "High",
            "CRITICAL": "Critical",
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


class StateId(IntEnum):
    UNKNOWN = 0
    NEW = 1
    IN_PROGRESS = 2
    SUPPRESSED = 3
    RESOLVED = 4
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
            "NEW": "New",
            "IN_PROGRESS": "In Progress",
            "SUPPRESSED": "Suppressed",
            "RESOLVED": "Resolved",
            "OTHER": "Other",
        }
        return name_map[super().name]


class SecurityFinding(BaseEvent):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    category_name: Annotated[Literal["Findings"], Field(frozen=True)] = "Findings"
    category_uid: Annotated[Literal[2], Field(frozen=True)] = 2
    schema_name: ClassVar[str] = "security_finding"

    # Required
    activity_id: ActivityId
    finding: Finding
    state_id: StateId

    # Recommended
    analytic: Analytic | None = None
    confidence_id: ConfidenceId | None = None
    confidence_score: int | None = None
    impact_id: ImpactId | None = None
    impact_score: int | None = None
    resources: list[ResourceDetails] | None = None
    risk_level_id: RiskLevelId | None = None
    risk_score: int | None = None

    # Optional
    attacks: list[Attack] | None = None
    cis_csc: list[CisCsc] | None = None
    compliance: Compliance | None = None
    data_sources: list[str] | None = None
    evidence: dict[str, Any] | None = None
    kill_chain: list[KillChainPhase] | None = None
    malware: list[Malware] | None = None
    nist: list[str] | None = None
    process: Process | None = None
    vulnerabilities: list[Vulnerability] | None = None

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
    def impact(self) -> str | None:
        if self.impact_id is None:
            return None
        return self.impact_id.name

    @impact.setter
    def impact(self, value: str | None) -> None:
        if value is None:
            self.impact_id = None
        else:
            self.impact_id = ImpactId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_impact_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "impact" in data and "impact_id" not in data:
            impact = re.sub(r"\W", "_", data.pop("impact").upper())
            data["impact_id"] = ImpactId[impact]
        return data

    @model_validator(mode="after")
    def validate_impact_after(self) -> Self:
        if self.__pydantic_extra__ and "impact" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("impact")
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

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def state(self) -> str:
        return self.state_id.name

    @state.setter
    def state(self, value: str) -> None:
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
