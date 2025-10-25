from typing import ClassVar

from ocsf.objects._entity import Entity


class Extension(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "extension"

    # Required
    name: str
    uid: str
    version: str
