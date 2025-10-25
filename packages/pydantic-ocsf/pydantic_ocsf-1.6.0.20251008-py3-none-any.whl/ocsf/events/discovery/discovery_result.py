import re
from enum import IntEnum, property as enum_property
from typing import Annotated, Any, ClassVar, Literal, Self

from pydantic import Field, computed_field, model_validator

from ocsf.events.base_event import BaseEvent
from ocsf.objects.query_info import QueryInfo


class ActivityId(IntEnum):
    UNKNOWN = 0
    QUERY = 1
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
            "QUERY": "Query",
            "OTHER": "Other",
        }
        return name_map[super().name]


class QueryResultId(IntEnum):
    UNKNOWN = 0
    EXISTS = 1
    PARTIAL = 2
    DOES_NOT_EXIST = 3
    ERROR = 4
    UNSUPPORTED = 5
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return QueryResultId[obj]
        else:
            return QueryResultId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "EXISTS": "Exists",
            "PARTIAL": "Partial",
            "DOES_NOT_EXIST": "Does not exist",
            "ERROR": "Error",
            "UNSUPPORTED": "Unsupported",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DiscoveryResult(BaseEvent):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    category_name: Annotated[Literal["Discovery"], Field(frozen=True)] = "Discovery"
    category_uid: Annotated[Literal[5], Field(frozen=True)] = 5
    schema_name: ClassVar[str] = "discovery_result"

    # Required
    activity_id: ActivityId
    query_result_id: QueryResultId

    # Recommended
    query_info: QueryInfo | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def query_result(self) -> str:
        return self.query_result_id.name

    @query_result.setter
    def query_result(self, value: str) -> None:
        self.query_result_id = QueryResultId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_query_result_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "query_result" in data and "query_result_id" not in data:
            query_result = re.sub(r"\W", "_", data.pop("query_result").upper())
            data["query_result_id"] = QueryResultId[query_result]
        return data

    @model_validator(mode="after")
    def validate_query_result_after(self) -> Self:
        if self.__pydantic_extra__ and "query_result" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("query_result")
        return self
