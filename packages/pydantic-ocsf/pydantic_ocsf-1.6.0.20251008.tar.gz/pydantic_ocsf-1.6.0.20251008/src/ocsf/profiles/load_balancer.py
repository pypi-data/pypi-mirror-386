from typing import ClassVar

from ocsf.objects.load_balancer import LoadBalancer as LoadBalancer_
from ocsf.profiles.base_profile import BaseProfile


class LoadBalancer(BaseProfile):
    schema_name: ClassVar[str] = "load_balancer"

    # Recommended
    load_balancer: LoadBalancer_ | None = None
