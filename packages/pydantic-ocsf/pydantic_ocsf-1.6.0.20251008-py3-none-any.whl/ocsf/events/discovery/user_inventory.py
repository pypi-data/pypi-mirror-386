from typing import ClassVar

from ocsf.events.discovery.discovery import Discovery
from ocsf.objects.actor import Actor
from ocsf.objects.user import User


class UserInventory(Discovery):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "User Inventory Info"
    class_uid: int = 5003
    schema_name: ClassVar[str] = "user_inventory"

    # Required
    user: User

    # Optional
    actor: Actor | None = None
