from typing import ClassVar

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.object import Object


class ProgrammaticCredential(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "programmatic_credential"

    # Required
    uid: str

    # Recommended
    type_: str | None = None

    # Optional
    last_used_time: Timestamp | None = None
