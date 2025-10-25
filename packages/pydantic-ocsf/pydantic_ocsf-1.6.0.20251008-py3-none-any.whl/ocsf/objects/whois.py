import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import EmailStr, IPvAnyNetwork, computed_field, model_validator

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.autonomous_system import AutonomousSystem
from ocsf.objects.domain_contact import DomainContact
from ocsf.objects.object import Object


class DnssecStatusId(IntEnum):
    UNKNOWN = 0
    SIGNED = 1
    UNSIGNED = 2
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return DnssecStatusId[obj]
        else:
            return DnssecStatusId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "SIGNED": "Signed",
            "UNSIGNED": "Unsigned",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Whois(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "whois"

    # Recommended
    created_time: Timestamp | None = None
    dnssec_status_id: DnssecStatusId | None = None
    domain: str | None = None
    domain_contacts: list[DomainContact] | None = None
    last_seen_time: Timestamp | None = None
    name_servers: list[str] | None = None
    registrar: str | None = None
    status: str | None = None

    # Optional
    autonomous_system: AutonomousSystem | None = None
    email_addr: EmailStr | None = None
    isp: str | None = None
    isp_org: str | None = None
    phone_number: str | None = None
    subdomains: list[str] | None = None
    subnet: IPvAnyNetwork | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def dnssec_status(self) -> str | None:
        if self.dnssec_status_id is None:
            return None
        return self.dnssec_status_id.name

    @dnssec_status.setter
    def dnssec_status(self, value: str | None) -> None:
        if value is None:
            self.dnssec_status_id = None
        else:
            self.dnssec_status_id = DnssecStatusId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_dnssec_status_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "dnssec_status" in data and "dnssec_status_id" not in data:
            dnssec_status = re.sub(r"\W", "_", data.pop("dnssec_status").upper())
            data["dnssec_status_id"] = DnssecStatusId[dnssec_status]
        return data

    @model_validator(mode="after")
    def validate_dnssec_status_after(self) -> Self:
        if self.__pydantic_extra__ and "dnssec_status" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("dnssec_status")
        return self
