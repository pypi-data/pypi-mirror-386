from typing import ClassVar

from pydantic import AnyUrl

from ocsf.objects._entity import Entity


class Tactic(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "tactic"

    # Recommended
    name: str | None = None
    uid: str | None = None

    # Optional
    src_url: AnyUrl | None = None
