from typing import Annotated, ClassVar, Literal

from pydantic import Field

from ocsf.events.base_event import BaseEvent
from ocsf.objects.actor import Actor
from ocsf.objects.device import Device


class System(BaseEvent):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    category_name: Annotated[Literal["System Activity"], Field(frozen=True)] = "System Activity"
    category_uid: Annotated[Literal[1], Field(frozen=True)] = 1
    schema_name: ClassVar[str] = "system"

    # Required
    actor: Actor
    device: Device
