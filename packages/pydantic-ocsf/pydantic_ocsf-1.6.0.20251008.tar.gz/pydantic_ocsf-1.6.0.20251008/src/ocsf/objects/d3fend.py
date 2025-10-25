from typing import ClassVar

from pydantic import model_validator

from ocsf.objects.d3f_tactic import D3FTactic
from ocsf.objects.d3f_technique import D3FTechnique
from ocsf.objects.object import Object


class D3Fend(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "d3fend"

    # Recommended
    d3f_tactic: D3FTactic | None = None
    d3f_technique: D3FTechnique | None = None
    version: str | None = None

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(getattr(self, field) is None for field in ["d3f_tactic", "d3f_technique"]):
            raise ValueError("At least one of `d3f_tactic`, `d3f_technique` must be provided")
        return self
