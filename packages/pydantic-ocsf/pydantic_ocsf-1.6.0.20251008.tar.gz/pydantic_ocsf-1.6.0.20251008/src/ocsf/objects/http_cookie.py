from typing import ClassVar

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.object import Object


class HttpCookie(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "http_cookie"

    # Required
    name: str
    value: str

    # Optional
    domain: str | None = None
    expiration_time: Timestamp | None = None
    http_only: bool | None = None
    is_http_only: bool | None = None
    is_secure: bool | None = None
    path: str | None = None
    samesite: str | None = None
    secure: bool | None = None
