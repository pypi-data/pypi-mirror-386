import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.events.findings.finding import Finding
from ocsf.objects.actor import Actor
from ocsf.objects.data_security import DataSecurity
from ocsf.objects.database import Database
from ocsf.objects.databucket import Databucket
from ocsf.objects.device import Device
from ocsf.objects.file import File
from ocsf.objects.network_endpoint import NetworkEndpoint
from ocsf.objects.resource_details import ResourceDetails
from ocsf.objects.table import Table


class ActivityId(IntEnum):
    UNKNOWN = 0
    CREATE = 1
    UPDATE = 2
    CLOSE = 3
    SUPPRESSED = 4
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
            "SUPPRESSED": "Suppressed",
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


class DataSecurityFinding(Finding):
    allowed_profiles: ClassVar[list[str]] = ["incident", "cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Data Security Finding"
    class_uid: int = 2006
    schema_name: ClassVar[str] = "data_security_finding"

    # Required
    activity_id: ActivityId

    # Recommended
    actor: Actor | None = None
    confidence_id: ConfidenceId | None = None
    data_security: DataSecurity | None = None
    database: Database | None = None
    databucket: Databucket | None = None
    device: Device | None = None
    dst_endpoint: NetworkEndpoint | None = None
    file: File | None = None
    is_alert: bool | None = None
    resources: list[ResourceDetails] | None = None
    src_endpoint: NetworkEndpoint | None = None
    table: Table | None = None

    # Optional
    confidence_score: int | None = None
    impact_id: ImpactId | None = None
    impact_score: int | None = None
    risk_details: str | None = None
    risk_level_id: RiskLevelId | None = None
    risk_score: int | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def activity_name(self) -> str:
        return self.activity_id.name

    @activity_name.setter
    def activity_name(self, value: str) -> None:
        self.activity_id = ActivityId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_activity_name_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "activity_name" in data and "activity_id" not in data:
            activity_name = re.sub(r"\W", "_", data.pop("activity_name").upper())
            data["activity_id"] = ActivityId[activity_name]
        return data

    @model_validator(mode="after")
    def validate_activity_name_after(self) -> Self:
        if self.__pydantic_extra__ and "activity_name" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("activity_name")
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
