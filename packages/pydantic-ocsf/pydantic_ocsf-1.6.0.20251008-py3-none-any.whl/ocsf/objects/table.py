from typing import ClassVar

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects._entity import Entity
from ocsf.objects.group import Group


class Table(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "table"

    # Recommended
    name: str | None = None
    uid: str | None = None

    # Optional
    created_time: Timestamp | None = None
    desc: str | None = None
    groups: list[Group] | None = None
    modified_time: Timestamp | None = None
    size: int | None = None
