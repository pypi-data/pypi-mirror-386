import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.events.application.application import Application
from ocsf.objects.actor import Actor
from ocsf.objects.database import Database
from ocsf.objects.databucket import Databucket
from ocsf.objects.http_request import HttpRequest
from ocsf.objects.http_response import HttpResponse
from ocsf.objects.network_endpoint import NetworkEndpoint
from ocsf.objects.query_info import QueryInfo
from ocsf.objects.table import Table


class ActivityId(IntEnum):
    UNKNOWN = 0
    READ = 1
    UPDATE = 2
    CONNECT = 3
    QUERY = 4
    WRITE = 5
    CREATE = 6
    DELETE = 7
    LIST = 8
    ENCRYPT = 9
    DECRYPT = 10
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
            "READ": "Read",
            "UPDATE": "Update",
            "CONNECT": "Connect",
            "QUERY": "Query",
            "WRITE": "Write",
            "CREATE": "Create",
            "DELETE": "Delete",
            "LIST": "List",
            "ENCRYPT": "Encrypt",
            "DECRYPT": "Decrypt",
            "OTHER": "Other",
        }
        return name_map[super().name]


class TypeId(IntEnum):
    UNKNOWN = 0
    DATABASE = 1
    DATABUCKET = 2
    TABLE = 3
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
            "DATABASE": "Database",
            "DATABUCKET": "Databucket",
            "TABLE": "Table",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DatastoreActivity(Application):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Datastore Activity"
    class_uid: int = 6005
    schema_name: ClassVar[str] = "datastore_activity"

    # Required
    activity_id: ActivityId
    actor: Actor
    src_endpoint: NetworkEndpoint

    # Recommended
    database: Database | None = None
    databucket: Databucket | None = None
    dst_endpoint: NetworkEndpoint | None = None
    http_request: HttpRequest | None = None
    http_response: HttpResponse | None = None
    query_info: QueryInfo | None = None
    table: Table | None = None
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
        if all(getattr(self, field) is None for field in ["database", "databucket", "table"]):
            raise ValueError("At least one of `database`, `databucket`, `table` must be provided")
        return self
