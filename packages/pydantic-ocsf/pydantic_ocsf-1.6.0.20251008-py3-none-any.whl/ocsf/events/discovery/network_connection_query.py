import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.events.discovery.discovery_result import DiscoveryResult
from ocsf.objects.network_connection_info import NetworkConnectionInfo
from ocsf.objects.process import Process


class StateId(IntEnum):
    UNKNOWN = 0
    ESTABLISHED = 1
    SYN_SENT = 2
    SYN_RECV = 3
    FIN_WAIT1 = 4
    FIN_WAIT2 = 5
    TIME_WAIT = 6
    CLOSED = 7
    CLOSE_WAIT = 8
    LAST_ACK = 9
    LISTEN = 10
    CLOSING = 11
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return StateId[obj]
        else:
            return StateId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "ESTABLISHED": "ESTABLISHED",
            "SYN_SENT": "SYN_SENT",
            "SYN_RECV": "SYN_RECV",
            "FIN_WAIT1": "FIN_WAIT1",
            "FIN_WAIT2": "FIN_WAIT2",
            "TIME_WAIT": "TIME_WAIT",
            "CLOSED": "CLOSED",
            "CLOSE_WAIT": "CLOSE_WAIT",
            "LAST_ACK": "LAST_ACK",
            "LISTEN": "LISTEN",
            "CLOSING": "CLOSING",
            "OTHER": "Other",
        }
        return name_map[super().name]


class NetworkConnectionQuery(DiscoveryResult):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Network Connection Query"
    class_uid: int = 5012
    schema_name: ClassVar[str] = "network_connection_query"

    # Required
    connection_info: NetworkConnectionInfo
    process: Process
    state_id: StateId

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def state(self) -> str:
        return self.state_id.name

    @state.setter
    def state(self, value: str) -> None:
        self.state_id = StateId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_state_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "state" in data and "state_id" not in data:
            state = re.sub(r"\W", "_", data.pop("state").upper())
            data["state_id"] = StateId[state]
        return data

    @model_validator(mode="after")
    def validate_state_after(self) -> Self:
        if self.__pydantic_extra__ and "state" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("state")
        return self
