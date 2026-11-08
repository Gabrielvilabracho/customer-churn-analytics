"""Local verified inputs and immutable publication adapters for education analysis."""

import csv
import io
import json
from importlib.metadata import version
from pathlib import Path
from typing import Any

from churn_ml.application.ports.education_analysis import EducationAnalysisInputs
from churn_ml.infrastructure.filesystem.education_analysis_store import (
    EducationAnalysisStore,
    read_education_sources,
)


class FilesystemEducationAnalysisInputs:
    def __init__(self, root: Path) -> None:
        self.root = root

    def load(self, run_id: str) -> EducationAnalysisInputs:
        import joblib

        sources = read_education_sources(self.root, run_id)
        # Deserialize exactly the checksum-verified snapshot, never reload a path.
        model = joblib.load(io.BytesIO(sources.members[f"models/{run_id}/model.joblib"]))
        if getattr(model, "model_name", None) != sources.metadata["model_name"] or set(
            getattr(model, "feature_columns", ())
        ) != set(sources.metadata["feature_schema"]):
            raise ValueError("Serialized model and source metadata disagree")
        splits = []
        for split in ("train", "test"):
            rows = list(
                csv.DictReader(
                    io.StringIO(
                        sources.members[f"processed/{run_id}/{split}.csv"].decode("utf-8")
                    )
                )
            )
            metadata = json.loads(sources.members[f"processed/{run_id}/{split}.metadata.json"])
            if len(rows) != metadata["row_count"]:
                raise ValueError("Source split row count mismatch")
            splits.append(rows)
        return EducationAnalysisInputs(
            model=model,
            train_rows=splits[0],
            test_rows=splits[1],
            dataset_id=sources.metadata["dataset_id"],
            model_name=sources.metadata["model_name"],
            threshold=sources.metrics["threshold"]["threshold"],
            source_hashes=sources.hashes,
            model_metrics=sources.metrics["metrics"],
            versions={name: version(name) for name in ("scikit-learn", "pandas", "numpy", "scipy")},
        )

    def assert_unchanged(self, run_id: str, hashes: dict[str, str]) -> None:
        # The shared reader verifies and hashes bytes without deserializing models.
        if read_education_sources(self.root, run_id).hashes != hashes:
            raise ValueError("Analysis source changed during computation")


class FilesystemEducationAnalysisPublisher:
    def __init__(self, store: EducationAnalysisStore) -> None:
        self.store = store

    def assert_available(self, run_id: str, analysis_id: str) -> None:
        if self.store.directory(run_id, analysis_id).exists():
            raise ValueError("Analysis identity already exists; use a new analysis ID")

    def publish(self, payload: dict[str, Any]) -> None:
        self.store.publish(payload)
