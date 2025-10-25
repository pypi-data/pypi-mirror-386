from typing import ClassVar

from ocsf.objects.trace import Trace as Trace_
from ocsf.profiles.base_profile import BaseProfile


class Trace(BaseProfile):
    schema_name: ClassVar[str] = "trace"

    # Recommended
    trace: Trace_ | None = None
