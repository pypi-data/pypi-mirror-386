import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self, TYPE_CHECKING, cast

from pydantic import SerializationInfo, SerializerFunctionWrapHandler, computed_field, model_serializer, model_validator

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.enrichment import Enrichment
from ocsf.objects.fingerprint import Fingerprint
from ocsf.objects.metadata import Metadata
from ocsf.objects.observable import Observable
from ocsf.ocsf_object import OcsfObject
from ocsf.profiles.manager import ProfileManager

if TYPE_CHECKING:
    from ocsf.profiles.base_profile import BaseProfile


class ActivityId(IntEnum):
    UNKNOWN = 0
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
            "OTHER": "Other",
        }
        return name_map[super().name]


class SeverityId(IntEnum):
    UNKNOWN = 0
    INFORMATIONAL = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5
    FATAL = 6
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return SeverityId[obj]
        else:
            return SeverityId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "INFORMATIONAL": "Informational",
            "LOW": "Low",
            "MEDIUM": "Medium",
            "HIGH": "High",
            "CRITICAL": "Critical",
            "FATAL": "Fatal",
            "OTHER": "Other",
        }
        return name_map[super().name]


class StatusId(IntEnum):
    UNKNOWN = 0
    SUCCESS = 1
    FAILURE = 2
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return StatusId[obj]
        else:
            return StatusId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "SUCCESS": "Success",
            "FAILURE": "Failure",
            "OTHER": "Other",
        }
        return name_map[super().name]


class BaseEvent(OcsfObject):
    __original_data__: dict[str, Any]
    __profiles__: dict[str, "BaseProfile"]
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    schema_name: ClassVar[str] = "base_event"

    # Required
    activity_id: ActivityId
    category_uid: int = 0
    class_uid: int = 0
    metadata: Metadata
    severity_id: SeverityId
    time: Timestamp

    # Recommended
    message: str | None = None
    observables: list[Observable] | None = None
    status_code: str | None = None
    status_detail: str | None = None
    status_id: StatusId | None = None
    timezone_offset: int | None = None

    # Optional
    category_name: str | None = None
    class_name: str | None = None
    count: int | None = None
    duration: int | None = None
    end_time: Timestamp | None = None
    enrichments: list[Enrichment] | None = None
    raw_data: str | None = None
    raw_data_hash: Fingerprint | None = None
    raw_data_size: int | None = None
    start_time: Timestamp | None = None
    unmapped: dict[str, Any] | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def activity_name(self) -> str:
        return self.activity_id.name

    @activity_name.setter
    def activity_name(self, value: str) -> None:
        self.activity_id = ActivityId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_activity_name_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "activity_name" in data and "activity_id" not in data:
            activity_name = re.sub(r"\W", "_", data.pop("activity_name").upper())
            data["activity_id"] = ActivityId[activity_name]
        return data

    @model_validator(mode="after")
    def validate_activity_name_after(self) -> Self:
        if self.__pydantic_extra__ and "activity_name" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("activity_name")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def severity(self) -> str:
        return self.severity_id.name

    @severity.setter
    def severity(self, value: str) -> None:
        self.severity_id = SeverityId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_severity_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "severity" in data and "severity_id" not in data:
            severity = re.sub(r"\W", "_", data.pop("severity").upper())
            data["severity_id"] = SeverityId[severity]
        return data

    @model_validator(mode="after")
    def validate_severity_after(self) -> Self:
        if self.__pydantic_extra__ and "severity" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("severity")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def status(self) -> str | None:
        if self.status_id is None:
            return None
        return self.status_id.name

    @status.setter
    def status(self, value: str | None) -> None:
        if value is None:
            self.status_id = None
        else:
            self.status_id = StatusId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_status_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "status" in data and "status_id" not in data:
            status = re.sub(r"\W", "_", data.pop("status").upper())
            data["status_id"] = StatusId[status]
        return data

    @model_validator(mode="after")
    def validate_status_after(self) -> Self:
        if self.__pydantic_extra__ and "status" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("status")
        return self

    def model_post_init(self, context: Any) -> None:
        self.__profiles__ = dict()
        return super().model_post_init(context)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def type_uid(self) -> int:
        return self.class_uid * 100 + self.activity_id

    @computed_field  # type: ignore[prop-decorator]
    @property
    def type_name(self) -> str:
        if hasattr(self, "class_name"):
            class_name = self.class_name
        else:
            class_name = "Base Event"
        return f"{class_name}: {self.activity_id.name}"

    @model_validator(mode="before")
    @classmethod
    def handle_type_fields(cls, data: dict[str, Any]) -> dict[str, Any]:
        data.pop("type_uid", None)
        data.pop("type_name", None)
        return data

    @model_validator(mode="after")
    def validate_profiles(self) -> Self:
        if self.metadata and self.metadata.profiles:
            for profile_name in self.metadata.profiles:
                if profile_name not in self.allowed_profiles:
                    raise ValueError(f"`{profile_name}` not allowed for {self.__class__.__name__}")
                profile_class = ProfileManager.get_profile_class(profile_name)
                self.__profiles__[profile_name] = profile_class.model_validate(self)
        return self

    def __getitem__[T: "BaseProfile"](self, profile_class: type[T]) -> T:
        if profile_class.schema_name not in self.__profiles__:
            if profile_class.schema_name not in self.allowed_profiles:
                raise ValueError(f"Profile `{profile_class.schema_name}` not allowed in `{self.schema_name}`")
            raise ValueError(f"Profile `{profile_class.schema_name}` not included in event")
        return cast(T, self.__profiles__[profile_class.schema_name])

    @model_serializer(mode="wrap")
    def serializer(self, handler: SerializerFunctionWrapHandler, info: SerializationInfo) -> dict[str, Any]:
        result = handler(self)
        if self.metadata.profiles:
            for profile in self.metadata.profiles:
                result.update(
                    self.__profiles__[profile].model_dump(
                        mode=info.mode,
                        context=info.context,
                        by_alias=info.by_alias,
                        exclude_unset=info.exclude_unset,
                        exclude_defaults=info.exclude_defaults,
                        exclude_none=info.exclude_none,
                        round_trip=info.round_trip,
                        serialize_as_any=info.serialize_as_any,
                    )
                )
        return result
