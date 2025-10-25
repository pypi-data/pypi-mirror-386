from typing import Annotated, ClassVar

from annotated_types import Ge, Lt

from ocsf.objects.object import Object


class PortInfo(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "port_info"

    # Required
    port: Annotated[int, Ge(0), Lt(65536)]

    # Recommended
    protocol_name: str | None = None

    # Optional
    protocol_num: int | None = None
