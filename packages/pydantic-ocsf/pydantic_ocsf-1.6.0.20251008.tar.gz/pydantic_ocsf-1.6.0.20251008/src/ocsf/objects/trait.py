from typing import ClassVar

from ocsf.objects._entity import Entity


class Trait(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "trait"

    # Recommended
    name: str | None = None
    uid: str | None = None

    # Optional
    category: str | None = None
    type_: str | None = None
    values: list[str] | None = None
