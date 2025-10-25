from typing import ClassVar

from ocsf.objects.analysis_target import AnalysisTarget
from ocsf.objects.anomaly import Anomaly
from ocsf.objects.baseline import Baseline
from ocsf.ocsf_object import OcsfObject


class AnomalyAnalysis(OcsfObject):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "anomaly_analysis"

    # Required
    analysis_targets: list[AnalysisTarget]
    anomalies: list[Anomaly]

    # Recommended
    baselines: list[Baseline] | None = None
