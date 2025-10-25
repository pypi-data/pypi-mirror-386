import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects.object import Object
from ocsf.objects.policy import Policy


class StatusId(IntEnum):
    UNKNOWN = 0
    APPLICABLE = 1
    INAPPLICABLE = 2
    EVALUATION_ERROR = 3
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
            "APPLICABLE": "Applicable",
            "INAPPLICABLE": "Inapplicable",
            "EVALUATION_ERROR": "Evaluation Error",
            "OTHER": "Other",
        }
        return name_map[super().name]


class AdditionalRestriction(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "additional_restriction"

    # Required
    policy: Policy

    # Recommended
    status_id: StatusId | None = None

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
