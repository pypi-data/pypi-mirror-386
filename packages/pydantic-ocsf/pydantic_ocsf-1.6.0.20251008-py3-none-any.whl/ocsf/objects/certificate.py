from typing import ClassVar

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.fingerprint import Fingerprint
from ocsf.objects.object import Object
from ocsf.objects.san import San


class Certificate(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "certificate"

    # Required
    issuer: str
    serial_number: str

    # Recommended
    created_time: Timestamp | None = None
    expiration_time: Timestamp | None = None
    fingerprints: list[Fingerprint] | None = None
    is_self_signed: bool | None = None
    subject: str | None = None
    version: str | None = None

    # Optional
    sans: list[San] | None = None
    uid: str | None = None
