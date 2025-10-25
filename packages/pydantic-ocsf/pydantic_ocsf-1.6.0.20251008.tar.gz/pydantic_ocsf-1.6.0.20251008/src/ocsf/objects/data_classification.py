import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import AnyUrl, computed_field, model_validator

from ocsf.objects.classifier_details import ClassifierDetails
from ocsf.objects.discovery_details import DiscoveryDetails
from ocsf.objects.object import Object
from ocsf.objects.policy import Policy


class CategoryId(IntEnum):
    UNKNOWN = 0
    PERSONAL = 1
    GOVERNMENTAL = 2
    FINANCIAL = 3
    BUSINESS = 4
    MILITARY_AND_LAW_ENFORCEMENT = 5
    SECURITY = 6
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return CategoryId[obj]
        else:
            return CategoryId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "PERSONAL": "Personal",
            "GOVERNMENTAL": "Governmental",
            "FINANCIAL": "Financial",
            "BUSINESS": "Business",
            "MILITARY_AND_LAW_ENFORCEMENT": "Military and Law Enforcement",
            "SECURITY": "Security",
            "OTHER": "Other",
        }
        return name_map[super().name]


class ConfidentialityId(IntEnum):
    UNKNOWN = 0
    NOT_CONFIDENTIAL = 1
    CONFIDENTIAL = 2
    SECRET = 3
    TOP_SECRET = 4
    PRIVATE = 5
    RESTRICTED = 6
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return ConfidentialityId[obj]
        else:
            return ConfidentialityId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "NOT_CONFIDENTIAL": "Not Confidential",
            "CONFIDENTIAL": "Confidential",
            "SECRET": "Secret",
            "TOP_SECRET": "Top Secret",
            "PRIVATE": "Private",
            "RESTRICTED": "Restricted",
            "OTHER": "Other",
        }
        return name_map[super().name]


class StatusId(IntEnum):
    UNKNOWN = 0
    COMPLETE = 1
    PARTIAL = 2
    FAIL = 3
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
            "COMPLETE": "Complete",
            "PARTIAL": "Partial",
            "FAIL": "Fail",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DataClassification(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "data_classification"

    # Recommended
    category_id: CategoryId | None = None
    classifier_details: ClassifierDetails | None = None
    confidentiality_id: ConfidentialityId | None = None
    status_id: StatusId | None = None

    # Optional
    discovery_details: list[DiscoveryDetails] | None = None
    policy: Policy | None = None
    size: int | None = None
    src_url: AnyUrl | None = None
    status_details: list[str] | None = None
    total: int | None = None
    uid: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def category(self) -> str | None:
        if self.category_id is None:
            return None
        return self.category_id.name

    @category.setter
    def category(self, value: str | None) -> None:
        if value is None:
            self.category_id = None
        else:
            self.category_id = CategoryId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_category_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "category" in data and "category_id" not in data:
            category = re.sub(r"\W", "_", data.pop("category").upper())
            data["category_id"] = CategoryId[category]
        return data

    @model_validator(mode="after")
    def validate_category_after(self) -> Self:
        if self.__pydantic_extra__ and "category" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("category")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def confidentiality(self) -> str | None:
        if self.confidentiality_id is None:
            return None
        return self.confidentiality_id.name

    @confidentiality.setter
    def confidentiality(self, value: str | None) -> None:
        if value is None:
            self.confidentiality_id = None
        else:
            self.confidentiality_id = ConfidentialityId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_confidentiality_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "confidentiality" in data and "confidentiality_id" not in data:
            confidentiality = re.sub(r"\W", "_", data.pop("confidentiality").upper())
            data["confidentiality_id"] = ConfidentialityId[confidentiality]
        return data

    @model_validator(mode="after")
    def validate_confidentiality_after(self) -> Self:
        if self.__pydantic_extra__ and "confidentiality" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("confidentiality")
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
        if all(getattr(self, field) is None for field in ["category_id", "confidentiality_id"]):
            raise ValueError("At least one of `category_id`, `confidentiality_id` must be provided")
        return self
