from typing import ClassVar

from ocsf.objects.object import Object
from ocsf.objects.rpc_interface import RpcInterface


class DceRpc(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "dce_rpc"

    # Required
    flags: list[str]
    rpc_interface: RpcInterface

    # Recommended
    command: str | None = None
    command_response: str | None = None
    opnum: int | None = None
