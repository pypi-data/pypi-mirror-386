from typing import ClassVar

from ocsf.objects.data_classification import DataClassification as DataClassification_
from ocsf.profiles.base_profile import BaseProfile


class DataClassification(BaseProfile):
    schema_name: ClassVar[str] = "data_classification"

    # Recommended
    data_classification: DataClassification_ | None = None
    data_classifications: list[DataClassification_] | None = None
