from typing import ClassVar

from ocsf.events.discovery.discovery_result import DiscoveryResult
from ocsf.objects.service import Service


class ServiceQuery(DiscoveryResult):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Service Query"
    class_uid: int = 5016
    schema_name: ClassVar[str] = "service_query"

    # Required
    service: Service
