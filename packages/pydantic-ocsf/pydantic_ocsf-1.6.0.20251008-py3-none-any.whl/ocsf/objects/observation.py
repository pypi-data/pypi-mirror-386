from typing import ClassVar

from ocsf.objects.object import Object
from ocsf.objects.timespan import Timespan


class Observation(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "observation"

    # Required
    value: str

    # Recommended
    count: int | None = None
    timespan: Timespan | None = None
