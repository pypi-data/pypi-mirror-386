from typing import ClassVar

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects._entity import Entity
from ocsf.objects.device import Device
from ocsf.objects.product import Product


class Logger(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "logger"

    # Recommended
    device: Device | None = None
    log_name: str | None = None
    log_provider: str | None = None
    logged_time: Timestamp | None = None
    name: str | None = None
    product: Product | None = None
    uid: str | None = None

    # Optional
    event_uid: str | None = None
    is_truncated: bool | None = None
    log_level: str | None = None
    log_version: str | None = None
    transmit_time: Timestamp | None = None
    untruncated_size: int | None = None
    version: str | None = None
