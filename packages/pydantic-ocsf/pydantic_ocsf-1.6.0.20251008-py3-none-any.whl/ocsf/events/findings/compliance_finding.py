from typing import ClassVar

from ocsf.events.findings.finding import Finding
from ocsf.objects.compliance import Compliance
from ocsf.objects.evidences import Evidences
from ocsf.objects.remediation import Remediation
from ocsf.objects.resource_details import ResourceDetails


class ComplianceFinding(Finding):
    allowed_profiles: ClassVar[list[str]] = ["incident", "cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Compliance Finding"
    class_uid: int = 2003
    schema_name: ClassVar[str] = "compliance_finding"

    # Required
    compliance: Compliance

    # Recommended
    remediation: Remediation | None = None
    resource: ResourceDetails | None = None
    resources: list[ResourceDetails] | None = None

    # Optional
    evidences: list[Evidences] | None = None
