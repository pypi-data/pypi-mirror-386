from typing import ClassVar
from uuid import UUID

from pydantic import model_validator

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects._entity import Entity


class ProcessEntity(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "process_entity"

    # Recommended
    cmd_line: str | None = None
    cpid: UUID | None = None
    created_time: Timestamp | None = None
    name: str | None = None
    pid: int | None = None
    uid: str | None = None

    # Optional
    path: str | None = None

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(getattr(self, field) is None for field in ["cmd_line", "name", "path", "pid", "uid", "cpid"]):
            raise ValueError("At least one of `cmd_line`, `name`, `path`, `pid`, `uid`, `cpid` must be provided")
        return self
