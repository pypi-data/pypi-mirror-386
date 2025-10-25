import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects.job import Job
from ocsf.objects.kernel_driver import KernelDriver
from ocsf.objects.process import Process
from ocsf.ocsf_object import OcsfObject


class RunModeIds(IntEnum):
    UNKNOWN = 0
    INTERACTIVE = 1
    OWN_PROCESS = 2
    SHARED_PROCESS = 3
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return RunModeIds[obj]
        else:
            return RunModeIds(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "INTERACTIVE": "Interactive",
            "OWN_PROCESS": "Own Process",
            "SHARED_PROCESS": "Shared Process",
            "OTHER": "Other",
        }
        return name_map[super().name]


class RunStateId(IntEnum):
    UNKNOWN = 0
    STOPPED = 1
    START_PENDING = 2
    STOP_PENDING = 3
    RUNNING = 4
    CONTINUE_PENDING = 5
    PAUSE_PENDING = 6
    PAUSED = 7
    RESTART_PENDING = 8
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
            "STOPPED": "Stopped",
            "START_PENDING": "Start Pending",
            "STOP_PENDING": "Stop Pending",
            "RUNNING": "Running",
            "CONTINUE_PENDING": "Continue Pending",
            "PAUSE_PENDING": "Pause Pending",
            "PAUSED": "Paused",
            "RESTART_PENDING": "Restart Pending",
            "OTHER": "Other",
        }
        return name_map[super().name]


class StartTypeId(IntEnum):
    UNKNOWN = 0
    AUTO = 1
    BOOT = 2
    ON_DEMAND = 3
    DISABLED = 4
    ALL_LOGINS = 5
    SPECIFIC_USER_LOGIN = 6
    SCHEDULED = 7
    SYSTEM_CHANGED = 8
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return StartTypeId[obj]
        else:
            return StartTypeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "AUTO": "Auto",
            "BOOT": "Boot",
            "ON_DEMAND": "On Demand",
            "DISABLED": "Disabled",
            "ALL_LOGINS": "All Logins",
            "SPECIFIC_USER_LOGIN": "Specific User Login",
            "SCHEDULED": "Scheduled",
            "SYSTEM_CHANGED": "System Changed",
            "OTHER": "Other",
        }
        return name_map[super().name]


class TypeId(IntEnum):
    UNKNOWN = 0
    KERNEL_MODE_DRIVER = 1
    USER_MODE_DRIVER = 2
    SERVICE = 3
    USER_MODE_APPLICATION = 4
    AUTOLOAD = 5
    SYSTEM_EXTENSION = 6
    KERNEL_EXTENSION = 7
    SCHEDULED_JOB__TASK = 8
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
            "KERNEL_MODE_DRIVER": "Kernel Mode Driver",
            "USER_MODE_DRIVER": "User Mode Driver",
            "SERVICE": "Service",
            "USER_MODE_APPLICATION": "User Mode Application",
            "AUTOLOAD": "Autoload",
            "SYSTEM_EXTENSION": "System Extension",
            "KERNEL_EXTENSION": "Kernel Extension",
            "SCHEDULED_JOB__TASK": "Scheduled Job, Task",
            "OTHER": "Other",
        }
        return name_map[super().name]


class StartupItem(OcsfObject):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "startup_item"

    # Required
    name: str
    start_type_id: StartTypeId

    # Recommended
    run_state_id: RunStateId | None = None
    type_id: TypeId | None = None

    # Optional
    driver: KernelDriver | None = None
    job: Job | None = None
    process: Process | None = None
    run_mode_ids: list[RunModeIds] | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def run_modes(self) -> list[str] | None:
        if self.run_mode_ids is None:
            return None
        return [value.name for value in self.run_mode_ids]

    @run_modes.setter
    def run_modes(self, value: list[str] | None) -> None:
        if value is None:
            self.run_mode_ids = None
        else:
            self.run_mode_ids = [RunModeIds[x] for x in value]

    @model_validator(mode="before")
    @classmethod
    def validate_run_modes_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "run_modes" in data and "run_mode_ids" not in data:
            run_modes = re.sub(r"\W", "_", data.pop("run_modes").upper())
            data["run_mode_ids"] = RunModeIds[run_modes]
        return data

    @model_validator(mode="after")
    def validate_run_modes_after(self) -> Self:
        if self.__pydantic_extra__ and "run_modes" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("run_modes")
        return self

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

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def start_type(self) -> str:
        return self.start_type_id.name

    @start_type.setter
    def start_type(self, value: str) -> None:
        self.start_type_id = StartTypeId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_start_type_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "start_type" in data and "start_type_id" not in data:
            start_type = re.sub(r"\W", "_", data.pop("start_type").upper())
            data["start_type_id"] = StartTypeId[start_type]
        return data

    @model_validator(mode="after")
    def validate_start_type_after(self) -> Self:
        if self.__pydantic_extra__ and "start_type" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("start_type")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def type(self) -> str | None:
        if self.type_id is None:
            return None
        return self.type_id.name

    @type.setter
    def type(self, value: str | None) -> None:
        if value is None:
            self.type_id = None
        else:
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

    @model_validator(mode="after")
    def validate_just_one(self):
        count = len([f for f in ["driver", "job", "process"] if getattr(self, f) is not None])
        if count != 1:
            raise ValueError("Just one of `driver`, `job`, `process` must be provided, got {count}")
        return self
