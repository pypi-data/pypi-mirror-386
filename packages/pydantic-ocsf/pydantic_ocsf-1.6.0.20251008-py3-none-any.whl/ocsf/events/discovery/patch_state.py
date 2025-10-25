from typing import ClassVar

from pydantic import model_validator

from ocsf.events.discovery.discovery import Discovery
from ocsf.objects.device import Device
from ocsf.objects.kb_article import KbArticle


class PatchState(Discovery):
    allowed_profiles: ClassVar[list[str]] = ["cloud", "datetime", "host", "osint", "security_control"]
    class_name: str = "Operating System Patch State"
    class_uid: int = 5004
    schema_name: ClassVar[str] = "patch_state"

    # Required
    device: Device

    # Recommended
    kb_article_list: list[KbArticle] | None = None

    @model_validator(mode="after")
    def validate_at_least_one(self):
        if all(
            getattr(self, field) is None for field in ["device.os.sp_name", "device.os.sp_ver", "device.os.version"]
        ):
            raise ValueError(
                "At least one of `device.os.sp_name`, `device.os.sp_ver`, `device.os.version` must be provided"
            )
        return self
