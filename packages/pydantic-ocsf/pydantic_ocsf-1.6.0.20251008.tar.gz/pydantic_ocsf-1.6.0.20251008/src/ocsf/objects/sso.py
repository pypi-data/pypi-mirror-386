import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import AnyUrl, computed_field, model_validator

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.certificate import Certificate
from ocsf.objects.object import Object


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


class Sso(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "sso"

    # Recommended
    certificate: Certificate | None = None
    name: str | None = None
    uid: str | None = None

    # Optional
    auth_protocol_id: AuthProtocolId | None = None
    created_time: Timestamp | None = None
    duration_mins: int | None = None
    idle_timeout: int | None = None
    login_endpoint: AnyUrl | None = None
    logout_endpoint: AnyUrl | None = None
    metadata_endpoint: AnyUrl | None = None
    modified_time: Timestamp | None = None
    protocol_name: str | None = None
    scopes: list[str] | None = None
    vendor_name: str | None = None

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
