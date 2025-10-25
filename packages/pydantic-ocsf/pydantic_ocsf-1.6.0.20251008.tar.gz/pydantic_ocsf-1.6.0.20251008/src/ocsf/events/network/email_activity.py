import re
from enum import IntEnum, property as enum_property
from typing import Annotated, Any, ClassVar, Literal, Self

from pydantic import EmailStr, Field, computed_field, model_validator

from ocsf.events.base_event import BaseEvent
from ocsf.objects.email import Email
from ocsf.objects.email_auth import EmailAuth
from ocsf.objects.network_endpoint import NetworkEndpoint


class ActivityId(IntEnum):
    UNKNOWN = 0
    SEND = 1
    RECEIVE = 2
    SCAN = 3
    TRACE = 4
    MTA_RELAY = 5
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
            "SEND": "Send",
            "RECEIVE": "Receive",
            "SCAN": "Scan",
            "TRACE": "Trace",
            "MTA_RELAY": "MTA Relay",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DirectionId(IntEnum):
    UNKNOWN = 0
    INBOUND = 1
    OUTBOUND = 2
    INTERNAL = 3
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return DirectionId[obj]
        else:
            return DirectionId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "INBOUND": "Inbound",
            "OUTBOUND": "Outbound",
            "INTERNAL": "Internal",
            "OTHER": "Other",
        }
        return name_map[super().name]


class EmailActivity(BaseEvent):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    category_name: Annotated[Literal["Network Activity"], Field(frozen=True)] = "Network Activity"
    category_uid: Annotated[Literal[4], Field(frozen=True)] = 4
    schema_name: ClassVar[str] = "email_activity"

    # Required
    activity_id: ActivityId
    direction_id: DirectionId
    email: Email

    # Recommended
    command: str | None = None
    dst_endpoint: NetworkEndpoint | None = None
    email_auth: EmailAuth | None = None
    from_: EmailStr | None = None
    message_trace_uid: str | None = None
    protocol_name: str | None = None
    smtp_hello: str | None = None
    src_endpoint: NetworkEndpoint | None = None
    to: list[EmailStr] | None = None

    # Optional
    attempt: int | None = None
    banner: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def direction(self) -> str:
        return self.direction_id.name

    @direction.setter
    def direction(self, value: str) -> None:
        self.direction_id = DirectionId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_direction_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "direction" in data and "direction_id" not in data:
            direction = re.sub(r"\W", "_", data.pop("direction").upper())
            data["direction_id"] = DirectionId[direction]
        return data

    @model_validator(mode="after")
    def validate_direction_after(self) -> Self:
        if self.__pydantic_extra__ and "direction" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("direction")
        return self
