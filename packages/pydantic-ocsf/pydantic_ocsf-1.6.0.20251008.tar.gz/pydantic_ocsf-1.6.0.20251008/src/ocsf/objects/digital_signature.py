import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.certificate import Certificate
from ocsf.objects.fingerprint import Fingerprint
from ocsf.objects.object import Object


class AlgorithmId(IntEnum):
    UNKNOWN = 0
    DSA = 1
    RSA = 2
    ECDSA = 3
    AUTHENTICODE = 4
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
            "DSA": "DSA",
            "RSA": "RSA",
            "ECDSA": "ECDSA",
            "AUTHENTICODE": "Authenticode",
            "OTHER": "Other",
        }
        return name_map[super().name]


class StateId(IntEnum):
    UNKNOWN = 0
    VALID = 1
    EXPIRED = 2
    REVOKED = 3
    SUSPENDED = 4
    PENDING = 5
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return StateId[obj]
        else:
            return StateId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "VALID": "Valid",
            "EXPIRED": "Expired",
            "REVOKED": "Revoked",
            "SUSPENDED": "Suspended",
            "PENDING": "Pending",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DigitalSignature(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "digital_signature"

    # Required
    algorithm_id: AlgorithmId

    # Recommended
    certificate: Certificate | None = None

    # Optional
    created_time: Timestamp | None = None
    developer_uid: str | None = None
    digest: Fingerprint | None = None
    state_id: StateId | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def algorithm(self) -> str:
        return self.algorithm_id.name

    @algorithm.setter
    def algorithm(self, value: str) -> None:
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

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def state(self) -> str | None:
        if self.state_id is None:
            return None
        return self.state_id.name

    @state.setter
    def state(self, value: str | None) -> None:
        if value is None:
            self.state_id = None
        else:
            self.state_id = StateId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_state_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "state" in data and "state_id" not in data:
            state = re.sub(r"\W", "_", data.pop("state").upper())
            data["state_id"] = StateId[state]
        return data

    @model_validator(mode="after")
    def validate_state_after(self) -> Self:
        if self.__pydantic_extra__ and "state" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("state")
        return self
