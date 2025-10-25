import re
from enum import IntEnum, StrEnum, property as enum_property
from typing import Any, ClassVar, Self

from pydantic import AnyUrl, IPvAnyNetwork, computed_field, model_validator

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.analytic import Analytic
from ocsf.objects.attack import Attack
from ocsf.objects.autonomous_system import AutonomousSystem
from ocsf.objects.campaign import Campaign
from ocsf.objects.digital_signature import DigitalSignature
from ocsf.objects.dns_answer import DnsAnswer
from ocsf.objects.email import Email
from ocsf.objects.email_auth import EmailAuth
from ocsf.objects.file import File
from ocsf.objects.kill_chain_phase import KillChainPhase
from ocsf.objects.location import Location
from ocsf.objects.malware import Malware
from ocsf.objects.object import Object
from ocsf.objects.reputation import Reputation
from ocsf.objects.script import Script
from ocsf.objects.threat_actor import ThreatActor
from ocsf.objects.user import User
from ocsf.objects.vulnerability import Vulnerability
from ocsf.objects.whois import Whois


class ConfidenceId(IntEnum):
    UNKNOWN = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return ConfidenceId[obj]
        else:
            return ConfidenceId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "LOW": "Low",
            "MEDIUM": "Medium",
            "HIGH": "High",
            "OTHER": "Other",
        }
        return name_map[super().name]


class DetectionPatternTypeId(IntEnum):
    UNKNOWN = 0
    STIX = 1
    PCRE = 2
    SIGMA = 3
    SNORT = 4
    SURICATA = 5
    YARA = 6
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return DetectionPatternTypeId[obj]
        else:
            return DetectionPatternTypeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "STIX": "STIX",
            "PCRE": "PCRE",
            "SIGMA": "SIGMA",
            "SNORT": "Snort",
            "SURICATA": "Suricata",
            "YARA": "YARA",
            "OTHER": "Other",
        }
        return name_map[super().name]


class SeverityId(IntEnum):
    UNKNOWN = 0
    INFORMATIONAL = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5
    FATAL = 6
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return SeverityId[obj]
        else:
            return SeverityId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "INFORMATIONAL": "Informational",
            "LOW": "Low",
            "MEDIUM": "Medium",
            "HIGH": "High",
            "CRITICAL": "Critical",
            "FATAL": "Fatal",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Tlp(StrEnum):
    TLP_AMBER = "AMBER"
    TLP_AMBER_STRICT = "AMBER STRICT"
    TLP_CLEAR = "CLEAR"
    TLP_GREEN = "GREEN"
    TLP_RED = "RED"
    TLP_WHITE = "WHITE"

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return Tlp[obj]
        else:
            return Tlp(obj)

    @enum_property
    def name(self):
        name_map = {
            "TLP_AMBER": "TLP:AMBER",
            "TLP_AMBER_STRICT": "TLP:AMBER+STRICT",
            "TLP_CLEAR": "TLP:CLEAR",
            "TLP_GREEN": "TLP:GREEN",
            "TLP_RED": "TLP:RED",
            "TLP_WHITE": "TLP:WHITE",
        }
        return name_map[super().name]


class TypeId(IntEnum):
    UNKNOWN = 0
    IP_ADDRESS = 1
    DOMAIN = 2
    HOSTNAME = 3
    HASH = 4
    URL = 5
    USER_AGENT = 6
    DIGITAL_CERTIFICATE = 7
    EMAIL = 8
    EMAIL_ADDRESS = 9
    VULNERABILITY = 10
    FILE = 11
    REGISTRY_KEY = 12
    REGISTRY_VALUE = 13
    COMMAND_LINE = 14
    OTHER = 99

    @classmethod
    def validate_python(cls, obj: Any):
        try:
            obj = int(obj)
        except ValueError:
            obj = str(obj).upper()
            return TypeId[obj]
        else:
            return TypeId(obj)

    @enum_property
    def name(self):
        name_map = {
            "UNKNOWN": "Unknown",
            "IP_ADDRESS": "IP Address",
            "DOMAIN": "Domain",
            "HOSTNAME": "Hostname",
            "HASH": "Hash",
            "URL": "URL",
            "USER_AGENT": "User Agent",
            "DIGITAL_CERTIFICATE": "Digital Certificate",
            "EMAIL": "Email",
            "EMAIL_ADDRESS": "Email Address",
            "VULNERABILITY": "Vulnerability",
            "FILE": "File",
            "REGISTRY_KEY": "Registry Key",
            "REGISTRY_VALUE": "Registry Value",
            "COMMAND_LINE": "Command Line",
            "OTHER": "Other",
        }
        return name_map[super().name]


class Osint(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "osint"

    # Required
    type_id: TypeId
    value: str

    # Recommended
    confidence_id: ConfidenceId | None = None
    tlp: Tlp | None = None

    # Optional
    answers: list[DnsAnswer] | None = None
    attacks: list[Attack] | None = None
    autonomous_system: AutonomousSystem | None = None
    campaign: Campaign | None = None
    category: str | None = None
    comment: str | None = None
    created_time: Timestamp | None = None
    creator: User | None = None
    desc: str | None = None
    detection_pattern: str | None = None
    detection_pattern_type_id: DetectionPatternTypeId | None = None
    email: Email | None = None
    email_auth: EmailAuth | None = None
    expiration_time: Timestamp | None = None
    external_uid: str | None = None
    file: File | None = None
    intrusion_sets: list[str] | None = None
    kill_chain: list[KillChainPhase] | None = None
    labels: list[str] | None = None
    location: Location | None = None
    malware: list[Malware] | None = None
    modified_time: Timestamp | None = None
    name: str | None = None
    references: list[str] | None = None
    related_analytics: list[Analytic] | None = None
    reputation: Reputation | None = None
    risk_score: int | None = None
    script: Script | None = None
    severity_id: SeverityId | None = None
    signatures: list[DigitalSignature] | None = None
    src_url: AnyUrl | None = None
    subdomains: list[str] | None = None
    subnet: IPvAnyNetwork | None = None
    threat_actor: ThreatActor | None = None
    uid: str | None = None
    uploaded_time: Timestamp | None = None
    vendor_name: str | None = None
    vulnerabilities: list[Vulnerability] | None = None
    whois: Whois | None = None

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def confidence(self) -> str | None:
        if self.confidence_id is None:
            return None
        return self.confidence_id.name

    @confidence.setter
    def confidence(self, value: str | None) -> None:
        if value is None:
            self.confidence_id = None
        else:
            self.confidence_id = ConfidenceId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_confidence_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "confidence" in data and "confidence_id" not in data:
            confidence = re.sub(r"\W", "_", data.pop("confidence").upper())
            data["confidence_id"] = ConfidenceId[confidence]
        return data

    @model_validator(mode="after")
    def validate_confidence_after(self) -> Self:
        if self.__pydantic_extra__ and "confidence" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("confidence")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def detection_pattern_type(self) -> str | None:
        if self.detection_pattern_type_id is None:
            return None
        return self.detection_pattern_type_id.name

    @detection_pattern_type.setter
    def detection_pattern_type(self, value: str | None) -> None:
        if value is None:
            self.detection_pattern_type_id = None
        else:
            self.detection_pattern_type_id = DetectionPatternTypeId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_detection_pattern_type_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "detection_pattern_type" in data and "detection_pattern_type_id" not in data:
            detection_pattern_type = re.sub(r"\W", "_", data.pop("detection_pattern_type").upper())
            data["detection_pattern_type_id"] = DetectionPatternTypeId[detection_pattern_type]
        return data

    @model_validator(mode="after")
    def validate_detection_pattern_type_after(self) -> Self:
        if self.__pydantic_extra__ and "detection_pattern_type" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("detection_pattern_type")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def severity(self) -> str | None:
        if self.severity_id is None:
            return None
        return self.severity_id.name

    @severity.setter
    def severity(self, value: str | None) -> None:
        if value is None:
            self.severity_id = None
        else:
            self.severity_id = SeverityId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_severity_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "severity" in data and "severity_id" not in data:
            severity = re.sub(r"\W", "_", data.pop("severity").upper())
            data["severity_id"] = SeverityId[severity]
        return data

    @model_validator(mode="after")
    def validate_severity_after(self) -> Self:
        if self.__pydantic_extra__ and "severity" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("severity")
        return self

    @computed_field  # type: ignore[misc,prop-decorator]
    @property
    def type(self) -> str:
        return self.type_id.name

    @type.setter
    def type(self, value: str) -> None:
        self.type_id = TypeId[value]

    @model_validator(mode="before")
    @classmethod
    def validate_type_before(cls, data: dict[str, Any]) -> dict[str, Any]:
        if "type" in data and "type_id" not in data:
            type = re.sub(r"\W", "_", data.pop("type").upper())
            data["type_id"] = TypeId[type]
        return data

    @model_validator(mode="after")
    def validate_type_after(self) -> Self:
        if self.__pydantic_extra__ and "type" in self.__pydantic_extra__:
            self.__pydantic_extra__.pop("type")
        return self
