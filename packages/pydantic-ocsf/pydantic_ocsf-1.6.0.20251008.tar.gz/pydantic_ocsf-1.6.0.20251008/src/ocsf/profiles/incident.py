import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import AnyUrl, computed_field, model_validator

from ocsf.objects.group import Group
from ocsf.objects.ticket import Ticket
from ocsf.objects.user import User
from ocsf.profiles.base_profile import BaseProfile


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


class Incident(BaseProfile):
    schema_name: ClassVar[str] = "incident"

    # Recommended
    impact_id: ImpactId | None = None
    impact_score: int | None = None
    priority_id: PriorityId | None = None
    src_url: AnyUrl | None = None
    verdict_id: VerdictId | None = None

    # Optional
    assignee: User | None = None
    assignee_group: Group | None = None
    is_suspected_breach: bool | None = None
    ticket: Ticket | None = None
    tickets: list[Ticket] | None = None

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
