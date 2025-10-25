import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects.data_classification import DataClassification
from ocsf.objects.policy import Policy


class DataLifecycleStateId(IntEnum):
    UNKNOWN = 0
    DATA_AT_REST = 1
    DATA_IN_TRANSIT = 2
    DATA_IN_USE = 3
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return DataLifecycleStateId[obj]
        else:
            return DataLifecycleStateId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "DATA_AT_REST": "Data at-Rest",
            "DATA_IN_TRANSIT": "Data in-Transit",
            "DATA_IN_USE": "Data in-Use",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DetectionSystemId(IntEnum):
    UNKNOWN = 0
    ENDPOINT = 1
    DLP_GATEWAY = 2
    MOBILE_DEVICE_MANAGEMENT = 3
    DATA_DISCOVERY___CLASSIFICATION = 4
    SECURE_WEB_GATEWAY = 5
    SECURE_EMAIL_GATEWAY = 6
    DIGITAL_RIGHTS_MANAGEMENT = 7
    CLOUD_ACCESS_SECURITY_BROKER = 8
    DATABASE_ACTIVITY_MONITORING = 9
    APPLICATION_LEVEL_DLP = 10
    DEVELOPER_SECURITY = 11
    DATA_SECURITY_POSTURE_MANAGEMENT = 12
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return DetectionSystemId[obj]
        else:
            return DetectionSystemId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "ENDPOINT": "Endpoint",
            "DLP_GATEWAY": "DLP Gateway",
            "MOBILE_DEVICE_MANAGEMENT": "Mobile Device Management",
            "DATA_DISCOVERY___CLASSIFICATION": "Data Discovery & Classification",
            "SECURE_WEB_GATEWAY": "Secure Web Gateway",
            "SECURE_EMAIL_GATEWAY": "Secure Email Gateway",
            "DIGITAL_RIGHTS_MANAGEMENT": "Digital Rights Management",
            "CLOUD_ACCESS_SECURITY_BROKER": "Cloud Access Security Broker",
            "DATABASE_ACTIVITY_MONITORING": "Database Activity Monitoring",
            "APPLICATION_LEVEL_DLP": "Application-Level DLP",
            "DEVELOPER_SECURITY": "Developer Security",
            "DATA_SECURITY_POSTURE_MANAGEMENT": "Data Security Posture Management",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DataSecurity(DataClassification):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "data_security"

    # Recommended
    data_lifecycle_state_id: DataLifecycleStateId | None = None
    detection_pattern: str | None = None
    detection_system_id: DetectionSystemId | None = None
    policy: Policy | None = None

    # Optional
    pattern_match: str | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def data_lifecycle_state(self) -> str | None:
        if self.data_lifecycle_state_id is None:
            return None
        return self.data_lifecycle_state_id.name

    @data_lifecycle_state.setter
    def data_lifecycle_state(self, value: str | None) -> None:
        if value is None:
            self.data_lifecycle_state_id = None
        else:
            self.data_lifecycle_state_id = DataLifecycleStateId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_data_lifecycle_state_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "data_lifecycle_state" in data and "data_lifecycle_state_id" not in data:
            data_lifecycle_state = re.sub(r"\W", "_", data.pop("data_lifecycle_state").upper())
            data["data_lifecycle_state_id"] = DataLifecycleStateId[data_lifecycle_state]
        return data

    @model_validator(mode="after")
    def validate_data_lifecycle_state_after(self) -> Self:
        if self.__pydantic_extra__ and "data_lifecycle_state" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("data_lifecycle_state")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def detection_system(self) -> str | None:
        if self.detection_system_id is None:
            return None
        return self.detection_system_id.name

    @detection_system.setter
    def detection_system(self, value: str | None) -> None:
        if value is None:
            self.detection_system_id = None
        else:
            self.detection_system_id = DetectionSystemId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_detection_system_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "detection_system" in data and "detection_system_id" not in data:
            detection_system = re.sub(r"\W", "_", data.pop("detection_system").upper())
            data["detection_system_id"] = DetectionSystemId[detection_system]
        return data

    @model_validator(mode="after")
    def validate_detection_system_after(self) -> Self:
        if self.__pydantic_extra__ and "detection_system" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("detection_system")
        return self

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(
            getattr(self, field) is None
            for field in ["data_lifecycle_state_id", "detection_pattern", "detection_system_id", "policy"]
        ):
            raise ValueError(
                "At least one of `data_lifecycle_state_id`, `detection_pattern`, `detection_system_id`, `policy` must be provided"
            )
        return self
