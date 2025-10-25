from typing import ClassVar

from ocsf.objects._entity import Entity
from ocsf.objects.policy import Policy


class Assessment(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "assessment"

    # Required
    meets_criteria: bool

    # Recommended
    desc: str | None = None
    name: str | None = None

    # Optional
    category: str | None = None
    policy: Policy | None = None
    uid: str | None = None
