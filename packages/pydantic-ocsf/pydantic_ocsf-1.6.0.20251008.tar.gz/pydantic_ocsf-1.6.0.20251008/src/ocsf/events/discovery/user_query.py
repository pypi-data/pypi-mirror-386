from typing import ClassVar

from ocsf.events.discovery.discovery_result import DiscoveryResult
from ocsf.objects.user import User


class UserQuery(DiscoveryResult):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "User Query"
    class_uid: int = 5018
    schema_name: ClassVar[str] = "user_query"

    # Required
    user: User
