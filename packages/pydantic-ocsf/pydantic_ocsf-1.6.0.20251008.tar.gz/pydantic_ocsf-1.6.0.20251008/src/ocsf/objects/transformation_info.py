from typing import ClassVar

from pydantic import AnyUrl

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects._entity import Entity
from ocsf.objects.product import Product


class TransformationInfo(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "transformation_info"

    # Recommended
    name: str | None = None
    time: Timestamp | None = None
    url_string: AnyUrl | None = None

    # Optional
    lang: str | None = None
    product: Product | None = None
    uid: str | None = None
