from typing import ClassVar

from pydantic import model_validator

from ocsf.objects._entity import Entity
from ocsf.objects.location import Location


class Aircraft(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "aircraft"

    # Recommended
    location: Location | None = None
    name: str | None = None
    uid: str | None = None

    # Optional
    model: str | None = None
    serial_number: str | None = None
    speed: str | None = None
    speed_accuracy: str | None = None
    track_direction: str | None = None
    uid_alt: str | None = None
    vertical_speed: str | None = None

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(getattr(self, field) is None for field in ["name", "serial_number", "uid", "uid_alt"]):
            raise ValueError("At least one of `name`, `serial_number`, `uid`, `uid_alt` must be provided")
        return self
