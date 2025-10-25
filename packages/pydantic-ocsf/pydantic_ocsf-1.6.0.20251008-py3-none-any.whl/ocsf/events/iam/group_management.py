from enum import IntEnum, property as enum_property
from typing import Any, ClassVar

from ocsf.events.iam.iam import IAM
from ocsf.objects.group import Group
from ocsf.objects.resource_details import ResourceDetails
from ocsf.objects.user import User


class ActivityId(IntEnum):
    UNKNOWN = 0
    ASSIGN_PRIVILEGES = 1
    REVOKE_PRIVILEGES = 2
    ADD_USER = 3
    REMOVE_USER = 4
    DELETE = 5
    CREATE = 6
    ADD_SUBGROUP = 7
    REMOVE_SUBGROUP = 8
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
            "ASSIGN_PRIVILEGES": "Assign Privileges",
            "REVOKE_PRIVILEGES": "Revoke Privileges",
            "ADD_USER": "Add User",
            "REMOVE_USER": "Remove User",
            "DELETE": "Delete",
            "CREATE": "Create",
            "ADD_SUBGROUP": "Add Subgroup",
            "REMOVE_SUBGROUP": "Remove Subgroup",
            "OTHER": "Other",
        }
        return name_map[super().name]


class GroupManagement(IAM):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Group Management"
    class_uid: int = 3006
    schema_name: ClassVar[str] = "group_management"

    # Required
    activity_id: ActivityId
    group: Group

    # Recommended
    privileges: list[str] | None = None
    resource: ResourceDetails | None = None
    subgroup: Group | None = None
    user: User | None = None
