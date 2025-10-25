from typing import ClassVar

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.object import Object


class Epss(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "epss"

    # Required
    score: str

    # Recommended
    created_time: Timestamp | None = None
    version: str | None = None

    # Optional
    percentile: float | None = None
