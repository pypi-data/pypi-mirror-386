from typing import ClassVar

from ocsf.events.discovery.discovery_result import DiscoveryResult
from ocsf.objects.network_interface import NetworkInterface


class NetworksQuery(DiscoveryResult):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Networks Query"
    class_uid: int = 5013
    schema_name: ClassVar[str] = "networks_query"

    # Required
    network_interfaces: list[NetworkInterface]
