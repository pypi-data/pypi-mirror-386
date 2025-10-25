import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import IPvAnyAddress, computed_field, model_validator

from ocsf.objects._resource import Resource
from ocsf.objects.agent import Agent
from ocsf.objects.graph import Graph
from ocsf.objects.group import Group
from ocsf.objects.user import User


class RoleId(IntEnum):
    UNKNOWN = 0
    TARGET = 1
    ACTOR = 2
    AFFECTED = 3
    RELATED = 4
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return RoleId[obj]
        else:
            return RoleId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "TARGET": "Target",
            "ACTOR": "Actor",
            "AFFECTED": "Affected",
            "RELATED": "Related",
            "OTHER": "Other",
        }
        return name_map[super().name]


class ResourceDetails(Resource):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "data_classification"]
    schema_name: ClassVar[str] = "resource_details"

    # Recommended
    hostname: str | None = None
    ip: IPvAnyAddress | None = None
    name: str | None = None
    owner: User | None = None
    role_id: RoleId | None = None

    # Optional
    agent_list: list[Agent] | None = None
    cloud_partition: str | None = None
    criticality: str | None = None
    group: Group | None = None
    is_backed_up: bool | None = None
    namespace: str | None = None
    region: str | None = None
    resource_relationship: Graph | None = None
    version: str | None = None
    zone: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def role(self) -> str | None:
        if self.role_id is None:
            return None
        return self.role_id.name

    @role.setter
    def role(self, value: str | None) -> None:
        if value is None:
            self.role_id = None
        else:
            self.role_id = RoleId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_role_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "role" in data and "role_id" not in data:
            role = re.sub(r"\W", "_", data.pop("role").upper())
            data["role_id"] = RoleId[role]
        return data

    @model_validator(mode="after")
    def validate_role_after(self) -> Self:
        if self.__pydantic_extra__ and "role" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("role")
        return self
