from typing import ClassVar

from ocsf.events.discovery.discovery_result import DiscoveryResult
from ocsf.objects.module import Module
from ocsf.objects.process import Process


class ModuleQuery(DiscoveryResult):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Module Query"
    class_uid: int = 5011
    schema_name: ClassVar[str] = "module_query"

    # Required
    module: Module
    process: Process
