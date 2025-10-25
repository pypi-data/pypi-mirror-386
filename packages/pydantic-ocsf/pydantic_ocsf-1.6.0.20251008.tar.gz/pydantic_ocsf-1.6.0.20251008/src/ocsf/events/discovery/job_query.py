from typing import ClassVar

from ocsf.events.discovery.discovery_result import DiscoveryResult
from ocsf.objects.job import Job


class JobQuery(DiscoveryResult):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Job Query"
    class_uid: int = 5010
    schema_name: ClassVar[str] = "job_query"

    # Required
    job: Job
