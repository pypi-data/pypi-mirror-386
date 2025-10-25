from typing import ClassVar

from ocsf.objects.object import Object


class Campaign(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "campaign"

    # Required
    name: str
