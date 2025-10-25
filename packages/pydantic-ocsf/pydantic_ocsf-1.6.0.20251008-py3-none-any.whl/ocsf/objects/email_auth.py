from typing import ClassVar

from ocsf.objects.object import Object


class EmailAuth(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "email_auth"

    # Recommended
    dkim: str | None = None
    dkim_domain: str | None = None
    dkim_signature: str | None = None
    dmarc: str | None = None
    dmarc_override: str | None = None
    dmarc_policy: str | None = None
    spf: str | None = None
