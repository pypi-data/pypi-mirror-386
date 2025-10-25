from typing import ClassVar

from pydantic import AnyUrl

from ocsf.objects.object import Object


class Cwe(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "cwe"

    # Required
    uid: str

    # Optional
    caption: str | None = None
    src_url: AnyUrl | None = None
