import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import EmailStr, computed_field, model_validator

from ocsf.objects.device import Device
from ocsf.objects.object import Object


class FactorTypeId(IntEnum):
    UNKNOWN = 0
    SMS = 1
    SECURITY_QUESTION = 2
    PHONE_CALL = 3
    BIOMETRIC = 4
    PUSH_NOTIFICATION = 5
    HARDWARE_TOKEN = 6
    OTP = 7
    EMAIL = 8
    U2F = 9
    WEBAUTHN = 10
    PASSWORD = 11
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return FactorTypeId[obj]
        else:
            return FactorTypeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "SMS": "SMS",
            "SECURITY_QUESTION": "Security Question",
            "PHONE_CALL": "Phone Call",
            "BIOMETRIC": "Biometric",
            "PUSH_NOTIFICATION": "Push Notification",
            "HARDWARE_TOKEN": "Hardware Token",
            "OTP": "OTP",
            "EMAIL": "Email",
            "U2F": "U2F",
            "WEBAUTHN": "WebAuthn",
            "PASSWORD": "Password",
            "OTHER": "Other",
        }
        return name_map[super().name]


class AuthFactor(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "auth_factor"

    # Required
    factor_type_id: FactorTypeId

    # Recommended
    device: Device | None = None
    is_hotp: bool | None = None
    is_totp: bool | None = None
    provider: str | None = None

    # Optional
    email_addr: EmailStr | None = None
    phone_number: str | None = None
    security_questions: list[str] | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def factor_type(self) -> str:
        return self.factor_type_id.name

    @factor_type.setter
    def factor_type(self, value: str) -> None:
        self.factor_type_id = FactorTypeId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_factor_type_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "factor_type" in data and "factor_type_id" not in data:
            factor_type = re.sub(r"\W", "_", data.pop("factor_type").upper())
            data["factor_type_id"] = FactorTypeId[factor_type]
        return data

    @model_validator(mode="after")
    def validate_factor_type_after(self) -> Self:
        if self.__pydantic_extra__ and "factor_type" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("factor_type")
        return self
