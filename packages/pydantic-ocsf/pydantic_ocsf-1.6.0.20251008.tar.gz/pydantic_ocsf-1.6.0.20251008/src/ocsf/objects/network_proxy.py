from typing import ClassVar

from ocsf.objects.network_endpoint import NetworkEndpoint


class NetworkProxy(NetworkEndpoint):
    allowed_profiles: ClassVar[list[str]] = ["container"]
    schema_name: ClassVar[str] = "network_proxy"
