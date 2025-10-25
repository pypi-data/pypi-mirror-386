from enum import IntEnum, property as enum_property
from typing import Any, ClassVar

from ocsf.objects._dns import Dns


class OpcodeId(IntEnum):
    QUERY = 0
    INVERSE_QUERY = 1
    STATUS = 2
    RESERVED = 3
    NOTIFY = 4
    UPDATE = 5
    DSO_MESSAGE = 6
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return OpcodeId[obj]
        else:
            return OpcodeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "QUERY": "Query",
            "INVERSE_QUERY": "Inverse Query",
            "STATUS": "Status",
            "RESERVED": "Reserved",
            "NOTIFY": "Notify",
            "UPDATE": "Update",
            "DSO_MESSAGE": "DSO Message",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DnsQuery(Dns):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "dns_query"

    # Required
    hostname: str

    # Recommended
    opcode_id: OpcodeId | None = None

    # Optional
    opcode: str | None = None
