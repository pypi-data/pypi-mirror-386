import re
from enum import IntEnum, property as enum_property
from typing import Annotated, Any, ClassVar, Literal, Self

from pydantic import Field, computed_field, model_validator

from ocsf.datatypes.timestamp import Timestamp
from ocsf.events.base_event import BaseEvent
from ocsf.objects.device import Device
from ocsf.objects.finding_info import FindingInfo
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


class StatusId(IntEnum):
    UNKNOWN = 0
    NEW = 1
    IN_PROGRESS = 2
    SUPPRESSED = 3
    RESOLVED = 4
    ARCHIVED = 5
    DELETED = 6
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
            "SUPPRESSED": "Suppressed",
            "RESOLVED": "Resolved",
            "ARCHIVED": "Archived",
            "DELETED": "Deleted",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Finding(BaseEvent):
    allowed_profiles: ClassVar[list[str]] = ["incident", "cloud", "datetime", "host", "osint", "security_control"]
    category_name: Annotated[Literal["Findings"], Field(frozen=True)] = "Findings"
    category_uid: Annotated[Literal[2], Field(frozen=True)] = 2
    schema_name: ClassVar[str] = "finding"

    # Required
    activity_id: ActivityId
    finding_info: FindingInfo

    # Recommended
    confidence_id: ConfidenceId | None = None
    status_id: StatusId | None = None

    # Optional
    comment: str | None = None
    confidence_score: int | None = None
    device: Device | None = None
    end_time: Timestamp | None = None
    start_time: Timestamp | None = None
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
