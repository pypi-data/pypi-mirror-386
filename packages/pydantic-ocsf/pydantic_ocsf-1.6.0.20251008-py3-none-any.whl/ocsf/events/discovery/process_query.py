from typing import ClassVar

from ocsf.events.discovery.discovery_result import DiscoveryResult
from ocsf.objects.process import Process


class ProcessQuery(DiscoveryResult):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Process Query"
    class_uid: int = 5015
    schema_name: ClassVar[str] = "process_query"

    # Required
    process: Process
