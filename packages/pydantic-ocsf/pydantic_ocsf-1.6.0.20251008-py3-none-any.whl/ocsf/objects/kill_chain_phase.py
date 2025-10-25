import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects.object import Object


class PhaseId(IntEnum):
    UNKNOWN = 0
    RECONNAISSANCE = 1
    WEAPONIZATION = 2
    DELIVERY = 3
    EXPLOITATION = 4
    INSTALLATION = 5
    COMMAND___CONTROL = 6
    ACTIONS_ON_OBJECTIVES = 7
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return PhaseId[obj]
        else:
            return PhaseId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "RECONNAISSANCE": "Reconnaissance",
            "WEAPONIZATION": "Weaponization",
            "DELIVERY": "Delivery",
            "EXPLOITATION": "Exploitation",
            "INSTALLATION": "Installation",
            "COMMAND___CONTROL": "Command & Control",
            "ACTIONS_ON_OBJECTIVES": "Actions on Objectives",
            "OTHER": "Other",
        }
        return name_map[super().name]


class KillChainPhase(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "kill_chain_phase"

    # Required
    phase_id: PhaseId

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def phase(self) -> str:
        return self.phase_id.name

    @phase.setter
    def phase(self, value: str) -> None:
        self.phase_id = PhaseId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_phase_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "phase" in data and "phase_id" not in data:
            phase = re.sub(r"\W", "_", data.pop("phase").upper())
            data["phase_id"] = PhaseId[phase]
        return data

    @model_validator(mode="after")
    def validate_phase_after(self) -> Self:
        if self.__pydantic_extra__ and "phase" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("phase")
        return self
