from dataclasses import asdict, dataclass
from typing import Any, Self


@dataclass(frozen=True)
class ClassificationMetricSet:
    pr_auc: float
    roc_auc: float
    precision: float
    recall: float
    accuracy: float
    top_risk_capture: float
    workload_at_threshold: float


@dataclass(frozen=True)
class ThresholdSelection:
    threshold: float
    tradeoff: str


@dataclass(frozen=True)
class ArtifactManifest:
    run_id: str
    dataset_id: str
    model_name: str
    created_at_utc: str


@dataclass(frozen=True)
class ArtifactBundle:
    manifest: ArtifactManifest
    metrics: ClassificationMetricSet
    threshold: ThresholdSelection
    prediction_samples: tuple[dict[str, str], ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "manifest": asdict(self.manifest),
            "metrics": asdict(self.metrics),
            "threshold": asdict(self.threshold),
        }

    @classmethod
    def from_json_dict(
        cls,
        payload: dict[str, Any],
        *,
        prediction_samples: tuple[dict[str, str], ...],
    ) -> Self:
        return cls(
            manifest=ArtifactManifest(**payload["manifest"]),
            metrics=ClassificationMetricSet(**payload["metrics"]),
            threshold=ThresholdSelection(**payload["threshold"]),
            prediction_samples=prediction_samples,
        )


@dataclass(frozen=True)
class CleanedSplitArtifact:
    run_id: str
    dataset_id: str
    split_name: str
    feature_columns: tuple[str, ...]
    target_column: str
    rows: tuple[dict[str, str], ...]

    def metadata_json_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "dataset_id": self.dataset_id,
            "split_name": self.split_name,
            "feature_columns": list(self.feature_columns),
            "target_column": self.target_column,
            "row_count": len(self.rows),
        }

    @classmethod
    def from_metadata_json_dict(
        cls,
        payload: dict[str, Any],
        *,
        rows: tuple[dict[str, str], ...],
    ) -> Self:
        return cls(
            run_id=payload["run_id"],
            dataset_id=payload["dataset_id"],
            split_name=payload["split_name"],
            feature_columns=tuple(payload["feature_columns"]),
            target_column=payload["target_column"],
            rows=rows,
        )
