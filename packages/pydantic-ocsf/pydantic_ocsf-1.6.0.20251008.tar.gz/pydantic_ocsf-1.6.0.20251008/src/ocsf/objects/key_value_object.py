from typing import ClassVar

from pydantic import model_validator

from ocsf.objects.object import Object


class KeyValueObject(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "key_value_object"

    # Required
    name: str

    # Recommended
    value: str | None = None
    values: list[str] | None = None

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(getattr(self, field) is None for field in ["value", "values"]):
            raise ValueError("At least one of `value`, `values` must be provided")
        return self
