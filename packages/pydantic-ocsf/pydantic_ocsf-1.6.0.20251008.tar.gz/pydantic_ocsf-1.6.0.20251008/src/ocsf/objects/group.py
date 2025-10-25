from typing import ClassVar

from ocsf.objects._entity import Entity


class Group(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "group"

    # Recommended
    name: str | None = None
    uid: str | None = None

    # Optional
    desc: str | None = None
    domain: str | None = None
    privileges: list[str] | None = None
    type_: str | None = None
