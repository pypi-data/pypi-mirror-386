import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.events.findings.finding import Finding
from ocsf.objects.anomaly_analysis import AnomalyAnalysis
from ocsf.objects.evidences import Evidences
from ocsf.objects.malware import Malware
from ocsf.objects.malware_scan_info import MalwareScanInfo
from ocsf.objects.remediation import Remediation
from ocsf.objects.resource_details import ResourceDetails
from ocsf.objects.vulnerability import Vulnerability


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


class DetectionFinding(Finding):
    allowed_profiles: ClassVar[list[str]] = ["incident", "cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Detection Finding"
    class_uid: int = 2004
    schema_name: ClassVar[str] = "detection_finding"

    # Recommended
    confidence_id: ConfidenceId | None = None
    evidences: list[Evidences] | None = None
    is_alert: bool | None = None
    resources: list[ResourceDetails] | None = None

    # Optional
    anomaly_analyses: list[AnomalyAnalysis] | None = None
    confidence_score: int | None = None
    impact_id: ImpactId | None = None
    impact_score: int | None = None
    malware: list[Malware] | None = None
    malware_scan_info: MalwareScanInfo | None = None
    remediation: Remediation | None = None
    risk_details: str | None = None
    risk_level_id: RiskLevelId | None = None
    risk_score: int | None = None
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
