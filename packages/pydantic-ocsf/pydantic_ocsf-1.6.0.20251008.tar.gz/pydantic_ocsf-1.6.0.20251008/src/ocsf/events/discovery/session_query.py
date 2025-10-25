from typing import ClassVar

from ocsf.events.discovery.discovery_result import DiscoveryResult
from ocsf.objects.session import Session


class SessionQuery(DiscoveryResult):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "User Session Query"
    class_uid: int = 5017
    schema_name: ClassVar[str] = "session_query"

    # Required
    session: Session
