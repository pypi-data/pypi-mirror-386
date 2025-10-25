from typing import ClassVar

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.object import Object
from ocsf.objects.service import Service


class Span(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "span"

    # Required
    end_time: Timestamp
    start_time: Timestamp
    uid: str

    # Optional
    duration: int | None = None
    message: str | None = None
    operation: str | None = None
    parent_uid: str | None = None
    service: Service | None = None
    status_code: str | None = None
