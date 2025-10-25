from typing import ClassVar

from ocsf.objects._entity import Entity


class Rule(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "rule"

    # Recommended
    name: str | None = None
    uid: str | None = None

    # Optional
    category: str | None = None
    desc: str | None = None
    type_: str | None = None
    version: str | None = None
