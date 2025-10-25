from typing import ClassVar

from ocsf.events.discovery.discovery_result import DiscoveryResult
from ocsf.objects.kernel import Kernel


class KernelObjectQuery(DiscoveryResult):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Kernel Object Query"
    class_uid: int = 5006
    schema_name: ClassVar[str] = "kernel_object_query"

    # Required
    kernel: Kernel
