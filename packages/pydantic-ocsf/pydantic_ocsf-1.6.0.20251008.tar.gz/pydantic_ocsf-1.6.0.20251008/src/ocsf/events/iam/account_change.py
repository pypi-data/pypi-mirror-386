from enum import IntEnum, property as enum_property
from typing import Any, ClassVar

from ocsf.events.iam.iam import IAM
from ocsf.objects.policy import Policy
from ocsf.objects.user import User


class ActivityId(IntEnum):
    UNKNOWN = 0
    CREATE = 1
    ENABLE = 2
    PASSWORD_CHANGE = 3
    PASSWORD_RESET = 4
    DISABLE = 5
    DELETE = 6
    ATTACH_POLICY = 7
    DETACH_POLICY = 8
    LOCK = 9
    MFA_FACTOR_ENABLE = 10
    MFA_FACTOR_DISABLE = 11
    UNLOCK = 12
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return ActivityId[obj]
        else:
            return ActivityId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "CREATE": "Create",
            "ENABLE": "Enable",
            "PASSWORD_CHANGE": "Password Change",
            "PASSWORD_RESET": "Password Reset",
            "DISABLE": "Disable",
            "DELETE": "Delete",
            "ATTACH_POLICY": "Attach Policy",
            "DETACH_POLICY": "Detach Policy",
            "LOCK": "Lock",
            "MFA_FACTOR_ENABLE": "MFA Factor Enable",
            "MFA_FACTOR_DISABLE": "MFA Factor Disable",
            "UNLOCK": "Unlock",
            "OTHER": "Other",
        }
        return name_map[super().name]


class AccountChange(IAM):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Account Change"
    class_uid: int = 3001
    schema_name: ClassVar[str] = "account_change"

    # Required
    activity_id: ActivityId
    user: User

    # Recommended
    user_result: User | None = None

    # Optional
    policies: list[Policy] | None = None
    policy: Policy | None = None
