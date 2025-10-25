from typing import Any, ClassVar

from pydantic import AnyUrl

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.object import Object
from ocsf.objects.product import Product
from ocsf.objects.related_event import RelatedEvent
from ocsf.objects.remediation import Remediation


class Finding(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "finding"

    # Required
    title: str
    uid: str

    # Optional
    created_time: Timestamp | None = None
    desc: str | None = None
    first_seen_time: Timestamp | None = None
    last_seen_time: Timestamp | None = None
    modified_time: Timestamp | None = None
    product: Product | None = None
    product_uid: str | None = None
    related_events: list[RelatedEvent] | None = None
    remediation: Remediation | None = None
    src_url: AnyUrl | None = None
    supporting_data: dict[str, Any] | None = None
    types: list[str] | None = None
