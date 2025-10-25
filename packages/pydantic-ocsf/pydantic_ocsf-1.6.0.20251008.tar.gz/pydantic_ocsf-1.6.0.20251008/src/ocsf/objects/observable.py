import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects.object import Object
from ocsf.objects.reputation import Reputation


class TypeId(IntEnum):
    UNKNOWN = 0
    HOSTNAME = 1
    IP_ADDRESS = 2
    MAC_ADDRESS = 3
    USER_NAME = 4
    EMAIL_ADDRESS = 5
    URL_STRING = 6
    FILE_NAME = 7
    HASH = 8
    PROCESS_NAME = 9
    RESOURCE_UID = 10
    PORT = 11
    SUBNET = 12
    COMMAND_LINE = 13
    COUNTRY = 14
    PROCESS_ID = 15
    HTTP_USER_AGENT = 16
    CWE_OBJECT__UID = 17
    CVE_OBJECT__UID = 18
    USER_CREDENTIAL_ID = 19
    ENDPOINT = 20
    USER = 21
    EMAIL = 22
    UNIFORM_RESOURCE_LOCATOR = 23
    FILE = 24
    PROCESS = 25
    GEO_LOCATION = 26
    CONTAINER = 27
    FINGERPRINT = 30
    USER_OBJECT__UID = 31
    GROUP_OBJECT__NAME = 32
    GROUP_OBJECT__UID = 33
    ACCOUNT_OBJECT__NAME = 34
    ACCOUNT_OBJECT__UID = 35
    SCRIPT_CONTENT = 36
    SERIAL_NUMBER = 37
    RESOURCE_DETAILS_OBJECT__NAME = 38
    PROCESS_ENTITY_OBJECT__UID = 39
    EMAIL_OBJECT__SUBJECT = 40
    EMAIL_OBJECT__UID = 41
    MESSAGE_UID = 42
    ADVISORY_OBJECT__UID = 44
    FILE_PATH = 45
    DEVICE_OBJECT__UID = 47
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
            "HOSTNAME": "Hostname",
            "IP_ADDRESS": "IP Address",
            "MAC_ADDRESS": "MAC Address",
            "USER_NAME": "User Name",
            "EMAIL_ADDRESS": "Email Address",
            "URL_STRING": "URL String",
            "FILE_NAME": "File Name",
            "HASH": "Hash",
            "PROCESS_NAME": "Process Name",
            "RESOURCE_UID": "Resource UID",
            "PORT": "Port",
            "SUBNET": "Subnet",
            "COMMAND_LINE": "Command Line",
            "COUNTRY": "Country",
            "PROCESS_ID": "Process ID",
            "HTTP_USER_AGENT": "HTTP User-Agent",
            "CWE_OBJECT__UID": "CWE Object: uid",
            "CVE_OBJECT__UID": "CVE Object: uid",
            "USER_CREDENTIAL_ID": "User Credential ID",
            "ENDPOINT": "Endpoint",
            "USER": "User",
            "EMAIL": "Email",
            "UNIFORM_RESOURCE_LOCATOR": "Uniform Resource Locator",
            "FILE": "File",
            "PROCESS": "Process",
            "GEO_LOCATION": "Geo Location",
            "CONTAINER": "Container",
            "FINGERPRINT": "Fingerprint",
            "USER_OBJECT__UID": "User Object: uid",
            "GROUP_OBJECT__NAME": "Group Object: name",
            "GROUP_OBJECT__UID": "Group Object: uid",
            "ACCOUNT_OBJECT__NAME": "Account Object: name",
            "ACCOUNT_OBJECT__UID": "Account Object: uid",
            "SCRIPT_CONTENT": "Script Content",
            "SERIAL_NUMBER": "Serial Number",
            "RESOURCE_DETAILS_OBJECT__NAME": "Resource Details Object: name",
            "PROCESS_ENTITY_OBJECT__UID": "Process Entity Object: uid",
            "EMAIL_OBJECT__SUBJECT": "Email Object: subject",
            "EMAIL_OBJECT__UID": "Email Object: uid",
            "MESSAGE_UID": "Message UID",
            "ADVISORY_OBJECT__UID": "Advisory Object: uid",
            "FILE_PATH": "File Path",
            "DEVICE_OBJECT__UID": "Device Object: uid",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Observable(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "observable"

    # Required
    type_id: TypeId

    # Recommended
    name: str | None = None

    # Optional
    reputation: Reputation | None = None
    value: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def type(self) -> str:
        return self.type_id.name

    @type.setter
    def type(self, value: str) -> None:
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
