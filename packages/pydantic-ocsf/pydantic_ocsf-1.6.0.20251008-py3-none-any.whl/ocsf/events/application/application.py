from typing import Annotated, ClassVar, Literal

from pydantic import Field

from ocsf.events.base_event import BaseEvent


class Application(BaseEvent):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    category_name: Annotated[Literal["Application Activity"], Field(frozen=True)] = "Application Activity"
    category_uid: Annotated[Literal[6], Field(frozen=True)] = 6
    schema_name: ClassVar[str] = "application"
