from typing import ClassVar

from ocsf.objects.additional_restriction import AdditionalRestriction
from ocsf.objects.key_value_object import KeyValueObject
from ocsf.objects.object import Object
from ocsf.objects.user import User


class AccessAnalysisResult(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "access_analysis_result"

    # Required
    accessors: list[User]

    # Recommended
    access_level: str | None = None

    # Optional
    access_type: str | None = None
    additional_restrictions: list[AdditionalRestriction] | None = None
    condition_keys: list[KeyValueObject] | None = None
    granted_privileges: list[str] | None = None
