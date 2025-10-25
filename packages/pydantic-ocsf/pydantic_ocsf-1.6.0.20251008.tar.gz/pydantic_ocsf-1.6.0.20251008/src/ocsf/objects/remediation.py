from typing import ClassVar

from ocsf.objects.cis_control import CisControl
from ocsf.objects.kb_article import KbArticle
from ocsf.objects.object import Object


class Remediation(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "remediation"

    # Required
    desc: str

    # Optional
    cis_controls: list[CisControl] | None = None
    kb_article_list: list[KbArticle] | None = None
    kb_articles: list[str] | None = None
    references: list[str] | None = None
