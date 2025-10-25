import re
from enum import IntEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import computed_field, model_validator

from ocsf.objects._entity import Entity
from ocsf.objects.actor import Actor
from ocsf.objects.api import API
from ocsf.objects.container import Container
from ocsf.objects.database import Database
from ocsf.objects.databucket import Databucket
from ocsf.objects.device import Device
from ocsf.objects.dns_query import DnsQuery
from ocsf.objects.email import Email
from ocsf.objects.file import File
from ocsf.objects.http_request import HttpRequest
from ocsf.objects.http_response import HttpResponse
from ocsf.objects.ja4_fingerprint import Ja4Fingerprint
from ocsf.objects.job import Job
from ocsf.objects.network_connection_info import NetworkConnectionInfo
from ocsf.objects.network_endpoint import NetworkEndpoint
from ocsf.objects.process import Process
from ocsf.objects.resource_details import ResourceDetails
from ocsf.objects.script import Script
from ocsf.objects.tls import TLS
from ocsf.objects.url import Url
from ocsf.objects.user import User


class VerdictId(IntEnum):
    UNKNOWN = 0
    FALSE_POSITIVE = 1
    TRUE_POSITIVE = 2
    DISREGARD = 3
    SUSPICIOUS = 4
    BENIGN = 5
    TEST = 6
    INSUFFICIENT_DATA = 7
    SECURITY_RISK = 8
    MANAGED_EXTERNALLY = 9
    DUPLICATE = 10
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return VerdictId[obj]
        else:
            return VerdictId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "FALSE_POSITIVE": "False Positive",
            "TRUE_POSITIVE": "True Positive",
            "DISREGARD": "Disregard",
            "SUSPICIOUS": "Suspicious",
            "BENIGN": "Benign",
            "TEST": "Test",
            "INSUFFICIENT_DATA": "Insufficient Data",
            "SECURITY_RISK": "Security Risk",
            "MANAGED_EXTERNALLY": "Managed Externally",
            "DUPLICATE": "Duplicate",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Evidences(Entity):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "evidences"

    # Recommended
    actor: Actor | None = None
    api: API | None = None
    connection_info: NetworkConnectionInfo | None = None
    container: Container | None = None
    database: Database | None = None
    databucket: Databucket | None = None
    device: Device | None = None
    dst_endpoint: NetworkEndpoint | None = None
    email: Email | None = None
    file: File | None = None
    http_request: HttpRequest | None = None
    http_response: HttpResponse | None = None
    ja4_fingerprint_list: list[Ja4Fingerprint] | None = None
    job: Job | None = None
    process: Process | None = None
    query: DnsQuery | None = None
    resources: list[ResourceDetails] | None = None
    script: Script | None = None
    src_endpoint: NetworkEndpoint | None = None
    tls: TLS | None = None
    url: Url | None = None
    user: User | None = None

    # Optional
    data: dict[str, Any] | None = None
    name: str | None = None
    uid: str | None = None
    verdict_id: VerdictId | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def verdict(self) -> str | None:
        if self.verdict_id is None:
            return None
        return self.verdict_id.name

    @verdict.setter
    def verdict(self, value: str | None) -> None:
        if value is None:
            self.verdict_id = None
        else:
            self.verdict_id = VerdictId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_verdict_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "verdict" in data and "verdict_id" not in data:
            verdict = re.sub(r"\W", "_", data.pop("verdict").upper())
            data["verdict_id"] = VerdictId[verdict]
        return data

    @model_validator(mode="after")
    def validate_verdict_after(self) -> Self:
        if self.__pydantic_extra__ and "verdict" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("verdict")
        return self

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(
            getattr(self, field) is None
            for field in [
                "actor",
                "api",
                "connection_info",
                "data",
                "database",
                "databucket",
                "device",
                "dst_endpoint",
                "email",
                "file",
                "process",
                "query",
                "resources",
                "src_endpoint",
                "url",
                "user",
                "job",
                "script",
            ]
        ):
            raise ValueError(
                "At least one of `actor`, `api`, `connection_info`, `data`, `database`, `databucket`, `device`, `dst_endpoint`, `email`, `file`, `process`, `query`, `resources`, `src_endpoint`, `url`, `user`, `job`, `script` must be provided"
            )
        return self
