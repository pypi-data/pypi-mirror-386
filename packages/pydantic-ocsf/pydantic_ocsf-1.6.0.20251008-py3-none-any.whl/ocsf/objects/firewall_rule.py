from typing import ClassVar

from ocsf.objects.rule import Rule


class FirewallRule(Rule):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "firewall_rule"

    # Optional
    condition: str | None = None
    duration: int | None = None
    match_details: list[str] | None = None
    match_location: str | None = None
    rate_limit: int | None = None
    sensitivity: str | None = None
