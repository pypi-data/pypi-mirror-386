from typing import ClassVar

from pydantic import model_validator

from ocsf.objects.network_endpoint import NetworkEndpoint
from ocsf.objects.object import Object


class EndpointConnection(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "endpoint_connection"

    # Recommended
    code: int | None = None
    network_endpoint: NetworkEndpoint | None = None

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(getattr(self, field) is None for field in ["network_endpoint", "code"]):
            raise ValueError("At least one of `network_endpoint`, `code` must be provided")
        return self
