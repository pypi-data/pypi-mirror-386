from typing import ClassVar

from ocsf.events.remediation.remediation_activity import RemediationActivity
from ocsf.objects.file import File


class FileRemediationActivity(RemediationActivity):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "File Remediation Activity"
    class_uid: int = 7002
    schema_name: ClassVar[str] = "file_remediation_activity"

    # Required
    file: File
