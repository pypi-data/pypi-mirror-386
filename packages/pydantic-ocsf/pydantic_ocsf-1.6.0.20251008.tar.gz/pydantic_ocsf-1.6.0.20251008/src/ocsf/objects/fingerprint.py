import hashlib
import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects.object import Object


class AlgorithmId(IntEnum):
    UNKNOWN = 0
    MD5 = 1
    SHA_1 = 2
    SHA_256 = 3
    SHA_512 = 4
    CTPH = 5
    TLSH = 6
    QUICKXORHASH = 7
    SHA_224 = 8
    SHA_384 = 9
    SHA_512_224 = 10
    SHA_512_256 = 11
    SHA3_224 = 12
    SHA3_256 = 13
    SHA3_384 = 14
    SHA3_512 = 15
    XXHASH_H3_64_BIT = 16
    XXHASH_H3_128_BIT = 17
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
            "MD5": "MD5",
            "SHA_1": "SHA-1",
            "SHA_256": "SHA-256",
            "SHA_512": "SHA-512",
            "CTPH": "CTPH",
            "TLSH": "TLSH",
            "QUICKXORHASH": "quickXorHash",
            "SHA_224": "SHA-224",
            "SHA_384": "SHA-384",
            "SHA_512_224": "SHA-512/224",
            "SHA_512_256": "SHA-512/256",
            "SHA3_224": "SHA3-224",
            "SHA3_256": "SHA3-256",
            "SHA3_384": "SHA3-384",
            "SHA3_512": "SHA3-512",
            "XXHASH_H3_64_BIT": "xxHash H3 64-bit",
            "XXHASH_H3_128_BIT": "xxHash H3 128-bit",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Fingerprint(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "fingerprint"

    # Required
    algorithm_id: AlgorithmId
    value: str

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

    @classmethod
    def generate_md5(cls, raw_data: str | bytes) -> "Fingerprint":
        if isinstance(raw_data, str):
            raw_data = raw_data.encode()
        h = hashlib.new("MD5")
        h.update(raw_data)
        return cls(algorithm_id=AlgorithmId.MD5, value=h.hexdigest())

    @classmethod
    def generate_sha_1(cls, raw_data: str | bytes) -> "Fingerprint":
        if isinstance(raw_data, str):
            raw_data = raw_data.encode()
        h = hashlib.new("SHA-1")
        h.update(raw_data)
        return cls(algorithm_id=AlgorithmId.SHA_1, value=h.hexdigest())

    @classmethod
    def generate_sha_256(cls, raw_data: str | bytes) -> "Fingerprint":
        if isinstance(raw_data, str):
            raw_data = raw_data.encode()
        h = hashlib.new("SHA-256")
        h.update(raw_data)
        return cls(algorithm_id=AlgorithmId.SHA_256, value=h.hexdigest())

    @classmethod
    def generate_sha_512(cls, raw_data: str | bytes) -> "Fingerprint":
        if isinstance(raw_data, str):
            raw_data = raw_data.encode()
        h = hashlib.new("SHA-512")
        h.update(raw_data)
        return cls(algorithm_id=AlgorithmId.SHA_512, value=h.hexdigest())

    @classmethod
    def generate_sha_224(cls, raw_data: str | bytes) -> "Fingerprint":
        if isinstance(raw_data, str):
            raw_data = raw_data.encode()
        h = hashlib.new("SHA-224")
        h.update(raw_data)
        return cls(algorithm_id=AlgorithmId.SHA_224, value=h.hexdigest())

    @classmethod
    def generate_sha_384(cls, raw_data: str | bytes) -> "Fingerprint":
        if isinstance(raw_data, str):
            raw_data = raw_data.encode()
        h = hashlib.new("SHA-384")
        h.update(raw_data)
        return cls(algorithm_id=AlgorithmId.SHA_384, value=h.hexdigest())

    @classmethod
    def generate_sha_512_224(cls, raw_data: str | bytes) -> "Fingerprint":
        if isinstance(raw_data, str):
            raw_data = raw_data.encode()
        h = hashlib.new("SHA-512/224")
        h.update(raw_data)
        return cls(algorithm_id=AlgorithmId.SHA_512_224, value=h.hexdigest())

    @classmethod
    def generate_sha_512_256(cls, raw_data: str | bytes) -> "Fingerprint":
        if isinstance(raw_data, str):
            raw_data = raw_data.encode()
        h = hashlib.new("SHA-512/256")
        h.update(raw_data)
        return cls(algorithm_id=AlgorithmId.SHA_512_256, value=h.hexdigest())

    @classmethod
    def generate_sha3_224(cls, raw_data: str | bytes) -> "Fingerprint":
        if isinstance(raw_data, str):
            raw_data = raw_data.encode()
        h = hashlib.new("SHA3-224")
        h.update(raw_data)
        return cls(algorithm_id=AlgorithmId.SHA3_224, value=h.hexdigest())

    @classmethod
    def generate_sha3_256(cls, raw_data: str | bytes) -> "Fingerprint":
        if isinstance(raw_data, str):
            raw_data = raw_data.encode()
        h = hashlib.new("SHA3-256")
        h.update(raw_data)
        return cls(algorithm_id=AlgorithmId.SHA3_256, value=h.hexdigest())

    @classmethod
    def generate_sha3_384(cls, raw_data: str | bytes) -> "Fingerprint":
        if isinstance(raw_data, str):
            raw_data = raw_data.encode()
        h = hashlib.new("SHA3-384")
        h.update(raw_data)
        return cls(algorithm_id=AlgorithmId.SHA3_384, value=h.hexdigest())

    @classmethod
    def generate_sha3_512(cls, raw_data: str | bytes) -> "Fingerprint":
        if isinstance(raw_data, str):
            raw_data = raw_data.encode()
        h = hashlib.new("SHA3-512")
        h.update(raw_data)
        return cls(algorithm_id=AlgorithmId.SHA3_512, value=h.hexdigest())
