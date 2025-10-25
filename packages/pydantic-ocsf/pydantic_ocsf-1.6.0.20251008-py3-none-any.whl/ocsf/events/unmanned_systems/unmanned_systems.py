from typing import Annotated, ClassVar, Literal

from pydantic import Field

from ocsf.events.base_event import BaseEvent
from ocsf.objects.network_connection_info import NetworkConnectionInfo
from ocsf.objects.network_endpoint import NetworkEndpoint
from ocsf.objects.network_proxy import NetworkProxy
from ocsf.objects.network_traffic import NetworkTraffic
from ocsf.objects.tls import TLS


class UnmannedSystems(BaseEvent):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    category_name: Annotated[Literal["Unmanned Systems"], Field(frozen=True)] = "Unmanned Systems"
    category_uid: Annotated[Literal[8], Field(frozen=True)] = 8
    schema_name: ClassVar[str] = "unmanned_systems"

    # Required
    dst_endpoint: NetworkEndpoint

    # Recommended
    connection_info: NetworkConnectionInfo | None = None
    proxy_endpoint: NetworkProxy | None = None
    src_endpoint: NetworkEndpoint | None = None
    traffic: NetworkTraffic | None = None

    # Optional
    tls: TLS | None = None
