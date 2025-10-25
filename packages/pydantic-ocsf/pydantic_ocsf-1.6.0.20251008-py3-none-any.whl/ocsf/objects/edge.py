from typing import Any, ClassVar

from ocsf.objects._entity import Entity


class Edge(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "edge"

    # Required
    source: str
    target: str

    # Recommended
    name: str | None = None
    relation: str | None = None
    uid: str | None = None

    # Optional
    data: dict[str, Any] | None = None
    is_directed: bool | None = None
