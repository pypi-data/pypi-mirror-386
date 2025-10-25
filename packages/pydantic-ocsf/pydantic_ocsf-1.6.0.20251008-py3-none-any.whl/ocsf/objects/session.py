from typing import ClassVar
from uuid import UUID

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.object import Object


class Session(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "session"

    # Recommended
    created_time: Timestamp | None = None
    is_remote: bool | None = None
    issuer: str | None = None
    uid: str | None = None

    # Optional
    count: int | None = None
    credential_uid: str | None = None
    expiration_reason: str | None = None
    expiration_time: Timestamp | None = None
    is_mfa: bool | None = None
    is_vpn: bool | None = None
    terminal: str | None = None
    uid_alt: str | None = None
    uuid: UUID | None = None
