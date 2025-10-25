from typing import ClassVar

from ocsf.objects.file import File
from ocsf.objects.object import Object
from ocsf.objects.remediation import Remediation
from ocsf.objects.rule import Rule
from ocsf.objects.user import User


class AffectedCode(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "affected_code"

    # Required
    file: File

    # Recommended
    end_column: int | None = None
    end_line: int | None = None
    rule: Rule | None = None
    start_column: int | None = None
    start_line: int | None = None

    # Optional
    owner: User | None = None
    remediation: Remediation | None = None
