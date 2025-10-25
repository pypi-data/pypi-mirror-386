import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.object import Object


class TypeId(IntEnum):
    UNKNOWN = 0
    MILLISECONDS = 1
    SECONDS = 2
    MINUTES = 3
    HOURS = 4
    DAYS = 5
    WEEKS = 6
    MONTHS = 7
    YEARS = 8
    TIME_INTERVAL = 9
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return TypeId[obj]
        else:
            return TypeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "MILLISECONDS": "Milliseconds",
            "SECONDS": "Seconds",
            "MINUTES": "Minutes",
            "HOURS": "Hours",
            "DAYS": "Days",
            "WEEKS": "Weeks",
            "MONTHS": "Months",
            "YEARS": "Years",
            "TIME_INTERVAL": "Time Interval",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Timespan(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "timespan"

    # Recommended
    duration: int | None = None
    duration_days: int | None = None
    duration_hours: int | None = None
    duration_mins: int | None = None
    duration_months: int | None = None
    duration_secs: int | None = None
    duration_weeks: int | None = None
    duration_years: int | None = None
    end_time: Timestamp | None = None
    start_time: Timestamp | None = None
    type_id: TypeId | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def type(self) -> str | None:
        if self.type_id is None:
            return None
        return self.type_id.name

    @type.setter
    def type(self, value: str | None) -> None:
        if value is None:
            self.type_id = None
        else:
            self.type_id = TypeId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_type_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "type" in data and "type_id" not in data:
            type = re.sub(r"\W", "_", data.pop("type").upper())
            data["type_id"] = TypeId[type]
        return data

    @model_validator(mode="after")
    def validate_type_after(self) -> Self:
        if self.__pydantic_extra__ and "type" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("type")
        return self

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(
            getattr(self, field) is None
            for field in [
                "duration",
                "duration_days",
                "duration_hours",
                "duration_mins",
                "duration_months",
                "duration_secs",
                "duration_weeks",
                "duration_years",
                "end_time",
                "start_time",
            ]
        ):
            raise ValueError(
                "At least one of `duration`, `duration_days`, `duration_hours`, `duration_mins`, `duration_months`, `duration_secs`, `duration_weeks`, `duration_years`, `end_time`, `start_time` must be provided"
            )
        return self
