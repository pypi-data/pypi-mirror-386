from typing import Any, ClassVar

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects._entity import Entity
from ocsf.objects.key_value_object import KeyValueObject


class Resource(Entity):
    allowed_profiles: ClassVar[list[str]] = ["data_classification"]
    schema_name: ClassVar[str] = "_resource"

    # Recommended
    name: str | None = None
    uid: str | None = None

    # Optional
    created_time: Timestamp | None = None
    data: dict[str, Any] | None = None
    labels: list[str] | None = None
    modified_time: Timestamp | None = None
    tags: list[KeyValueObject] | None = None
    type_: str | None = None
    uid_alt: str | None = None
