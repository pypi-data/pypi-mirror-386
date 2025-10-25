from typing import ClassVar

from ocsf.objects._entity import Entity
from ocsf.objects.key_value_object import KeyValueObject


class Service(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "service"

    # Recommended
    name: str | None = None
    uid: str | None = None
    version: str | None = None

    # Optional
    labels: list[str] | None = None
    tags: list[KeyValueObject] | None = None
