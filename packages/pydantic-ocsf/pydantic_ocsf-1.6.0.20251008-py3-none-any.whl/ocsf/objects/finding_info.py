from typing import ClassVar

from pydantic import AnyUrl

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.analytic import Analytic
from ocsf.objects.attack import Attack
from ocsf.objects.graph import Graph
from ocsf.objects.key_value_object import KeyValueObject
from ocsf.objects.kill_chain_phase import KillChainPhase
from ocsf.objects.object import Object
from ocsf.objects.product import Product
from ocsf.objects.related_event import RelatedEvent
from ocsf.objects.trait import Trait


class FindingInfo(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "finding_info"

    # Required
    uid: str

    # Recommended
    analytic: Analytic | None = None
    title: str | None = None

    # Optional
    attack_graph: Graph | None = None
    attacks: list[Attack] | None = None
    created_time: Timestamp | None = None
    data_sources: list[str] | None = None
    desc: str | None = None
    first_seen_time: Timestamp | None = None
    kill_chain: list[KillChainPhase] | None = None
    last_seen_time: Timestamp | None = None
    modified_time: Timestamp | None = None
    product: Product | None = None
    product_uid: str | None = None
    related_analytics: list[Analytic] | None = None
    related_events: list[RelatedEvent] | None = None
    related_events_count: int | None = None
    src_url: AnyUrl | None = None
    tags: list[KeyValueObject] | None = None
    traits: list[Trait] | None = None
    types: list[str] | None = None
    uid_alt: str | None = None
