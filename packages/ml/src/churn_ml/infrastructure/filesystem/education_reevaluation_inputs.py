"""Verified local inputs for explicitly trusted historical reevaluation."""

import csv
from io import BytesIO, StringIO
from pathlib import Path

from churn_ml.application.ports.education_reevaluation import EducationReevaluationInputs
from churn_ml.infrastructure.filesystem.education_analysis_store import read_education_sources
from churn_ml.infrastructure.sklearn.candidate import SklearnProbabilityModel


class FilesystemEducationReevaluationInputs:
    def __init__(self, root: Path) -> None:
        self.root = root

    def load(self, run_id: str) -> EducationReevaluationInputs:
        import joblib

        sources = read_education_sources(self.root, run_id)
        model = joblib.load(BytesIO(sources.members[f"models/{run_id}/model.joblib"]))
        if (
            not isinstance(model, SklearnProbabilityModel)
            or not hasattr(model.estimator, "named_steps")
            or model.model_name != sources.metadata["model_name"]
            or set(model.feature_columns) != set(sources.metadata["feature_schema"])
        ):
            raise ValueError("Verified source is not the declared sklearn model")
        rows = list(
            csv.DictReader(
                StringIO(sources.members[f"processed/{run_id}/test.csv"].decode("utf-8"))
            )
        )
        return EducationReevaluationInputs(
            model=model,
            test_rows=rows,
            threshold=sources.metrics["threshold"]["threshold"],
            source_hashes=sources.hashes,
            historical_metrics=sources.metrics["metrics"],
        )

    def assert_unchanged(self, run_id: str, hashes: dict[str, str]) -> None:
        if read_education_sources(self.root, run_id).hashes != hashes:
            raise ValueError("Source artifacts changed during reevaluation")
