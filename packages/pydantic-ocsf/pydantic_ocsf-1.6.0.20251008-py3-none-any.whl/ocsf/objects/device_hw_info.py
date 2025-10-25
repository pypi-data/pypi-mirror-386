import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self
from uuid import UUID

from pydantic import computed_field, model_validator

from ocsf.objects.display import Display
from ocsf.objects.keyboard_info import KeyboardInfo
from ocsf.objects.object import Object


class CpuArchitectureId(IntEnum):
    UNKNOWN = 0
    X86 = 1
    ARM = 2
    RISC_V = 3
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return CpuArchitectureId[obj]
        else:
            return CpuArchitectureId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "X86": "x86",
            "ARM": "ARM",
            "RISC_V": "RISC-V",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DeviceHwInfo(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "device_hw_info"

    # Optional
    bios_date: str | None = None
    bios_manufacturer: str | None = None
    bios_ver: str | None = None
    chassis: str | None = None
    cpu_architecture_id: CpuArchitectureId | None = None
    cpu_bits: int | None = None
    cpu_cores: int | None = None
    cpu_count: int | None = None
    cpu_speed: int | None = None
    cpu_type: str | None = None
    desktop_display: Display | None = None
    keyboard_info: KeyboardInfo | None = None
    ram_size: int | None = None
    serial_number: str | None = None
    uuid: UUID | None = None
    vendor_name: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def cpu_architecture(self) -> str | None:
        if self.cpu_architecture_id is None:
            return None
        return self.cpu_architecture_id.name

    @cpu_architecture.setter
    def cpu_architecture(self, value: str | None) -> None:
        if value is None:
            self.cpu_architecture_id = None
        else:
            self.cpu_architecture_id = CpuArchitectureId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_cpu_architecture_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "cpu_architecture" in data and "cpu_architecture_id" not in data:
            cpu_architecture = re.sub(r"\W", "_", data.pop("cpu_architecture").upper())
            data["cpu_architecture_id"] = CpuArchitectureId[cpu_architecture]
        return data

    @model_validator(mode="after")
    def validate_cpu_architecture_after(self) -> Self:
        if self.__pydantic_extra__ and "cpu_architecture" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("cpu_architecture")
        return self
