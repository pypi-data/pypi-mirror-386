import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects._dns import Dns


class FlagIds(IntEnum):
    UNKNOWN = 0
    AUTHORITATIVE_ANSWER = 1
    TRUNCATED_RESPONSE = 2
    RECURSION_DESIRED = 3
    RECURSION_AVAILABLE = 4
    AUTHENTIC_DATA = 5
    CHECKING_DISABLED = 6
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return FlagIds[obj]
        else:
            return FlagIds(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "AUTHORITATIVE_ANSWER": "Authoritative Answer",
            "TRUNCATED_RESPONSE": "Truncated Response",
            "RECURSION_DESIRED": "Recursion Desired",
            "RECURSION_AVAILABLE": "Recursion Available",
            "AUTHENTIC_DATA": "Authentic Data",
            "CHECKING_DISABLED": "Checking Disabled",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DnsAnswer(Dns):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "dns_answer"

    # Required
    rdata: str

    # Recommended
    class_: str | None = None
    flag_ids: list[FlagIds] | None = None
    ttl: int | None = None
    type_: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def flags(self) -> list[str] | None:
        if self.flag_ids is None:
            return None
        return [value.name for value in self.flag_ids]

    @flags.setter
    def flags(self, value: list[str] | None) -> None:
        if value is None:
            self.flag_ids = None
        else:
            self.flag_ids = [FlagIds[x] for x in value]

    @model_validator(mode="before")
    @classmethod
    def validate_flags_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "flags" in data and "flag_ids" not in data:
            flags = re.sub(r"\W", "_", data.pop("flags").upper())
            data["flag_ids"] = FlagIds[flags]
        return data

    @model_validator(mode="after")
    def validate_flags_after(self) -> Self:
        if self.__pydantic_extra__ and "flags" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("flags")
        return self
