from typing import ClassVar

from ocsf.events.discovery.discovery_result import DiscoveryResult
from ocsf.objects.peripheral_device import PeripheralDevice


class PeripheralDeviceQuery(DiscoveryResult):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Peripheral Device Query"
    class_uid: int = 5014
    schema_name: ClassVar[str] = "peripheral_device_query"

    # Required
    peripheral_device: PeripheralDevice
