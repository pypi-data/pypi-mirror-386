from typing import ClassVar

from ocsf.objects.key_value_object import KeyValueObject
from ocsf.objects.object import Object
from ocsf.objects.policy import Policy


class PermissionAnalysisResult(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "permission_analysis_result"

    # Recommended
    policy: Policy | None = None

    # Optional
    condition_keys: list[KeyValueObject] | None = None
    granted_privileges: list[str] | None = None
    unused_privileges_count: int | None = None
    unused_services_count: int | None = None
