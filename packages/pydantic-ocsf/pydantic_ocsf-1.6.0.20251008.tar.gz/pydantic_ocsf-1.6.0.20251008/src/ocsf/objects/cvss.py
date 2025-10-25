from enum import StrEnum, property as enum_property
from typing import Any, ClassVar

from pydantic import AnyUrl

from ocsf.objects.metric import Metric
from ocsf.objects.object import Object


class Depth(StrEnum):
    BASE = "Base"
    ENVIRONMENTAL = "Environmental"
    TEMPORAL = "Temporal"

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return Depth[obj]
        else:
            return Depth(obj)

    @enum_property
    def name(self):
        name_map = {
            "BASE": "Base",
            "ENVIRONMENTAL": "Environmental",
            "TEMPORAL": "Temporal",
        }
        return name_map[super().name]


class Cvss(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "cvss"

    # Required
    base_score: float
    version: str

    # Recommended
    depth: Depth | None = None
    overall_score: float | None = None
    vendor_name: str | None = None

    # Optional
    metrics: list[Metric] | None = None
    severity: str | None = None
    src_url: AnyUrl | None = None
    vector_string: str | None = None
