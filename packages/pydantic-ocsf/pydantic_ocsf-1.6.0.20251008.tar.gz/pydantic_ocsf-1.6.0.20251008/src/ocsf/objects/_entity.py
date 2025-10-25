from typing import ClassVar

from pydantic import model_validator

from ocsf.objects.object import Object


class Entity(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "_entity"

    # Recommended
    name: str | None = None
    uid: str | None = None

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(getattr(self, field) is None for field in ["name", "uid"]):
            raise ValueError("At least one of `name`, `uid` must be provided")
        return self
