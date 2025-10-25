from enum import IntEnum, property as enum_property
from typing import Any, ClassVar

from ocsf.events.application.application import Application
from ocsf.objects.actor import Actor
from ocsf.objects.api import API
from ocsf.objects.http_request import HttpRequest
from ocsf.objects.http_response import HttpResponse
from ocsf.objects.network_endpoint import NetworkEndpoint
from ocsf.objects.resource_details import ResourceDetails


class ActivityId(IntEnum):
    UNKNOWN = 0
    CREATE = 1
    READ = 2
    UPDATE = 3
    DELETE = 4
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
            "CREATE": "Create",
            "READ": "Read",
            "UPDATE": "Update",
            "DELETE": "Delete",
            "OTHER": "Other",
        }
        return name_map[super().name]


class APIActivity(Application):
    allowed_profiles: ClassVar[list[str]] = ["trace", "cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "API Activity"
    class_uid: int = 6003
    schema_name: ClassVar[str] = "api_activity"

    # Required
    activity_id: ActivityId
    actor: Actor
    api: API
    src_endpoint: NetworkEndpoint

    # Recommended
    dst_endpoint: NetworkEndpoint | None = None
    http_request: HttpRequest | None = None
    http_response: HttpResponse | None = None
    resources: list[ResourceDetails] | None = None
