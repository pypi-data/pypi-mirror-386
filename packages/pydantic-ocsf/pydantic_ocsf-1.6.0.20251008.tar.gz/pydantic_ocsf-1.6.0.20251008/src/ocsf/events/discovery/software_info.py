from typing import ClassVar

from ocsf.events.discovery.discovery import Discovery
from ocsf.objects.actor import Actor
from ocsf.objects.device import Device
from ocsf.objects.package import Package
from ocsf.objects.product import Product
from ocsf.objects.sbom import Sbom


class SoftwareInfo(Discovery):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Software Inventory Info"
    class_uid: int = 5020
    schema_name: ClassVar[str] = "software_info"

    # Required
    device: Device

    # Recommended
    package: Package | None = None
    sbom: Sbom | None = None

    # Optional
    actor: Actor | None = None
    product: Product | None = None
