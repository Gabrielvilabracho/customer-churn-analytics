import csv
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from churn_ml.domain.artifacts import ArtifactBundle, CleanedSplitArtifact

_SAFE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+\Z")


def _validate_run_id(run_id: str) -> None:
    if not run_id or not _SAFE_NAME_PATTERN.match(run_id):
        raise ValueError(
            f"Invalid run_id {run_id!r}: must match [A-Za-z0-9_-]+ "
            "with no path separators or empty string."
        )


def _validate_split_name(split_name: str) -> None:
    if not split_name or not _SAFE_NAME_PATTERN.match(split_name):
        raise ValueError(
            f"Invalid split_name {split_name!r}: must match [A-Za-z0-9_-]+ "
            "with no path separators or empty string."
        )


def _read_metadata_or_empty(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


class FilesystemArtifactStore:
    def __init__(self, *, root: Path) -> None:
        self._root = root

    def save_bundle(self, bundle: ArtifactBundle) -> None:
        _validate_run_id(bundle.manifest.run_id)
        metrics_dir = self._root / "metrics" / bundle.manifest.run_id
        models_dir = self._root / "models" / bundle.manifest.run_id
        metrics_dir.mkdir(parents=True, exist_ok=True)
        models_dir.mkdir(parents=True, exist_ok=True)

        (metrics_dir / "metrics.json").write_text(
            json.dumps(bundle.to_json_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        _write_prediction_samples(metrics_dir / "prediction_samples.csv", bundle)

        # Read-merge-write so that an existing model_binary_path is not erased.
        metadata_path = models_dir / "model_metadata.json"
        existing = _read_metadata_or_empty(metadata_path)
        # Preserve model_binary_path if the binary file exists but metadata lost it
        # (e.g. due to corruption between save_model_binary and save_bundle).
        if "model_binary_path" not in existing:
            candidate_binary = models_dir / "model.joblib"
            if candidate_binary.exists():
                existing["model_binary_path"] = "model.joblib"
        merged = {**existing, **bundle.to_json_dict()["manifest"]}
        metadata_path.write_text(
            json.dumps(merged, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def load_bundle(self, run_id: str) -> ArtifactBundle:
        _validate_run_id(run_id)
        metrics_dir = self._root / "metrics" / run_id
        payload = json.loads((metrics_dir / "metrics.json").read_text(encoding="utf-8"))
        return ArtifactBundle.from_json_dict(
            payload,
            prediction_samples=_read_prediction_samples(metrics_dir / "prediction_samples.csv"),
        )

    def save_cleaned_split(self, split: CleanedSplitArtifact) -> None:
        _validate_run_id(split.run_id)
        _validate_split_name(split.split_name)
        processed_dir = self._root / "processed" / split.run_id
        processed_dir.mkdir(parents=True, exist_ok=True)
        (processed_dir / f"{split.split_name}.metadata.json").write_text(
            json.dumps(split.metadata_json_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        _write_rows_csv(processed_dir / f"{split.split_name}.csv", split.rows)

    def save_model_binary(self, model: Any, *, run_id: str) -> None:
        _validate_run_id(run_id)
        import joblib

        models_dir = self._root / "models" / run_id
        models_dir.mkdir(parents=True, exist_ok=True)

        final_path = models_dir / "model.joblib"
        tmp_path = models_dir / "model.joblib.tmp"
        joblib.dump(model, tmp_path)
        os.replace(tmp_path, final_path)

        checksum = hashlib.sha256(final_path.read_bytes()).hexdigest()
        (models_dir / "model.joblib.sha256").write_text(checksum, encoding="utf-8")

        metadata_path = models_dir / "model_metadata.json"
        metadata = _read_metadata_or_empty(metadata_path)
        metadata["model_binary_path"] = "model.joblib"
        metadata_path.write_text(
            json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8"
        )

    def load_model_binary(self, run_id: str) -> Any:
        _validate_run_id(run_id)
        import joblib  # transitive dep of scikit-learn; type already resolved by save_model_binary

        return joblib.load(self._root / "models" / run_id / "model.joblib")

    def delete_processed_run(self, run_id: str) -> None:
        import shutil

        _validate_run_id(run_id)
        processed_run_dir = self._root / "processed" / run_id
        if processed_run_dir.exists():
            shutil.rmtree(processed_run_dir)

    def load_cleaned_split(self, run_id: str, split_name: str) -> CleanedSplitArtifact:
        _validate_run_id(run_id)
        _validate_split_name(split_name)
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
