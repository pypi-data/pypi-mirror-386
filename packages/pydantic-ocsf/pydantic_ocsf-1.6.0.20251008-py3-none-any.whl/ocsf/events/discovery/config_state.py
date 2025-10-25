from typing import ClassVar

from ocsf.events.discovery.discovery import Discovery
from ocsf.objects.actor import Actor
from ocsf.objects.assessment import Assessment
from ocsf.objects.cis_benchmark_result import CisBenchmarkResult
from ocsf.objects.device import Device


class ConfigState(Discovery):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Device Config State"
    class_uid: int = 5002
    schema_name: ClassVar[str] = "config_state"

    # Required
    device: Device

    # Recommended
    cis_benchmark_result: CisBenchmarkResult | None = None

    # Optional
    actor: Actor | None = None
    assessments: list[Assessment] | None = None
