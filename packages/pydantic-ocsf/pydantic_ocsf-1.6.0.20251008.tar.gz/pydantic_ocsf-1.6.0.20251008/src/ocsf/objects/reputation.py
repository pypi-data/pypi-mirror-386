import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects.object import Object


class ScoreId(IntEnum):
    UNKNOWN = 0
    VERY_SAFE = 1
    SAFE = 2
    PROBABLY_SAFE = 3
    LEANS_SAFE = 4
    MAY_NOT_BE_SAFE = 5
    EXERCISE_CAUTION = 6
    SUSPICIOUS_RISKY = 7
    POSSIBLY_MALICIOUS = 8
    PROBABLY_MALICIOUS = 9
    MALICIOUS = 10
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return ScoreId[obj]
        else:
            return ScoreId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "VERY_SAFE": "Very Safe",
            "SAFE": "Safe",
            "PROBABLY_SAFE": "Probably Safe",
            "LEANS_SAFE": "Leans Safe",
            "MAY_NOT_BE_SAFE": "May not be Safe",
            "EXERCISE_CAUTION": "Exercise Caution",
            "SUSPICIOUS_RISKY": "Suspicious/Risky",
            "POSSIBLY_MALICIOUS": "Possibly Malicious",
            "PROBABLY_MALICIOUS": "Probably Malicious",
            "MALICIOUS": "Malicious",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Reputation(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "reputation"

    # Required
    base_score: float
    score_id: ScoreId

    # Recommended
    provider: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def score(self) -> str:
        return self.score_id.name

    @score.setter
    def score(self, value: str) -> None:
        self.score_id = ScoreId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_score_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "score" in data and "score_id" not in data:
            score = re.sub(r"\W", "_", data.pop("score").upper())
            data["score_id"] = ScoreId[score]
        return data

    @model_validator(mode="after")
    def validate_score_after(self) -> Self:
        if self.__pydantic_extra__ and "score" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("score")
        return self
