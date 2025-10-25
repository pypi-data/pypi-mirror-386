from typing import ClassVar

from pydantic import AnyUrl

from ocsf.datatypes.timestamp import Timestamp
from ocsf.objects.cvss import Cvss
from ocsf.objects.cwe import Cwe
from ocsf.objects.epss import Epss
from ocsf.objects.object import Object
from ocsf.objects.product import Product


class Cve(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "cve"

    # Required
    uid: str

    # Recommended
    created_time: Timestamp | None = None
    cvss: list[Cvss] | None = None
    references: list[str] | None = None
    title: str | None = None
    type_: str | None = None

    # Optional
    cwe: Cwe | None = None
    cwe_uid: str | None = None
    cwe_url: AnyUrl | None = None
    desc: str | None = None
    epss: Epss | None = None
    modified_time: Timestamp | None = None
    product: Product | None = None
    related_cwes: list[Cwe] | None = None
