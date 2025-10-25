import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.datatypes.timestamp import Timestamp
from ocsf.events.application.application import Application
from ocsf.objects.actor import Actor
from ocsf.objects.file import File
from ocsf.objects.http_request import HttpRequest
from ocsf.objects.http_response import HttpResponse
from ocsf.objects.network_connection_info import NetworkConnectionInfo
from ocsf.objects.network_endpoint import NetworkEndpoint


class ActivityId(IntEnum):
    UNKNOWN = 0
    UPLOAD = 1
    DOWNLOAD = 2
    UPDATE = 3
    DELETE = 4
    RENAME = 5
    COPY = 6
    MOVE = 7
    RESTORE = 8
    PREVIEW = 9
    LOCK = 10
    UNLOCK = 11
    SHARE = 12
    UNSHARE = 13
    OPEN = 14
    SYNC = 15
    UNSYNC = 16
    ACCESS_CHECK = 17
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
            "UPLOAD": "Upload",
            "DOWNLOAD": "Download",
            "UPDATE": "Update",
            "DELETE": "Delete",
            "RENAME": "Rename",
            "COPY": "Copy",
            "MOVE": "Move",
            "RESTORE": "Restore",
            "PREVIEW": "Preview",
            "LOCK": "Lock",
            "UNLOCK": "Unlock",
            "SHARE": "Share",
            "UNSHARE": "Unshare",
            "OPEN": "Open",
            "SYNC": "Sync",
            "UNSYNC": "Unsync",
            "ACCESS_CHECK": "Access Check",
            "OTHER": "Other",
        }
        return name_map[super().name]


class ShareTypeId(IntEnum):
    UNKNOWN = 0
    FILE = 1
    PIPE = 2
    PRINT = 3
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return ShareTypeId[obj]
        else:
            return ShareTypeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "FILE": "File",
            "PIPE": "Pipe",
            "PRINT": "Print",
            "OTHER": "Other",
        }
        return name_map[super().name]


class FileHosting(Application):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "File Hosting Activity"
    class_uid: int = 6006
    schema_name: ClassVar[str] = "file_hosting"

    # Required
    activity_id: ActivityId
    actor: Actor
    file: File
    src_endpoint: NetworkEndpoint

    # Recommended
    dst_endpoint: NetworkEndpoint | None = None
    http_request: HttpRequest | None = None

    # Optional
    access_list: list[str] | None = None
    access_mask: int | None = None
    access_result: dict[str, Any] | None = None
    connection_info: NetworkConnectionInfo | None = None
    expiration_time: Timestamp | None = None
    file_result: File | None = None
    http_response: HttpResponse | None = None
    share: str | None = None
    share_type_id: ShareTypeId | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def share_type(self) -> str | None:
        if self.share_type_id is None:
            return None
        return self.share_type_id.name

    @share_type.setter
    def share_type(self, value: str | None) -> None:
        if value is None:
            self.share_type_id = None
        else:
            self.share_type_id = ShareTypeId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_share_type_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "share_type" in data and "share_type_id" not in data:
            share_type = re.sub(r"\W", "_", data.pop("share_type").upper())
            data["share_type_id"] = ShareTypeId[share_type]
        return data

    @model_validator(mode="after")
    def validate_share_type_after(self) -> Self:
        if self.__pydantic_extra__ and "share_type" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("share_type")
        return self
