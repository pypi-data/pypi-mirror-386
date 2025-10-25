from typing import Any, ClassVar

from pydantic import AnyUrl

from ocsf.objects._resource import Resource


class WebResource(Resource):
    allowed_profiles: ClassVar[list[str]] = ["data_classification"]
    schema_name: ClassVar[str] = "web_resource"

    # Recommended
    name: str | None = None
    uid: str | None = None
    url_string: AnyUrl | None = None

    # Optional
    data: dict[str, Any] | None = None
    desc: str | None = None
    type_: str | None = None
