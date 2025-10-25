from typing import ClassVar
from uuid import UUID

from pydantic import model_validator

from ocsf.objects.fingerprint import Fingerprint
from ocsf.objects.image import Image
from ocsf.objects.key_value_object import KeyValueObject
from ocsf.objects.object import Object


class Container(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "container"

    # Recommended
    hash: Fingerprint | None = None
    image: Image | None = None
    name: str | None = None
    size: int | None = None
    uid: str | None = None

    # Optional
    labels: list[str] | None = None
    network_driver: str | None = None
    orchestrator: str | None = None
    pod_uuid: UUID | None = None
    runtime: str | None = None
    tag: str | None = None
    tags: list[KeyValueObject] | None = None

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(getattr(self, field) is None for field in ["uid", "name"]):
            raise ValueError("At least one of `uid`, `name` must be provided")
        return self
