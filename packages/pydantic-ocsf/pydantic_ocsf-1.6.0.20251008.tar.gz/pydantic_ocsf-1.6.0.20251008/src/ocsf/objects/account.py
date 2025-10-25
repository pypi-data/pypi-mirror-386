import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects._entity import Entity
from ocsf.objects.key_value_object import KeyValueObject


class TypeId(IntEnum):
    UNKNOWN = 0
    LDAP_ACCOUNT = 1
    WINDOWS_ACCOUNT = 2
    AWS_IAM_USER = 3
    AWS_IAM_ROLE = 4
    GCP_ACCOUNT = 5
    AZURE_AD_ACCOUNT = 6
    MAC_OS_ACCOUNT = 7
    APPLE_ACCOUNT = 8
    LINUX_ACCOUNT = 9
    AWS_ACCOUNT = 10
    GCP_PROJECT = 11
    OCI_COMPARTMENT = 12
    AZURE_SUBSCRIPTION = 13
    SALESFORCE_ACCOUNT = 14
    GOOGLE_WORKSPACE = 15
    SERVICENOW_INSTANCE = 16
    M365_TENANT = 17
    EMAIL_ACCOUNT = 18
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
            "LDAP_ACCOUNT": "LDAP Account",
            "WINDOWS_ACCOUNT": "Windows Account",
            "AWS_IAM_USER": "AWS IAM User",
            "AWS_IAM_ROLE": "AWS IAM Role",
            "GCP_ACCOUNT": "GCP Account",
            "AZURE_AD_ACCOUNT": "Azure AD Account",
            "MAC_OS_ACCOUNT": "Mac OS Account",
            "APPLE_ACCOUNT": "Apple Account",
            "LINUX_ACCOUNT": "Linux Account",
            "AWS_ACCOUNT": "AWS Account",
            "GCP_PROJECT": "GCP Project",
            "OCI_COMPARTMENT": "OCI Compartment",
            "AZURE_SUBSCRIPTION": "Azure Subscription",
            "SALESFORCE_ACCOUNT": "Salesforce Account",
            "GOOGLE_WORKSPACE": "Google Workspace",
            "SERVICENOW_INSTANCE": "Servicenow Instance",
            "M365_TENANT": "M365 Tenant",
            "EMAIL_ACCOUNT": "Email Account",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Account(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "account"

    # Recommended
    name: str | None = None
    type_id: TypeId | None = None
    uid: str | None = None

    # Optional
    labels: list[str] | None = None
    tags: list[KeyValueObject] | None = None

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
