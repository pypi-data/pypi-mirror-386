import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects.object import Object


class AlgorithmId(IntEnum):
    UNKNOWN = 0
    DES = 1
    TRIPLEDES = 2
    AES = 3
    RSA = 4
    ECC = 5
    SM2 = 6
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return AlgorithmId[obj]
        else:
            return AlgorithmId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "DES": "DES",
            "TRIPLEDES": "TripleDES",
            "AES": "AES",
            "RSA": "RSA",
            "ECC": "ECC",
            "SM2": "SM2",
            "OTHER": "Other",
        }
        return name_map[super().name]


class EncryptionDetails(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "encryption_details"

    # Recommended
    algorithm_id: AlgorithmId | None = None
    type_: str | None = None

    # Optional
    key_length: int | None = None
    key_uid: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def algorithm(self) -> str | None:
        if self.algorithm_id is None:
            return None
        return self.algorithm_id.name

    @algorithm.setter
    def algorithm(self, value: str | None) -> None:
        if value is None:
            self.algorithm_id = None
        else:
            self.algorithm_id = AlgorithmId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_algorithm_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "algorithm" in data and "algorithm_id" not in data:
            algorithm = re.sub(r"\W", "_", data.pop("algorithm").upper())
            data["algorithm_id"] = AlgorithmId[algorithm]
        return data

    @model_validator(mode="after")
    def validate_algorithm_after(self) -> Self:
        if self.__pydantic_extra__ and "algorithm" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("algorithm")
        return self
