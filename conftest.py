"""Shared synthetic education publication for cross-package integration tests."""

from pathlib import Path
from typing import Any

import pytest
from churn_ml.domain.artifacts import (
    ArtifactBundle,
    ArtifactManifest,
    ClassificationMetricSet,
    CleanedSplitArtifact,
    ThresholdSelection,
)
from churn_ml.infrastructure.filesystem.artifact_store import FilesystemArtifactStore
from churn_ml.infrastructure.sklearn.candidate import SklearnLogisticRegressionTrainer


@pytest.fixture
def education_source(tmp_path: Path) -> Path:
    def rows(start: int) -> list[dict[str, Any]]:
        return [
            {
                "Student_ID": str(start + i),
                "Weekly_GenAI_Hours": str(i % 20),
                "Major_Category": "Arts" if i % 2 else "Engineering",
                "Burnout_Risk_Level": "High" if i % 20 >= 10 else "Low",
            }
            for i in range(80)
        ]

    features = ("Weekly_GenAI_Hours", "Major_Category")
    model = SklearnLogisticRegressionTrainer("education-test", features).train(
        rows(0),
        target_column="Burnout_Risk_Level",
    )
    store = FilesystemArtifactStore(root=tmp_path)
    store.save_bundle(
        ArtifactBundle(
            ArtifactManifest(
                "education-test",
                "synthetic-education",
                "education-test",
                "2026-11-07Z",
                {"Weekly_GenAI_Hours": "number", "Major_Category": "string"},
            ),
            ClassificationMetricSet(0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.5),
            ThresholdSelection(0.3, "Synthetic test threshold"),
            (),
        )
    )
    for name, start in (("train", 0), ("test", 1000)):
        store.save_cleaned_split(
            CleanedSplitArtifact(
                "education-test",
                "synthetic-education",
                name,
                features,
                "Burnout_Risk_Level",
                tuple(rows(start)),
            )
        )
    store.save_model_binary(model, run_id="education-test")
    store.publish_run("education-test")
    return tmp_path
