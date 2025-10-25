from typing import ClassVar

from ocsf.events.remediation.remediation_activity import RemediationActivity
from ocsf.objects.process import Process


class ProcessRemediationActivity(RemediationActivity):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Process Remediation Activity"
    class_uid: int = 7003
    schema_name: ClassVar[str] = "process_remediation_activity"

    # Required
    process: Process
