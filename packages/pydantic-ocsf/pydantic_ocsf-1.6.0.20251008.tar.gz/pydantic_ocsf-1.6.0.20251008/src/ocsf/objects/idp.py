import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import AnyUrl, computed_field, model_validator

from ocsf.objects._entity import Entity
from ocsf.objects.auth_factor import AuthFactor
from ocsf.objects.fingerprint import Fingerprint
from ocsf.objects.scim import Scim
from ocsf.objects.sso import Sso


class StateId(IntEnum):
    UNKNOWN = 0
    ACTIVE = 1
    SUSPENDED = 2
    DEPRECATED = 3
    DELETED = 4
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
            "SUSPENDED": "Suspended",
            "DEPRECATED": "Deprecated",
            "DELETED": "Deleted",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Idp(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "idp"

    # Recommended
    name: str | None = None
    uid: str | None = None

    # Optional
    auth_factors: list[AuthFactor] | None = None
    domain: str | None = None
    fingerprint: Fingerprint | None = None
    has_mfa: bool | None = None
    issuer: str | None = None
    protocol_name: str | None = None
    scim: Scim | None = None
    sso: Sso | None = None
    state_id: StateId | None = None
    tenant_uid: str | None = None
    url_string: AnyUrl | None = None

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
