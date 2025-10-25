from typing import ClassVar

from ocsf.events.discovery.discovery_result import DiscoveryResult
from ocsf.objects.file import File


class FolderQuery(DiscoveryResult):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Folder Query"
    class_uid: int = 5008
    schema_name: ClassVar[str] = "folder_query"

    # Required
    folder: File
