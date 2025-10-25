from typing import Any, ClassVar

from pydantic import model_validator

from ocsf.objects._entity import Entity
from ocsf.objects.group import Group


class Policy(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "policy"

    # Recommended
    is_applied: bool | None = None
    name: str | None = None
    uid: str | None = None
    version: str | None = None

    # Optional
    data: dict[str, Any] | None = None
    desc: str | None = None
    group: Group | None = None
    type_: str | None = None

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(getattr(self, field) is None for field in ["name", "type", "uid"]):
            raise ValueError("At least one of `name`, `type`, `uid` must be provided")
        return self
