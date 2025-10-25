from typing import ClassVar

from ocsf.events.discovery.discovery import Discovery
from ocsf.objects.actor import Actor
from ocsf.objects.device import Device


class InventoryInfo(Discovery):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Device Inventory Info"
    class_uid: int = 5001
    schema_name: ClassVar[str] = "inventory_info"

    # Required
    device: Device

    # Optional
    actor: Actor | None = None
