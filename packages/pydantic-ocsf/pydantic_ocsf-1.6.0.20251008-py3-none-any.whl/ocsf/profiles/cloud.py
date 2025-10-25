from typing import ClassVar

from ocsf.objects.api import API
from ocsf.objects.cloud import Cloud as Cloud_
from ocsf.profiles.base_profile import BaseProfile


class Cloud(BaseProfile):
    schema_name: ClassVar[str] = "cloud"

    # Required
    cloud: Cloud_

    # Optional
    api: API | None = None
