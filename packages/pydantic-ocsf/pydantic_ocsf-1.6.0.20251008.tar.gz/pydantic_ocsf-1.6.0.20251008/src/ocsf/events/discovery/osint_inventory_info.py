from typing import ClassVar

from ocsf.events.discovery.discovery import Discovery
from ocsf.objects.actor import Actor
from ocsf.objects.osint import Osint


class OsintInventoryInfo(Discovery):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "OSINT Inventory Info"
    class_uid: int = 5021
    schema_name: ClassVar[str] = "osint_inventory_info"

    # Required
    osint: list[Osint]

    # Optional
    actor: Actor | None = None
