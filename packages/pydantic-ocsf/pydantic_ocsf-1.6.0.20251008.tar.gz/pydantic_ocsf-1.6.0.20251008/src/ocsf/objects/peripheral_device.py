from typing import ClassVar

from ocsf.objects._entity import Entity


class PeripheralDevice(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "peripheral_device"

    # Required
    class_: str
    name: str

    # Recommended
    model: str | None = None
    serial_number: str | None = None
    uid: str | None = None
    vendor_name: str | None = None
