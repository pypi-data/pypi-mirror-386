from typing import ClassVar

from ocsf.events.discovery.discovery_result import DiscoveryResult
from ocsf.objects.group import Group
from ocsf.objects.user import User


class AdminGroupQuery(DiscoveryResult):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Admin Group Query"
    class_uid: int = 5009
    schema_name: ClassVar[str] = "admin_group_query"

    # Required
    group: Group

    # Recommended
    users: list[User] | None = None
