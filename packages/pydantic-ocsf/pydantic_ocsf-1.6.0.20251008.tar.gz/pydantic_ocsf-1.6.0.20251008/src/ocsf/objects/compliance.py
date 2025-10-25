import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects.assessment import Assessment
from ocsf.objects.check import Check
from ocsf.objects.kb_article import KbArticle
from ocsf.objects.key_value_object import KeyValueObject
from ocsf.objects.object import Object


class StatusId(IntEnum):
    UNKNOWN = 0
    PASS = 1
    WARNING = 2
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
            "PASS": "Pass",
            "WARNING": "Warning",
            "FAIL": "Fail",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Compliance(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "compliance"

    # Recommended
    control: str | None = None
    standards: list[str] | None = None
    status_id: StatusId | None = None

    # Optional
    assessments: list[Assessment] | None = None
    category: str | None = None
    checks: list[Check] | None = None
    compliance_references: list[KbArticle] | None = None
    compliance_standards: list[KbArticle] | None = None
    control_parameters: list[KeyValueObject] | None = None
    desc: str | None = None
    requirements: list[str] | None = None
    status_code: str | None = None
    status_detail: str | None = None
    status_details: list[str] | None = None

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
