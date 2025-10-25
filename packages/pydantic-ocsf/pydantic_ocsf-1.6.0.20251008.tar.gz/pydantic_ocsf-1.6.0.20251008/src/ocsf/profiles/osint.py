from typing import ClassVar

from ocsf.objects.osint import Osint as Osint_
from ocsf.profiles.base_profile import BaseProfile


class Osint(BaseProfile):
    schema_name: ClassVar[str] = "osint"

    # Required
    osint: list[Osint_]
