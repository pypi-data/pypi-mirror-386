from typing import ClassVar

from pydantic import model_validator

from ocsf.objects.object import Object


class Location(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "location"

    # Recommended
    city: str | None = None
    continent: str | None = None
    country: str | None = None

    # Optional
    aerial_height: str | None = None
    coordinates: list[float] | None = None
    desc: str | None = None
    geodetic_altitude: str | None = None
    geodetic_vertical_accuracy: str | None = None
    geohash: str | None = None
    horizontal_accuracy: str | None = None
    is_on_premises: bool | None = None
    isp: str | None = None
    lat: float | None = None
    long: float | None = None
    postal_code: str | None = None
    pressure_altitude: str | None = None
    provider: str | None = None
    region: str | None = None

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(getattr(self, field) is None for field in ["city", "country", "postal_code", "region"]):
            raise ValueError("At least one of `city`, `country`, `postal_code`, `region` must be provided")
        return self
