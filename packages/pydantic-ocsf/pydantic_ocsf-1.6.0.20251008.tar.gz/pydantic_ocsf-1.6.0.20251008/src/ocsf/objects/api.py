from typing import ClassVar

from ocsf.objects.group import Group
from ocsf.objects.object import Object
from ocsf.objects.request import Request
from ocsf.objects.response import Response
from ocsf.objects.service import Service


class API(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "api"

    # Required
    operation: str

    # Recommended
    request: Request | None = None
    response: Response | None = None

    # Optional
    group: Group | None = None
    service: Service | None = None
    version: str | None = None
