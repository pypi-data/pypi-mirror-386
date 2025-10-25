from typing import ClassVar

from ocsf.events.remediation.remediation_activity import RemediationActivity
from ocsf.objects.network_connection_info import NetworkConnectionInfo


class NetworkRemediationActivity(RemediationActivity):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Network Remediation Activity"
    class_uid: int = 7004
    schema_name: ClassVar[str] = "network_remediation_activity"

    # Required
    connection_info: NetworkConnectionInfo
