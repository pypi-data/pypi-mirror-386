from enum import IntEnum, property as enum_property
from typing import Any, ClassVar

from ocsf.events.application.application import Application
from ocsf.objects.http_request import HttpRequest
from ocsf.objects.http_response import HttpResponse
from ocsf.objects.network_endpoint import NetworkEndpoint
from ocsf.objects.network_proxy import NetworkProxy
from ocsf.objects.tls import TLS
from ocsf.objects.web_resource import WebResource


class ActivityId(IntEnum):
    UNKNOWN = 0
    ACCESS_GRANT = 1
    ACCESS_DENY = 2
    ACCESS_REVOKE = 3
    ACCESS_ERROR = 4
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
            "ACCESS_GRANT": "Access Grant",
            "ACCESS_DENY": "Access Deny",
            "ACCESS_REVOKE": "Access Revoke",
            "ACCESS_ERROR": "Access Error",
            "OTHER": "Other",
        }
        return name_map[super().name]


class WebResourceAccessActivity(Application):
    allowed_profiles: ClassVar[list[str]] = ["network_proxy", "cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Web Resource Access Activity"
    class_uid: int = 6004
    schema_name: ClassVar[str] = "web_resource_access_activity"

    # Required
    activity_id: ActivityId
    http_request: HttpRequest
    web_resources: list[WebResource]

    # Recommended
    src_endpoint: NetworkEndpoint | None = None

    # Optional
    http_response: HttpResponse | None = None
    proxy: NetworkProxy | None = None
    tls: TLS | None = None
