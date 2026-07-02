import csv
import json
from pathlib import Path

from churn_ml.domain.artifacts import ArtifactBundle, CleanedSplitArtifact


class FilesystemArtifactStore:
    def __init__(self, *, root: Path) -> None:
        self._root = root

    def save_bundle(self, bundle: ArtifactBundle) -> None:
        metrics_dir = self._root / "metrics" / bundle.manifest.run_id
        models_dir = self._root / "models" / bundle.manifest.run_id
        metrics_dir.mkdir(parents=True, exist_ok=True)
        models_dir.mkdir(parents=True, exist_ok=True)

        (metrics_dir / "metrics.json").write_text(
            json.dumps(bundle.to_json_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        _write_prediction_samples(metrics_dir / "prediction_samples.csv", bundle)
        (models_dir / "model_metadata.json").write_text(
            json.dumps(bundle.to_json_dict()["manifest"], indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def load_bundle(self, run_id: str) -> ArtifactBundle:
        metrics_dir = self._root / "metrics" / run_id
        payload = json.loads((metrics_dir / "metrics.json").read_text(encoding="utf-8"))
        return ArtifactBundle.from_json_dict(
            payload,
            prediction_samples=_read_prediction_samples(metrics_dir / "prediction_samples.csv"),
        )

    def save_cleaned_split(self, split: CleanedSplitArtifact) -> None:
        processed_dir = self._root / "processed" / split.run_id
        processed_dir.mkdir(parents=True, exist_ok=True)
        (processed_dir / f"{split.split_name}.metadata.json").write_text(
            json.dumps(split.metadata_json_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        _write_rows_csv(processed_dir / f"{split.split_name}.csv", split.rows)

    def load_cleaned_split(self, run_id: str, split_name: str) -> CleanedSplitArtifact:
        processed_dir = self._root / "processed" / run_id
        payload = json.loads(
            (processed_dir / f"{split_name}.metadata.json").read_text(encoding="utf-8")
        )
        return CleanedSplitArtifact.from_metadata_json_dict(
            payload,
            rows=_read_rows_csv(processed_dir / f"{split_name}.csv"),
        )


def _write_prediction_samples(path: Path, bundle: ArtifactBundle) -> None:
    _write_rows_csv(path, bundle.prediction_samples)


def _write_rows_csv(path: Path, rows: tuple[dict[str, str], ...]) -> None:
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as raw_file:
        writer = csv.DictWriter(raw_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_prediction_samples(path: Path) -> tuple[dict[str, str], ...]:
    return _read_rows_csv(path)


def _read_rows_csv(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as raw_file:
        return tuple(dict(row) for row in csv.DictReader(raw_file))
