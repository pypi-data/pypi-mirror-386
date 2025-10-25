from typing import ClassVar

from ocsf.objects.object import Object
from ocsf.objects.occurrence_details import OccurrenceDetails


class DiscoveryDetails(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "discovery_details"

    # Recommended
    count: int | None = None
    type_: str | None = None

    # Optional
    occurrence_details: OccurrenceDetails | None = None
    occurrences: list[OccurrenceDetails] | None = None
    value: str | None = None
