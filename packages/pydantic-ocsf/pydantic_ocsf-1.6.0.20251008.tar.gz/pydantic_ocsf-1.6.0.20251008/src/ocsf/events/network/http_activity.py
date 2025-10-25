from enum import IntEnum, property as enum_property
from typing import Any, ClassVar

from pydantic import model_validator

from ocsf.events.network.network import Network
from ocsf.objects.file import File
from ocsf.objects.http_cookie import HttpCookie
from ocsf.objects.http_request import HttpRequest
from ocsf.objects.http_response import HttpResponse


class ActivityId(IntEnum):
    UNKNOWN = 0
    CONNECT = 1
    DELETE = 2
    GET = 3
    HEAD = 4
    OPTIONS = 5
    POST = 6
    PUT = 7
    TRACE = 8
    PATCH = 9
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return ActivityId[obj]
        else:
            return ActivityId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "CONNECT": "Connect",
            "DELETE": "Delete",
            "GET": "Get",
            "HEAD": "Head",
            "OPTIONS": "Options",
            "POST": "Post",
            "PUT": "Put",
            "TRACE": "Trace",
            "PATCH": "Patch",
            "OTHER": "Other",
        }
        return name_map[super().name]


class HttpActivity(Network):
    allowed_profiles: ClassVar[list[str]] = [
        "trace",
        "network_proxy",
        "load_balancer",
        "cloud",
        "datetime",
        "host",
        "osint",
        "security_control",
    ]
    class_name: str = "HTTP Activity"
    class_uid: int = 4002
    schema_name: ClassVar[str] = "http_activity"

    # Required
    activity_id: ActivityId

    # Recommended
    http_cookies: list[HttpCookie] | None = None
    http_request: HttpRequest | None = None
    http_response: HttpResponse | None = None
    http_status: int | None = None

    # Optional
    file: File | None = None

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(getattr(self, field) is None for field in ["http_request", "http_response"]):
            raise ValueError("At least one of `http_request`, `http_response` must be provided")
        return self
