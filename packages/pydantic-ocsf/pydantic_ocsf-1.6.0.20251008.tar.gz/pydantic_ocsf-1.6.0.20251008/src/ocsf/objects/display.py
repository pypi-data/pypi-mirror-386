from typing import ClassVar

from ocsf.objects.object import Object


class Display(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "display"

    # Optional
    color_depth: int | None = None
    physical_height: int | None = None
    physical_orientation: int | None = None
    physical_width: int | None = None
    scale_factor: int | None = None
