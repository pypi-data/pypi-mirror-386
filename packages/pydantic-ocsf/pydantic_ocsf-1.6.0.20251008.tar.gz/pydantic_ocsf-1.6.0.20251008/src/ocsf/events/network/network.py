from typing import Annotated, ClassVar, Literal

from pydantic import Field, model_validator

from ocsf.events.base_event import BaseEvent
from ocsf.objects.ja4_fingerprint import Ja4Fingerprint
from ocsf.objects.network_connection_info import NetworkConnectionInfo
from ocsf.objects.network_endpoint import NetworkEndpoint
from ocsf.objects.network_proxy import NetworkProxy
from ocsf.objects.network_traffic import NetworkTraffic
from ocsf.objects.tls import TLS


class Network(BaseEvent):
    allowed_profiles: ClassVar[list[str]] = [
        "network_proxy",
        "load_balancer",
        "cloud",
        "datetime",
        "host",
        "osint",
        "security_control",
    ]
    category_name: Annotated[Literal["Network Activity"], Field(frozen=True)] = "Network Activity"
    category_uid: Annotated[Literal[4], Field(frozen=True)] = 4
    schema_name: ClassVar[str] = "network"

    # Recommended
    connection_info: NetworkConnectionInfo | None = None
    dst_endpoint: NetworkEndpoint | None = None
    proxy: NetworkProxy | None = None
    src_endpoint: NetworkEndpoint | None = None
    traffic: NetworkTraffic | None = None

    # Optional
    app_name: str | None = None
    ja4_fingerprint_list: list[Ja4Fingerprint] | None = None
    tls: TLS | None = None

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(getattr(self, field) is None for field in ["dst_endpoint", "src_endpoint"]):
            raise ValueError("At least one of `dst_endpoint`, `src_endpoint` must be provided")
        return self
