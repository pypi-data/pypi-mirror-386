from typing import ClassVar

from ocsf.objects.object import Object


class KeyboardInfo(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "keyboard_info"

    # Optional
    function_keys: int | None = None
    ime: str | None = None
    keyboard_layout: str | None = None
    keyboard_subtype: int | None = None
    keyboard_type: str | None = None
