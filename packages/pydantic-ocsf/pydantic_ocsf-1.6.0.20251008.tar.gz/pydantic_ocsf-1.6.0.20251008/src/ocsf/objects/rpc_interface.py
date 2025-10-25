from typing import ClassVar
from uuid import UUID

from ocsf.objects.object import Object


class RpcInterface(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "rpc_interface"

    # Required
    uuid: UUID
    version: str

    # Recommended
    ack_reason: int | None = None
    ack_result: int | None = None
