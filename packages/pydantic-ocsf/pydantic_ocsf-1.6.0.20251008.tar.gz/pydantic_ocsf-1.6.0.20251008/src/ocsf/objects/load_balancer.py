from typing import ClassVar

from pydantic import IPvAnyAddress

from ocsf.objects._entity import Entity
from ocsf.objects.endpoint_connection import EndpointConnection
from ocsf.objects.metric import Metric
from ocsf.objects.network_endpoint import NetworkEndpoint


class LoadBalancer(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "load_balancer"

    # Recommended
    code: int | None = None
    dst_endpoint: NetworkEndpoint | None = None
    endpoint_connections: list[EndpointConnection] | None = None
    name: str | None = None
    uid: str | None = None

    # Optional
    classification: str | None = None
    error_message: str | None = None
    ip: IPvAnyAddress | None = None
    message: str | None = None
    metrics: list[Metric] | None = None
    status_detail: str | None = None
