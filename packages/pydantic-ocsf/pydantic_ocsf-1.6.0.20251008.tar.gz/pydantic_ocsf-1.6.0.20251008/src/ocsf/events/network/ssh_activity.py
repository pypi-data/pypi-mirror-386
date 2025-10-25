import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.events.network.network import Network
from ocsf.objects.file import File
from ocsf.objects.hassh import Hassh


class ActivityId(IntEnum):
    UNKNOWN = 0
    OPEN = 1
    CLOSE = 2
    RESET = 3
    FAIL = 4
    REFUSE = 5
    TRAFFIC = 6
    LISTEN = 7
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
            "OPEN": "Open",
            "CLOSE": "Close",
            "RESET": "Reset",
            "FAIL": "Fail",
            "REFUSE": "Refuse",
            "TRAFFIC": "Traffic",
            "LISTEN": "Listen",
            "OTHER": "Other",
        }
        return name_map[super().name]


class AuthTypeId(IntEnum):
    UNKNOWN = 0
    CERTIFICATE_BASED = 1
    GSSAPI = 2
    HOST_BASED = 3
    KEYBOARD_INTERACTIVE = 4
    PASSWORD = 5
    PUBLIC_KEY = 6
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return AuthTypeId[obj]
        else:
            return AuthTypeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "CERTIFICATE_BASED": "Certificate Based",
            "GSSAPI": "GSSAPI",
            "HOST_BASED": "Host Based",
            "KEYBOARD_INTERACTIVE": "Keyboard Interactive",
            "PASSWORD": "Password",
            "PUBLIC_KEY": "Public Key",
            "OTHER": "Other",
        }
        return name_map[super().name]


class SshActivity(Network):
    allowed_profiles: ClassVar[list[str]] = [
        "network_proxy",
        "load_balancer",
        "cloud",
        "datetime",
        "host",
        "osint",
        "security_control",
    ]
    class_name: str = "SSH Activity"
    class_uid: int = 4007
    schema_name: ClassVar[str] = "ssh_activity"

    # Required
    activity_id: ActivityId

    # Recommended
    auth_type_id: AuthTypeId | None = None
    client_hassh: Hassh | None = None
    protocol_ver: str | None = None
    server_hassh: Hassh | None = None

    # Optional
    file: File | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def auth_type(self) -> str | None:
        if self.auth_type_id is None:
            return None
        return self.auth_type_id.name

    @auth_type.setter
    def auth_type(self, value: str | None) -> None:
        if value is None:
            self.auth_type_id = None
        else:
            self.auth_type_id = AuthTypeId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_auth_type_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "auth_type" in data and "auth_type_id" not in data:
            auth_type = re.sub(r"\W", "_", data.pop("auth_type").upper())
            data["auth_type_id"] = AuthTypeId[auth_type]
        return data

    @model_validator(mode="after")
    def validate_auth_type_after(self) -> Self:
        if self.__pydantic_extra__ and "auth_type" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("auth_type")
        return self
