from typing import ClassVar

from ocsf.events.discovery.discovery_result import DiscoveryResult
from ocsf.objects.startup_item import StartupItem


class StartupItemQuery(DiscoveryResult):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Startup Item Query"
    class_uid: int = 5022
    schema_name: ClassVar[str] = "startup_item_query"

    # Required
    startup_item: StartupItem
