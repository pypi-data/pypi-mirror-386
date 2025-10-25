from typing import ClassVar

from ocsf.objects.object import Object


class LongString(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "long_string"

    # Required
    value: str

    # Optional
    is_truncated: bool | None = None
    untruncated_size: int | None = None
