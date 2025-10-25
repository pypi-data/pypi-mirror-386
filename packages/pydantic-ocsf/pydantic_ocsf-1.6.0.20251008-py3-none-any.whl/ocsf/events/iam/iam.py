from typing import Annotated, ClassVar, Literal

from pydantic import Field

from ocsf.events.base_event import BaseEvent
from ocsf.objects.actor import Actor
from ocsf.objects.http_request import HttpRequest
from ocsf.objects.http_response import HttpResponse
from ocsf.objects.network_endpoint import NetworkEndpoint


class IAM(BaseEvent):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    category_name: Annotated[Literal["Identity & Access Management"], Field(frozen=True)] = (
        "Identity & Access Management"
    )
    category_uid: Annotated[Literal[3], Field(frozen=True)] = 3
    schema_name: ClassVar[str] = "iam"

    # Recommended
    actor: Actor | None = None
    src_endpoint: NetworkEndpoint | None = None

    # Optional
    http_request: HttpRequest | None = None
    http_response: HttpResponse | None = None
