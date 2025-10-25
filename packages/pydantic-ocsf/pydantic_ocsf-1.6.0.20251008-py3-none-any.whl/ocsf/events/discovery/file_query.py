from typing import ClassVar

from ocsf.events.discovery.discovery_result import DiscoveryResult
from ocsf.objects.file import File


class FileQuery(DiscoveryResult):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "File Query"
    class_uid: int = 5007
    schema_name: ClassVar[str] = "file_query"

    # Required
    file: File
