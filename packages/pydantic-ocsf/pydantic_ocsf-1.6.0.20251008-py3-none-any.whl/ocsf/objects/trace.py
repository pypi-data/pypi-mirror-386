from typing import ClassVar

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.object import Object
from ocsf.objects.service import Service
from ocsf.objects.span import Span


class Trace(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "trace"

    # Required
    uid: str

    # Optional
    duration: int | None = None
    end_time: Timestamp | None = None
    flags: list[str] | None = None
    service: Service | None = None
    span: Span | None = None
    start_time: Timestamp | None = None
