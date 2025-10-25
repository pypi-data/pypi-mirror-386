import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.events.network.network import Network
from ocsf.objects.dce_rpc import DceRpc
from ocsf.objects.file import File
from ocsf.objects.response import Response


class ActivityId(IntEnum):
    UNKNOWN = 0
    FILE_SUPERSEDE = 1
    FILE_OPEN = 2
    FILE_CREATE = 3
    FILE_OPEN_IF = 4
    FILE_OVERWRITE = 5
    FILE_OVERWRITE_IF = 6
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
            "FILE_SUPERSEDE": "File Supersede",
            "FILE_OPEN": "File Open",
            "FILE_CREATE": "File Create",
            "FILE_OPEN_IF": "File Open If",
            "FILE_OVERWRITE": "File Overwrite",
            "FILE_OVERWRITE_IF": "File Overwrite If",
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


class SmbActivity(Network):
    allowed_profiles: ClassVar[list[str]] = [
        "network_proxy",
        "load_balancer",
        "cloud",
        "datetime",
        "host",
        "osint",
        "security_control",
    ]
    class_name: str = "SMB Activity"
    class_uid: int = 4006
    schema_name: ClassVar[str] = "smb_activity"

    # Required
    activity_id: ActivityId

    # Recommended
    client_dialects: list[str] | None = None
    command: str | None = None
    dialect: str | None = None
    file: File | None = None
    open_type: str | None = None
    response: Response | None = None
    share: str | None = None
    share_type_id: ShareTypeId | None = None
    tree_uid: str | None = None

    # Optional
    dce_rpc: DceRpc | None = None

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
