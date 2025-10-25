from typing import ClassVar

from ocsf.objects.actor import Actor
from ocsf.objects.device import Device
from ocsf.profiles.base_profile import BaseProfile


class Host(BaseProfile):
    schema_name: ClassVar[str] = "host"

    # Recommended
    device: Device | None = None

    # Optional
    actor: Actor | None = None
