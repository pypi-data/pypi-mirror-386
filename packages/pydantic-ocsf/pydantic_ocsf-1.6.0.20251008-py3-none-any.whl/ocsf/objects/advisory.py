import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import AnyUrl, computed_field, model_validator

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.cve import Cve
from ocsf.objects.cwe import Cwe
from ocsf.objects.object import Object
from ocsf.objects.os import Os
from ocsf.objects.product import Product
from ocsf.objects.timespan import Timespan


class InstallStateId(IntEnum):
    UNKNOWN = 0
    INSTALLED = 1
    NOT_INSTALLED = 2
    INSTALLED_PENDING_REBOOT = 3
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return InstallStateId[obj]
        else:
            return InstallStateId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "INSTALLED": "Installed",
            "NOT_INSTALLED": "Not Installed",
            "INSTALLED_PENDING_REBOOT": "Installed Pending Reboot",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Advisory(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "advisory"

    # Required
    uid: str

    # Recommended
    created_time: Timestamp | None = None
    install_state_id: InstallStateId | None = None
    os: Os | None = None
    references: list[str] | None = None
    title: str | None = None

    # Optional
    avg_timespan: Timespan | None = None
    bulletin: str | None = None
    classification: str | None = None
    desc: str | None = None
    is_superseded: bool | None = None
    modified_time: Timestamp | None = None
    product: Product | None = None
    related_cves: list[Cve] | None = None
    related_cwes: list[Cwe] | None = None
    size: int | None = None
    src_url: AnyUrl | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def install_state(self) -> str | None:
        if self.install_state_id is None:
            return None
        return self.install_state_id.name

    @install_state.setter
    def install_state(self, value: str | None) -> None:
        if value is None:
            self.install_state_id = None
        else:
            self.install_state_id = InstallStateId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_install_state_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "install_state" in data and "install_state_id" not in data:
            install_state = re.sub(r"\W", "_", data.pop("install_state").upper())
            data["install_state_id"] = InstallStateId[install_state]
        return data

    @model_validator(mode="after")
    def validate_install_state_after(self) -> Self:
        if self.__pydantic_extra__ and "install_state" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("install_state")
        return self
