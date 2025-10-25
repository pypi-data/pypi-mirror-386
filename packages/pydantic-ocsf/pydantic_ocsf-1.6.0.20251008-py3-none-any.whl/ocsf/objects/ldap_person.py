from typing import ClassVar, TYPE_CHECKING

from pydantic import EmailStr

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.key_value_object import KeyValueObject
from ocsf.objects.location import Location
from ocsf.objects.object import Object

if TYPE_CHECKING:
    from ocsf.objects.user import User


class LdapPerson(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "ldap_person"

    # Optional
    cost_center: str | None = None
    created_time: Timestamp | None = None
    deleted_time: Timestamp | None = None
    display_name: str | None = None
    email_addrs: list[EmailStr] | None = None
    employee_uid: str | None = None
    given_name: str | None = None
    hire_time: Timestamp | None = None
    job_title: str | None = None
    labels: list[str] | None = None
    last_login_time: Timestamp | None = None
    ldap_cn: str | None = None
    ldap_dn: str | None = None
    leave_time: Timestamp | None = None
    location: Location | None = None
    manager: "User | None" = None
    modified_time: Timestamp | None = None
    office_location: str | None = None
    phone_number: str | None = None
    surname: str | None = None
    tags: list[KeyValueObject] | None = None
