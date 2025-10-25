from typing import ClassVar

from ocsf.objects.object import Object


class ClassifierDetails(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "classifier_details"

    # Required
    type_: str

    # Recommended
    name: str | None = None
    uid: str | None = None
