import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.file import File
from ocsf.objects.object import Object
from ocsf.objects.user import User


class RunStateId(IntEnum):
    UNKNOWN = 0
    READY = 1
    QUEUED = 2
    RUNNING = 3
    STOPPED = 4
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return RunStateId[obj]
        else:
            return RunStateId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "READY": "Ready",
            "QUEUED": "Queued",
            "RUNNING": "Running",
            "STOPPED": "Stopped",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Job(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "job"

    # Required
    file: File
    name: str

    # Recommended
    cmd_line: str | None = None
    created_time: Timestamp | None = None
    desc: str | None = None
    last_run_time: Timestamp | None = None
    run_state_id: RunStateId | None = None

    # Optional
    next_run_time: Timestamp | None = None
    user: User | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def run_state(self) -> str | None:
        if self.run_state_id is None:
            return None
        return self.run_state_id.name

    @run_state.setter
    def run_state(self, value: str | None) -> None:
        if value is None:
            self.run_state_id = None
        else:
            self.run_state_id = RunStateId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_run_state_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "run_state" in data and "run_state_id" not in data:
            run_state = re.sub(r"\W", "_", data.pop("run_state").upper())
            data["run_state_id"] = RunStateId[run_state]
        return data

    @model_validator(mode="after")
    def validate_run_state_after(self) -> Self:
        if self.__pydantic_extra__ and "run_state" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("run_state")
        return self
