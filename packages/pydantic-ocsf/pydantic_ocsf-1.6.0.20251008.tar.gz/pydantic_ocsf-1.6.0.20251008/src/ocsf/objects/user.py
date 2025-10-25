import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self, TYPE_CHECKING

from pydantic import EmailStr, computed_field, model_validator

from ocsf.objects._entity import Entity
from ocsf.objects.account import Account
from ocsf.objects.group import Group
from ocsf.objects.organization import Organization
from ocsf.objects.programmatic_credential import ProgrammaticCredential

if TYPE_CHECKING:
    from ocsf.objects.ldap_person import LdapPerson


class RiskLevelId(IntEnum):
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return RiskLevelId[obj]
        else:
            return RiskLevelId(obj)

    @enum_property
    def name(self):
        name_map = {
            "INFO": "Info",
            "LOW": "Low",
            "MEDIUM": "Medium",
            "HIGH": "High",
            "CRITICAL": "Critical",
            "OTHER": "Other",
        }
        return name_map[super().name]


class TypeId(IntEnum):
    UNKNOWN = 0
    USER = 1
    ADMIN = 2
    SYSTEM = 3
    SERVICE = 4
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
            "USER": "User",
            "ADMIN": "Admin",
            "SYSTEM": "System",
            "SERVICE": "Service",
            "OTHER": "Other",
        }
        return name_map[super().name]


class User(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "user"

    # Recommended
    has_mfa: bool | None = None
    name: str | None = None
    type_id: TypeId | None = None
    uid: str | None = None

    # Optional
    account: Account | None = None
    credential_uid: str | None = None
    display_name: str | None = None
    domain: str | None = None
    email_addr: EmailStr | None = None
    forward_addr: EmailStr | None = None
    full_name: str | None = None
    groups: list[Group] | None = None
    ldap_person: "LdapPerson | None" = None
    org: Organization | None = None
    phone_number: str | None = None
    programmatic_credentials: list[ProgrammaticCredential] | None = None
    risk_level_id: RiskLevelId | None = None
    risk_score: int | None = None
    uid_alt: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def risk_level(self) -> str | None:
        if self.risk_level_id is None:
            return None
        return self.risk_level_id.name

    @risk_level.setter
    def risk_level(self, value: str | None) -> None:
        if value is None:
            self.risk_level_id = None
        else:
            self.risk_level_id = RiskLevelId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_risk_level_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "risk_level" in data and "risk_level_id" not in data:
            risk_level = re.sub(r"\W", "_", data.pop("risk_level").upper())
            data["risk_level_id"] = RiskLevelId[risk_level]
        return data

    @model_validator(mode="after")
    def validate_risk_level_after(self) -> Self:
        if self.__pydantic_extra__ and "risk_level" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("risk_level")
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
    def validate_at_least_one(self):
        if all(getattr(self, field) is None for field in ["account", "name", "uid"]):
            raise ValueError("At least one of `account`, `name`, `uid` must be provided")
        return self
