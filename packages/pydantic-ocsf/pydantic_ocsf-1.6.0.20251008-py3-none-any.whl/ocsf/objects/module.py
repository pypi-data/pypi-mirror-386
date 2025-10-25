import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects.file import File
from ocsf.objects.object import Object


class LoadTypeId(IntEnum):
    UNKNOWN = 0
    STANDARD = 1
    NON_STANDARD = 2
    SHELLCODE = 3
    MAPPED = 4
    NONSTANDARD_BACKED = 5
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return LoadTypeId[obj]
        else:
            return LoadTypeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "STANDARD": "Standard",
            "NON_STANDARD": "Non Standard",
            "SHELLCODE": "ShellCode",
            "MAPPED": "Mapped",
            "NONSTANDARD_BACKED": "NonStandard Backed",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Module(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "module"

    # Required
    load_type_id: LoadTypeId

    # Recommended
    base_address: str | None = None
    file: File | None = None
    start_address: str | None = None
    type_: str | None = None

    # Optional
    function_name: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def load_type(self) -> str:
        return self.load_type_id.name

    @load_type.setter
    def load_type(self, value: str) -> None:
        self.load_type_id = LoadTypeId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_load_type_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "load_type" in data and "load_type_id" not in data:
            load_type = re.sub(r"\W", "_", data.pop("load_type").upper())
            data["load_type_id"] = LoadTypeId[load_type]
        return data

    @model_validator(mode="after")
    def validate_load_type_after(self) -> Self:
        if self.__pydantic_extra__ and "load_type" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("load_type")
        return self
