from typing import ClassVar

from ocsf.objects.fingerprint import Fingerprint
from ocsf.objects.object import Object


class Hassh(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "hassh"

    # Required
    fingerprint: Fingerprint

    # Recommended
    algorithm: str | None = None
