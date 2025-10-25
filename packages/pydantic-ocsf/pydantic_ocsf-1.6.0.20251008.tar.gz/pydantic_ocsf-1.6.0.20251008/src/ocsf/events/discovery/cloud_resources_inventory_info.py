from typing import ClassVar

from pydantic import model_validator

from ocsf.events.discovery.discovery import Discovery
from ocsf.objects.cloud import Cloud
from ocsf.objects.container import Container
from ocsf.objects.database import Database
from ocsf.objects.databucket import Databucket
from ocsf.objects.idp import Idp
from ocsf.objects.resource_details import ResourceDetails
from ocsf.objects.table import Table


class CloudResourcesInventoryInfo(Discovery):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Cloud Resources Inventory Info"
    class_uid: int = 5023
    schema_name: ClassVar[str] = "cloud_resources_inventory_info"

    # Recommended
    cloud: Cloud | None = None
    container: Container | None = None
    database: Database | None = None
    databucket: Databucket | None = None
    idp: Idp | None = None
    region: str | None = None
    resources: list[ResourceDetails] | None = None
    table: Table | None = None

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(
            getattr(self, field) is None
            for field in ["cloud", "container", "database", "databucket", "idp", "resources", "table"]
        ):
            raise ValueError(
                "At least one of `cloud`, `container`, `database`, `databucket`, `idp`, `resources`, `table` must be provided"
            )
        return self
