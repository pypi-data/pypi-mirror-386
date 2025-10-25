import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.events.iam.iam import IAM
from ocsf.objects.auth_factor import AuthFactor
from ocsf.objects.authentication_token import AuthenticationToken
from ocsf.objects.certificate import Certificate
from ocsf.objects.network_endpoint import NetworkEndpoint
from ocsf.objects.process import Process
from ocsf.objects.service import Service
from ocsf.objects.session import Session
from ocsf.objects.user import User


class AccountSwitchTypeId(IntEnum):
    UNKNOWN = 0
    SUBSTITUTE_USER = 1
    IMPERSONATE = 2
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return AccountSwitchTypeId[obj]
        else:
            return AccountSwitchTypeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "SUBSTITUTE_USER": "Substitute User",
            "IMPERSONATE": "Impersonate",
            "OTHER": "Other",
        }
        return name_map[super().name]


class ActivityId(IntEnum):
    UNKNOWN = 0
    LOGON = 1
    LOGOFF = 2
    AUTHENTICATION_TICKET = 3
    SERVICE_TICKET_REQUEST = 4
    SERVICE_TICKET_RENEW = 5
    PREAUTH = 6
    ACCOUNT_SWITCH = 7
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return ActivityId[obj]
        else:
            return ActivityId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "LOGON": "Logon",
            "LOGOFF": "Logoff",
            "AUTHENTICATION_TICKET": "Authentication Ticket",
            "SERVICE_TICKET_REQUEST": "Service Ticket Request",
            "SERVICE_TICKET_RENEW": "Service Ticket Renew",
            "PREAUTH": "Preauth",
            "ACCOUNT_SWITCH": "Account Switch",
            "OTHER": "Other",
        }
        return name_map[super().name]


class AuthProtocolId(IntEnum):
    UNKNOWN = 0
    NTLM = 1
    KERBEROS = 2
    DIGEST = 3
    OPENID = 4
    SAML = 5
    OAUTH_2_0 = 6
    PAP = 7
    CHAP = 8
    EAP = 9
    RADIUS = 10
    BASIC_AUTHENTICATION = 11
    LDAP = 12
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return AuthProtocolId[obj]
        else:
            return AuthProtocolId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "NTLM": "NTLM",
            "KERBEROS": "Kerberos",
            "DIGEST": "Digest",
            "OPENID": "OpenID",
            "SAML": "SAML",
            "OAUTH_2_0": "OAUTH 2.0",
            "PAP": "PAP",
            "CHAP": "CHAP",
            "EAP": "EAP",
            "RADIUS": "RADIUS",
            "BASIC_AUTHENTICATION": "Basic Authentication",
            "LDAP": "LDAP",
            "OTHER": "Other",
        }
        return name_map[super().name]


class LogonTypeId(IntEnum):
    UNKNOWN = 0
    SYSTEM = 1
    INTERACTIVE = 2
    NETWORK = 3
    BATCH = 4
    OS_SERVICE = 5
    UNLOCK = 7
    NETWORK_CLEARTEXT = 8
    NEW_CREDENTIALS = 9
    REMOTE_INTERACTIVE = 10
    CACHED_INTERACTIVE = 11
    CACHED_REMOTE_INTERACTIVE = 12
    CACHED_UNLOCK = 13
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return LogonTypeId[obj]
        else:
            return LogonTypeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "SYSTEM": "System",
            "INTERACTIVE": "Interactive",
            "NETWORK": "Network",
            "BATCH": "Batch",
            "OS_SERVICE": "OS Service",
            "UNLOCK": "Unlock",
            "NETWORK_CLEARTEXT": "Network Cleartext",
            "NEW_CREDENTIALS": "New Credentials",
            "REMOTE_INTERACTIVE": "Remote Interactive",
            "CACHED_INTERACTIVE": "Cached Interactive",
            "CACHED_REMOTE_INTERACTIVE": "Cached Remote Interactive",
            "CACHED_UNLOCK": "Cached Unlock",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Authentication(IAM):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Authentication"
    class_uid: int = 3002
    schema_name: ClassVar[str] = "authentication"

    # Required
    activity_id: ActivityId
    user: User

    # Recommended
    account_switch_type_id: AccountSwitchTypeId | None = None
    auth_protocol_id: AuthProtocolId | None = None
    certificate: Certificate | None = None
    dst_endpoint: NetworkEndpoint | None = None
    is_mfa: bool | None = None
    is_remote: bool | None = None
    logon_type_id: LogonTypeId | None = None
    service: Service | None = None
    session: Session | None = None
    status_detail: str | None = None

    # Optional
    auth_factors: list[AuthFactor] | None = None
    authentication_token: AuthenticationToken | None = None
    is_cleartext: bool | None = None
    is_new_logon: bool | None = None
    logon_process: Process | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def account_switch_type(self) -> str | None:
        if self.account_switch_type_id is None:
            return None
        return self.account_switch_type_id.name

    @account_switch_type.setter
    def account_switch_type(self, value: str | None) -> None:
        if value is None:
            self.account_switch_type_id = None
        else:
            self.account_switch_type_id = AccountSwitchTypeId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_account_switch_type_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "account_switch_type" in data and "account_switch_type_id" not in data:
            account_switch_type = re.sub(r"\W", "_", data.pop("account_switch_type").upper())
            data["account_switch_type_id"] = AccountSwitchTypeId[account_switch_type]
        return data

    @model_validator(mode="after")
    def validate_account_switch_type_after(self) -> Self:
        if self.__pydantic_extra__ and "account_switch_type" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("account_switch_type")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def auth_protocol(self) -> str | None:
        if self.auth_protocol_id is None:
            return None
        return self.auth_protocol_id.name

    @auth_protocol.setter
    def auth_protocol(self, value: str | None) -> None:
        if value is None:
            self.auth_protocol_id = None
        else:
            self.auth_protocol_id = AuthProtocolId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_auth_protocol_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "auth_protocol" in data and "auth_protocol_id" not in data:
            auth_protocol = re.sub(r"\W", "_", data.pop("auth_protocol").upper())
            data["auth_protocol_id"] = AuthProtocolId[auth_protocol]
        return data

    @model_validator(mode="after")
    def validate_auth_protocol_after(self) -> Self:
        if self.__pydantic_extra__ and "auth_protocol" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("auth_protocol")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def logon_type(self) -> str | None:
        if self.logon_type_id is None:
            return None
        return self.logon_type_id.name

    @logon_type.setter
    def logon_type(self, value: str | None) -> None:
        if value is None:
            self.logon_type_id = None
        else:
            self.logon_type_id = LogonTypeId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_logon_type_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "logon_type" in data and "logon_type_id" not in data:
            logon_type = re.sub(r"\W", "_", data.pop("logon_type").upper())
            data["logon_type_id"] = LogonTypeId[logon_type]
        return data

    @model_validator(mode="after")
    def validate_logon_type_after(self) -> Self:
        if self.__pydantic_extra__ and "logon_type" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("logon_type")
        return self

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(getattr(self, field) is None for field in ["service", "dst_endpoint"]):
            raise ValueError("At least one of `service`, `dst_endpoint` must be provided")
        return self
