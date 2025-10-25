from typing import ClassVar

from ocsf.objects.object import Object


class CisCsc(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "cis_csc"

    # Required
    control: str

    # Recommended
    version: str | None = None
