from typing import Any, ClassVar

from pydantic import AnyUrl

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.object import Object
from ocsf.objects.reputation import Reputation


class Enrichment(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "enrichment"

    # Required
    data: dict[str, Any]
    name: str
    value: str

    # Recommended
    created_time: Timestamp | None = None
    provider: str | None = None
    short_desc: str | None = None
    src_url: AnyUrl | None = None
    type_: str | None = None

    # Optional
    desc: str | None = None
    reputation: Reputation | None = None
