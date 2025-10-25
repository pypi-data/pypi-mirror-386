from typing import ClassVar

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.object import Object
from ocsf.objects.programmatic_credential import ProgrammaticCredential


class IdentityActivityMetrics(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "identity_activity_metrics"

    # Recommended
    last_seen_time: Timestamp | None = None

    # Optional
    first_seen_time: Timestamp | None = None
    last_authentication_time: Timestamp | None = None
    password_last_used_time: Timestamp | None = None
    programmatic_credentials: list[ProgrammaticCredential] | None = None
