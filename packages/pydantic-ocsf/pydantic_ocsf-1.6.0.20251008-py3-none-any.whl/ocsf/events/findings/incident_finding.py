import re
from enum import IntEnum, property as enum_property
from typing import Annotated, Any, ClassVar, Literal, Self

from pydantic import AnyUrl, Field, computed_field, model_validator

from ocsf.datatypes.timestamp import Timestamp
from ocsf.events.base_event import BaseEvent
from ocsf.objects.attack import Attack
from ocsf.objects.finding_info import FindingInfo
from ocsf.objects.group import Group
from ocsf.objects.ticket import Ticket
from ocsf.objects.user import User
from ocsf.objects.vendor_attributes import VendorAttributes


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


class PriorityId(IntEnum):
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
            return PriorityId[obj]
        else:
            return PriorityId(obj)

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


class StatusId(IntEnum):
    UNKNOWN = 0
    NEW = 1
    IN_PROGRESS = 2
    ON_HOLD = 3
    RESOLVED = 4
    CLOSED = 5
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
            "NEW": "New",
            "IN_PROGRESS": "In Progress",
            "ON_HOLD": "On Hold",
            "RESOLVED": "Resolved",
            "CLOSED": "Closed",
            "OTHER": "Other",
        }
        return name_map[super().name]


class VerdictId(IntEnum):
    UNKNOWN = 0
    FALSE_POSITIVE = 1
    TRUE_POSITIVE = 2
    DISREGARD = 3
    SUSPICIOUS = 4
    BENIGN = 5
    TEST = 6
    INSUFFICIENT_DATA = 7
    SECURITY_RISK = 8
    MANAGED_EXTERNALLY = 9
    DUPLICATE = 10
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return VerdictId[obj]
        else:
            return VerdictId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "FALSE_POSITIVE": "False Positive",
            "TRUE_POSITIVE": "True Positive",
            "DISREGARD": "Disregard",
            "SUSPICIOUS": "Suspicious",
            "BENIGN": "Benign",
            "TEST": "Test",
            "INSUFFICIENT_DATA": "Insufficient Data",
            "SECURITY_RISK": "Security Risk",
            "MANAGED_EXTERNALLY": "Managed Externally",
            "DUPLICATE": "Duplicate",
            "OTHER": "Other",
        }
        return name_map[super().name]


class IncidentFinding(BaseEvent):
    allowed_profiles: ClassVar[list[str]] = ["incident", "cloud", "datetime", "host", "osint", "security_control"]
    category_name: Annotated[Literal["Findings"], Field(frozen=True)] = "Findings"
    category_uid: Annotated[Literal[2], Field(frozen=True)] = 2
    schema_name: ClassVar[str] = "incident_finding"

    # Required
    activity_id: ActivityId
    finding_info_list: list[FindingInfo]
    status_id: StatusId

    # Recommended
    confidence_id: ConfidenceId | None = None
    desc: str | None = None
    impact_id: ImpactId | None = None
    impact_score: int | None = None
    priority_id: PriorityId | None = None
    src_url: AnyUrl | None = None
    verdict_id: VerdictId | None = None

    # Optional
    assignee: User | None = None
    assignee_group: Group | None = None
    attacks: list[Attack] | None = None
    comment: str | None = None
    confidence_score: int | None = None
    end_time: Timestamp | None = None
    is_suspected_breach: bool | None = None
    start_time: Timestamp | None = None
    ticket: Ticket | None = None
    tickets: list[Ticket] | None = None
    vendor_attributes: VendorAttributes | None = None

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
    def priority(self) -> str | None:
        if self.priority_id is None:
            return None
        return self.priority_id.name

    @priority.setter
    def priority(self, value: str | None) -> None:
        if value is None:
            self.priority_id = None
        else:
            self.priority_id = PriorityId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_priority_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "priority" in data and "priority_id" not in data:
            priority = re.sub(r"\W", "_", data.pop("priority").upper())
            data["priority_id"] = PriorityId[priority]
        return data

    @model_validator(mode="after")
    def validate_priority_after(self) -> Self:
        if self.__pydantic_extra__ and "priority" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("priority")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def status(self) -> str:
        return self.status_id.name

    @status.setter
    def status(self, value: str) -> None:
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

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def verdict(self) -> str | None:
        if self.verdict_id is None:
            return None
        return self.verdict_id.name

    @verdict.setter
    def verdict(self, value: str | None) -> None:
        if value is None:
            self.verdict_id = None
        else:
            self.verdict_id = VerdictId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_verdict_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "verdict" in data and "verdict_id" not in data:
            verdict = re.sub(r"\W", "_", data.pop("verdict").upper())
            data["verdict_id"] = VerdictId[verdict]
        return data

    @model_validator(mode="after")
    def validate_verdict_after(self) -> Self:
        if self.__pydantic_extra__ and "verdict" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("verdict")
        return self

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(getattr(self, field) is None for field in ["assignee", "assignee_group"]):
            raise ValueError("At least one of `assignee`, `assignee_group` must be provided")
        return self
