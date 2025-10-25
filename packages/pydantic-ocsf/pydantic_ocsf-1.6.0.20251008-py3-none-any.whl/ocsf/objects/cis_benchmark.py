from typing import ClassVar

from ocsf.objects.cis_control import CisControl
from ocsf.objects.object import Object


class CisBenchmark(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "cis_benchmark"

    # Required
    name: str

    # Recommended
    cis_controls: list[CisControl] | None = None

    # Optional
    desc: str | None = None
