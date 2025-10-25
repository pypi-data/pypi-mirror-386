import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.datatypes.timestamp import Timestamp
from ocsf.events.network.network import Network
from ocsf.objects.dns_answer import DnsAnswer
from ocsf.objects.dns_query import DnsQuery
from ocsf.objects.network_connection_info import NetworkConnectionInfo
from ocsf.objects.network_endpoint import NetworkEndpoint
from ocsf.objects.network_traffic import NetworkTraffic


class ActivityId(IntEnum):
    UNKNOWN = 0
    QUERY = 1
    RESPONSE = 2
    TRAFFIC = 6
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
            "QUERY": "Query",
            "RESPONSE": "Response",
            "TRAFFIC": "Traffic",
            "OTHER": "Other",
        }
        return name_map[super().name]


class RcodeId(IntEnum):
    NOERROR = 0
    FORMERROR = 1
    SERVERROR = 2
    NXDOMAIN = 3
    NOTIMP = 4
    REFUSED = 5
    YXDOMAIN = 6
    YXRRSET = 7
    NXRRSET = 8
    NOTAUTH = 9
    NOTZONE = 10
    DSOTYPENI = 11
    BADSIG_VERS = 16
    BADKEY = 17
    BADTIME = 18
    BADMODE = 19
    BADNAME = 20
    BADALG = 21
    BADTRUNC = 22
    BADCOOKIE = 23
    UNASSIGNED = 24
    RESERVED = 25
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return RcodeId[obj]
        else:
            return RcodeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "NOERROR": "NoError",
            "FORMERROR": "FormError",
            "SERVERROR": "ServError",
            "NXDOMAIN": "NXDomain",
            "NOTIMP": "NotImp",
            "REFUSED": "Refused",
            "YXDOMAIN": "YXDomain",
            "YXRRSET": "YXRRSet",
            "NXRRSET": "NXRRSet",
            "NOTAUTH": "NotAuth",
            "NOTZONE": "NotZone",
            "DSOTYPENI": "DSOTYPENI",
            "BADSIG_VERS": "BADSIG_VERS",
            "BADKEY": "BADKEY",
            "BADTIME": "BADTIME",
            "BADMODE": "BADMODE",
            "BADNAME": "BADNAME",
            "BADALG": "BADALG",
            "BADTRUNC": "BADTRUNC",
            "BADCOOKIE": "BADCOOKIE",
            "UNASSIGNED": "Unassigned",
            "RESERVED": "Reserved",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DnsActivity(Network):
    allowed_profiles: ClassVar[list[str]] = [
        "network_proxy",
        "load_balancer",
        "cloud",
        "datetime",
        "host",
        "osint",
        "security_control",
    ]
    class_name: str = "DNS Activity"
    class_uid: int = 4003
    schema_name: ClassVar[str] = "dns_activity"

    # Required
    activity_id: ActivityId

    # Recommended
    answers: list[DnsAnswer] | None = None
    dst_endpoint: NetworkEndpoint | None = None
    query: DnsQuery | None = None
    query_time: Timestamp | None = None
    rcode_id: RcodeId | None = None
    response_time: Timestamp | None = None

    # Optional
    connection_info: NetworkConnectionInfo | None = None
    traffic: NetworkTraffic | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def rcode(self) -> str | None:
        if self.rcode_id is None:
            return None
        return self.rcode_id.name

    @rcode.setter
    def rcode(self, value: str | None) -> None:
        if value is None:
            self.rcode_id = None
        else:
            self.rcode_id = RcodeId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_rcode_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "rcode" in data and "rcode_id" not in data:
            rcode = re.sub(r"\W", "_", data.pop("rcode").upper())
            data["rcode_id"] = RcodeId[rcode]
        return data

    @model_validator(mode="after")
    def validate_rcode_after(self) -> Self:
        if self.__pydantic_extra__ and "rcode" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("rcode")
        return self
