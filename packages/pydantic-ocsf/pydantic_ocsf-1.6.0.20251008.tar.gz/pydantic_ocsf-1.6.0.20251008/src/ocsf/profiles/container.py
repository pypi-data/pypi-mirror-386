from typing import ClassVar

from ocsf.objects.container import Container as Container_
from ocsf.profiles.base_profile import BaseProfile


class Container(BaseProfile):
    schema_name: ClassVar[str] = "container"

    # Recommended
    container: Container_ | None = None
    namespace_pid: int | None = None
