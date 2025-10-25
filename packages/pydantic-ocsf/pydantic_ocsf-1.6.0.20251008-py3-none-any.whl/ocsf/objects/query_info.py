from typing import Any, ClassVar

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects._entity import Entity


class QueryInfo(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "query_info"

    # Required
    query_string: str

    # Recommended
    name: str | None = None
    uid: str | None = None

    # Optional
    bytes: int | None = None
    data: dict[str, Any] | None = None
    query_time: Timestamp | None = None
