import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects.graph import Graph
from ocsf.objects.group import Group
from ocsf.objects.key_value_object import KeyValueObject
from ocsf.objects.object import Object
from ocsf.objects.sbom import Sbom
from ocsf.objects.url import Url
from ocsf.objects.user import User


class RiskLevelId(IntEnum):
    INFO = 0
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
            return RiskLevelId[obj]
        else:
            return RiskLevelId(obj)

    @enum_property
    def name(self):
        name_map = {
            "INFO": "Info",
            "LOW": "Low",
            "MEDIUM": "Medium",
            "HIGH": "High",
            "CRITICAL": "Critical",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Application(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "application"

    # Recommended
    name: str | None = None
    owner: User | None = None
    uid: str | None = None

    # Optional
    criticality: str | None = None
    data: dict[str, Any] | None = None
    desc: str | None = None
    group: Group | None = None
    hostname: str | None = None
    labels: list[str] | None = None
    region: str | None = None
    resource_relationship: Graph | None = None
    risk_level_id: RiskLevelId | None = None
    risk_score: int | None = None
    sbom: Sbom | None = None
    tags: list[KeyValueObject] | None = None
    type_: str | None = None
    uid_alt: str | None = None
    url: Url | None = None
    version: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def risk_level(self) -> str | None:
        if self.risk_level_id is None:
            return None
        return self.risk_level_id.name

    @risk_level.setter
    def risk_level(self, value: str | None) -> None:
        if value is None:
            self.risk_level_id = None
        else:
            self.risk_level_id = RiskLevelId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_risk_level_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "risk_level" in data and "risk_level_id" not in data:
            risk_level = re.sub(r"\W", "_", data.pop("risk_level").upper())
            data["risk_level_id"] = RiskLevelId[risk_level]
        return data

    @model_validator(mode="after")
    def validate_risk_level_after(self) -> Self:
        if self.__pydantic_extra__ and "risk_level" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("risk_level")
        return self

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(getattr(self, field) is None for field in ["uid", "name"]):
            raise ValueError("At least one of `uid`, `name` must be provided")
        return self
