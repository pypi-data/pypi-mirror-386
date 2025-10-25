import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects.file import File
from ocsf.objects.fingerprint import Fingerprint
from ocsf.objects.long_string import LongString
from ocsf.objects.object import Object


class TypeId(IntEnum):
    UNKNOWN = 0
    WINDOWS_COMMAND_PROMPT = 1
    POWERSHELL = 2
    PYTHON = 3
    JAVASCRIPT = 4
    VBSCRIPT = 5
    UNIX_SHELL = 6
    VBA = 7
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
            "WINDOWS_COMMAND_PROMPT": "Windows Command Prompt",
            "POWERSHELL": "PowerShell",
            "PYTHON": "Python",
            "JAVASCRIPT": "JavaScript",
            "VBSCRIPT": "VBScript",
            "UNIX_SHELL": "Unix Shell",
            "VBA": "VBA",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Script(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "script"

    # Required
    script_content: LongString
    type_id: TypeId

    # Recommended
    hashes: list[Fingerprint] | None = None

    # Optional
    file: File | None = None
    name: str | None = None
    parent_uid: str | None = None
    uid: str | None = None

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
