import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects._entity import Entity


class StateId(IntEnum):
    UNKNOWN = 0
    ACTIVE = 1
    SUPPRESSED = 2
    EXPERIMENTAL = 3
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return StateId[obj]
        else:
            return StateId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "ACTIVE": "Active",
            "SUPPRESSED": "Suppressed",
            "EXPERIMENTAL": "Experimental",
            "OTHER": "Other",
        }
        return name_map[super().name]


class TypeId(IntEnum):
    UNKNOWN = 0
    RULE = 1
    BEHAVIORAL = 2
    STATISTICAL = 3
    LEARNING__ML_DL_ = 4
    FINGERPRINTING = 5
    TAGGING = 6
    KEYWORD_MATCH = 7
    REGULAR_EXPRESSIONS = 8
    EXACT_DATA_MATCH = 9
    PARTIAL_DATA_MATCH = 10
    INDEXED_DATA_MATCH = 11
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
            "RULE": "Rule",
            "BEHAVIORAL": "Behavioral",
            "STATISTICAL": "Statistical",
            "LEARNING__ML_DL_": "Learning (ML/DL)",
            "FINGERPRINTING": "Fingerprinting",
            "TAGGING": "Tagging",
            "KEYWORD_MATCH": "Keyword Match",
            "REGULAR_EXPRESSIONS": "Regular Expressions",
            "EXACT_DATA_MATCH": "Exact Data Match",
            "PARTIAL_DATA_MATCH": "Partial Data Match",
            "INDEXED_DATA_MATCH": "Indexed Data Match",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Analytic(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "analytic"

    # Required
    type_id: TypeId

    # Recommended
    name: str | None = None
    uid: str | None = None

    # Optional
    algorithm: str | None = None
    category: str | None = None
    desc: str | None = None
    related_analytics: list["Analytic"] | None = None
    state_id: StateId | None = None
    version: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def state(self) -> str | None:
        if self.state_id is None:
            return None
        return self.state_id.name

    @state.setter
    def state(self, value: str | None) -> None:
        if value is None:
            self.state_id = None
        else:
            self.state_id = StateId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_state_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "state" in data and "state_id" not in data:
            state = re.sub(r"\W", "_", data.pop("state").upper())
            data["state_id"] = StateId[state]
        return data

    @model_validator(mode="after")
    def validate_state_after(self) -> Self:
        if self.__pydantic_extra__ and "state" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("state")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def type(self) -> str:
        return self.type_id.name

    @type.setter
    def type(self, value: str) -> None:
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
