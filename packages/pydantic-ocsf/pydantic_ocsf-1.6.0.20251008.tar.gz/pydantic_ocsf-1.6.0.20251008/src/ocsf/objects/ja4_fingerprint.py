import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects.object import Object


class TypeId(IntEnum):
    UNKNOWN = 0
    JA4 = 1
    JA4SERVER = 2
    JA4HTTP = 3
    JA4LATENCY = 4
    JA4X509 = 5
    JA4SSH = 6
    JA4TCP = 7
    JA4TCPSERVER = 8
    JA4TCPSCAN = 9
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
            "JA4": "JA4",
            "JA4SERVER": "JA4Server",
            "JA4HTTP": "JA4HTTP",
            "JA4LATENCY": "JA4Latency",
            "JA4X509": "JA4X509",
            "JA4SSH": "JA4SSH",
            "JA4TCP": "JA4TCP",
            "JA4TCPSERVER": "JA4TCPServer",
            "JA4TCPSCAN": "JA4TCPScan",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Ja4Fingerprint(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "ja4_fingerprint"

    # Required
    type_id: TypeId
    value: str

    # Optional
    section_a: str | None = None
    section_b: str | None = None
    section_c: str | None = None
    section_d: str | None = None

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
