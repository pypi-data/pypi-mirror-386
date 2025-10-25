from typing import ClassVar

from ocsf.objects.object import Object


class CisControl(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "cis_control"

    # Required
    name: str

    # Recommended
    version: str | None = None

    # Optional
    desc: str | None = None
