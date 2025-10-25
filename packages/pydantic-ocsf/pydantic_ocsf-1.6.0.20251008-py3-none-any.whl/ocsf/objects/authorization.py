from typing import ClassVar

from ocsf.objects.object import Object
from ocsf.objects.policy import Policy


class Authorization(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "authorization"

    # Recommended
    decision: str | None = None

    # Optional
    policy: Policy | None = None
