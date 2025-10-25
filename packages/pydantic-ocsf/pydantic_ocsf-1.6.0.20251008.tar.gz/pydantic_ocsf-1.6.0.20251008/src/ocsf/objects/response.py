from typing import Any, ClassVar

from ocsf.objects.container import Container
from ocsf.objects.object import Object


class Response(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "response"

    # Recommended
    code: int | None = None
    error: str | None = None
    error_message: str | None = None
    message: str | None = None

    # Optional
    containers: list[Container] | None = None
    data: dict[str, Any] | None = None
    flags: list[str] | None = None
