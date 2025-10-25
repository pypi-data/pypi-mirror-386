from typing import ClassVar

from ocsf.objects.object import Object
from ocsf.objects.observation import Observation


class Baseline(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "baseline"

    # Required
    observation_parameter: str
    observations: list[Observation]

    # Recommended
    observation_type: str | None = None
    observed_pattern: str | None = None
