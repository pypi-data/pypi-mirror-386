from typing import ClassVar

from pydantic import model_validator

from ocsf.objects.authorization import Authorization
from ocsf.objects.idp import Idp
from ocsf.objects.object import Object
from ocsf.objects.process import Process
from ocsf.objects.session import Session
from ocsf.objects.user import User


class Actor(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "actor"

    # Recommended
    process: Process | None = None
    user: User | None = None

    # Optional
    app_name: str | None = None
    app_uid: str | None = None
    authorizations: list[Authorization] | None = None
    idp: Idp | None = None
    invoked_by: str | None = None
    session: Session | None = None

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(
            getattr(self, field) is None
            for field in ["process", "user", "invoked_by", "session", "app_name", "app_uid"]
        ):
            raise ValueError(
                "At least one of `process`, `user`, `invoked_by`, `session`, `app_name`, `app_uid` must be provided"
            )
        return self
