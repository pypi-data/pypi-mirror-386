import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects.file import File
from ocsf.objects.group import Group
from ocsf.objects.job import Job
from ocsf.objects.kernel import Kernel
from ocsf.objects.module import Module
from ocsf.objects.network_connection_info import NetworkConnectionInfo
from ocsf.objects.network_interface import NetworkInterface
from ocsf.objects.peripheral_device import PeripheralDevice
from ocsf.objects.process import Process
from ocsf.objects.service import Service
from ocsf.objects.session import Session
from ocsf.objects.startup_item import StartupItem
from ocsf.objects.user import User
from ocsf.ocsf_object import OcsfObject


class QueryTypeId(IntEnum):
    UNKNOWN = 0
    KERNEL = 1
    FILE = 2
    FOLDER = 3
    ADMIN_GROUP = 4
    JOB = 5
    MODULE = 6
    NETWORK_CONNECTION = 7
    NETWORK_INTERFACES = 8
    PERIPHERAL_DEVICE = 9
    PROCESS = 10
    SERVICE = 11
    SESSION = 12
    USER = 13
    USERS = 14
    STARTUP_ITEM = 15
    REGISTRY_KEY = 16
    REGISTRY_VALUE = 17
    PREFETCH = 18
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return QueryTypeId[obj]
        else:
            return QueryTypeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "KERNEL": "Kernel",
            "FILE": "File",
            "FOLDER": "Folder",
            "ADMIN_GROUP": "Admin Group",
            "JOB": "Job",
            "MODULE": "Module",
            "NETWORK_CONNECTION": "Network Connection",
            "NETWORK_INTERFACES": "Network Interfaces",
            "PERIPHERAL_DEVICE": "Peripheral Device",
            "PROCESS": "Process",
            "SERVICE": "Service",
            "SESSION": "Session",
            "USER": "User",
            "USERS": "Users",
            "STARTUP_ITEM": "Startup Item",
            "REGISTRY_KEY": "Registry Key",
            "REGISTRY_VALUE": "Registry Value",
            "PREFETCH": "Prefetch",
            "OTHER": "Other",
        }
        return name_map[super().name]


class TcpStateId(IntEnum):
    UNKNOWN = 0
    ESTABLISHED = 1
    SYN_SENT = 2
    SYN_RECEIVED = 3
    FIN_WAIT_1 = 4
    FIN_WAIT_2 = 5
    TIME_WAIT = 6
    CLOSED = 7
    CLOSE_WAIT = 8
    LAST_ACK = 9
    LISTEN = 10
    CLOSING = 11

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return TcpStateId[obj]
        else:
            return TcpStateId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "ESTABLISHED": "ESTABLISHED",
            "SYN_SENT": "SYN-SENT",
            "SYN_RECEIVED": "SYN-RECEIVED",
            "FIN_WAIT_1": "FIN-WAIT-1",
            "FIN_WAIT_2": "FIN-WAIT-2",
            "TIME_WAIT": "TIME-WAIT",
            "CLOSED": "CLOSED",
            "CLOSE_WAIT": "CLOSE-WAIT",
            "LAST_ACK": "LAST-ACK",
            "LISTEN": "LISTEN",
            "CLOSING": "CLOSING",
        }
        return name_map[super().name]


class QueryEvidence(OcsfObject):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "query_evidence"

    # Required
    query_type_id: QueryTypeId

    # Recommended
    connection_info: NetworkConnectionInfo | None = None
    file: File | None = None
    folder: File | None = None
    group: Group | None = None
    job: Job | None = None
    kernel: Kernel | None = None
    module: Module | None = None
    network_interfaces: list[NetworkInterface] | None = None
    peripheral_device: PeripheralDevice | None = None
    process: Process | None = None
    service: Service | None = None
    session: Session | None = None
    startup_item: StartupItem | None = None
    user: User | None = None

    # Optional
    state: str | None = None
    tcp_state_id: TcpStateId | None = None
    users: list[User] | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def query_type(self) -> str:
        return self.query_type_id.name

    @query_type.setter
    def query_type(self, value: str) -> None:
        self.query_type_id = QueryTypeId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_query_type_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "query_type" in data and "query_type_id" not in data:
            query_type = re.sub(r"\W", "_", data.pop("query_type").upper())
            data["query_type_id"] = QueryTypeId[query_type]
        return data

    @model_validator(mode="after")
    def validate_query_type_after(self) -> Self:
        if self.__pydantic_extra__ and "query_type" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("query_type")
        return self

    @model_validator(mode="after")
    def validate_just_one(self):
        count = len(
            [
                f
                for f in [
                    "connection_info",
                    "file",
                    "folder",
                    "group",
                    "job",
                    "kernel",
                    "module",
                    "network_interfaces",
                    "peripheral_device",
                    "process",
                    "service",
                    "session",
                    "startup_item",
                    "user",
                ]
                if getattr(self, f) is not None
            ]
        )
        if count != 1:
            raise ValueError(
                "Just one of `connection_info`, `file`, `folder`, `group`, `job`, `kernel`, `module`, `network_interfaces`, `peripheral_device`, `process`, `service`, `session`, `startup_item`, `user` must be provided, got {count}"
            )
        return self
