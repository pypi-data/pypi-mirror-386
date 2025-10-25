from typing import ClassVar

from ocsf.objects.object import Object


class Metric(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "metric"

    # Required
    name: str
    value: str
