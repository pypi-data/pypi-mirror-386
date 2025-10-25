from typing import ClassVar

from pydantic import AnyUrl

from ocsf.objects._entity import Entity
from ocsf.objects.feature import Feature


class Product(Entity):
    allowed_profiles: ClassVar[list[str]] = ["data_classification"]
    schema_name: ClassVar[str] = "product"

    # Recommended
    name: str | None = None
    uid: str | None = None
    vendor_name: str | None = None
    version: str | None = None

    # Optional
    cpe_name: str | None = None
    feature: Feature | None = None
    lang: str | None = None
    path: str | None = None
    url_string: AnyUrl | None = None
