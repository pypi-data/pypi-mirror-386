from enum import StrEnum, property as enum_property
from typing import Any, ClassVar

from pydantic import IPvAnyAddress

from ocsf.objects.http_header import HttpHeader
from ocsf.objects.object import Object
from ocsf.objects.url import Url


class HttpMethod(StrEnum):
    CONNECT = "CONNECT"
    DELETE = "DELETE"
    GET = "GET"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    PATCH = "PATCH"
    POST = "POST"
    PUT = "PUT"
    TRACE = "TRACE"

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return HttpMethod[obj]
        else:
            return HttpMethod(obj)

    @enum_property
    def name(self):
        name_map = {
            "CONNECT": "Connect",
            "DELETE": "Delete",
            "GET": "Get",
            "HEAD": "Head",
            "OPTIONS": "Options",
            "PATCH": "Patch",
            "POST": "Post",
            "PUT": "Put",
            "TRACE": "Trace",
        }
        return name_map[super().name]


class HttpRequest(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "http_request"

    # Recommended
    http_headers: list[HttpHeader] | None = None
    http_method: HttpMethod | None = None
    url: Url | None = None
    user_agent: str | None = None
    version: str | None = None

    # Optional
    args: str | None = None
    body_length: int | None = None
    length: int | None = None
    referrer: str | None = None
    uid: str | None = None
    x_forwarded_for: list[IPvAnyAddress] | None = None
