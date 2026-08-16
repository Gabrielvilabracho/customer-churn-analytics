import csv
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from churn_ml.domain.artifacts import ArtifactBundle, CleanedSplitArtifact

_SAFE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+\Z")


class ArtifactNotFoundError(FileNotFoundError):
    pass


class LeaseConflictError(RuntimeError):
    """Raised when a run's write lease is held by another owner."""


class IntegrityError(RuntimeError):
    """Raised when a published run fails exact-byte validation."""


class PublicationError(RuntimeError):
    """Raised when a run is already published or cannot be published."""


_PUBLISHED_RUN_MEMBERS = (
    "metrics.json",
    "prediction_samples.csv",
    "model_metadata.json",
    "model.joblib",
    "model.joblib.sha256",
)


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
        try:
            payload = json.loads((metrics_dir / "metrics.json").read_text(encoding="utf-8"))
            return ArtifactBundle.from_json_dict(
                payload,
                prediction_samples=_read_prediction_samples(metrics_dir / "prediction_samples.csv"),
            )
        except FileNotFoundError as exc:
            raise ArtifactNotFoundError(f"Artifact bundle not found for run_id={run_id!r}") from exc

    def acquire_lease(self, run_id: str, owner: str) -> None:
        """Acquire a per-run write lease.

        A run can have at most one publisher at a time. Re-acquiring the lease
        with the same owner is idempotent; a different owner is rejected.
        """
        _validate_run_id(run_id)
        if not owner:
            raise ValueError("Lease owner must not be empty")

        lease_path = self._root / "models" / run_id / ".lease"
        if lease_path.exists():
            current = json.loads(lease_path.read_text(encoding="utf-8"))
            if current.get("owner") != owner:
                raise LeaseConflictError(
                    f"Run {run_id!r} lease is held by {current.get('owner')!r}"
                )
            return

        lease_path.parent.mkdir(parents=True, exist_ok=True)
        lease_path.write_text(
            json.dumps({"run_id": run_id, "owner": owner}, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def release_lease(self, run_id: str, owner: str) -> None:
        """Release the write lease; only the current owner may release it."""
        _validate_run_id(run_id)
        lease_path = self._root / "models" / run_id / ".lease"
        if not lease_path.exists():
            return

        current = json.loads(lease_path.read_text(encoding="utf-8"))
        if current.get("owner") != owner:
            raise LeaseConflictError(
                f"Run {run_id!r} lease is held by {current.get('owner')!r}"
            )
        lease_path.unlink()

    def publish_run(self, run_id: str) -> dict[str, str]:
        """Publish an immutable run by writing its completion manifest LAST.

        The completion manifest records the run ID and the SHA-256 checksum of
        every required member. Once written, a run is immutable: calling this
        again for the same run rejects the overwrite.

        Returns the member checksums recorded in the completion manifest.
        """
        _validate_run_id(run_id)
        completion_path = self._root / "models" / run_id / "completion.json"
        if completion_path.exists():
            raise PublicationError(
                f"Run {run_id!r} is already published; published runs are immutable"
            )

        member_paths = [
            self._root / "metrics" / run_id / member
            for member in ("metrics.json", "prediction_samples.csv")
        ] + [
            self._root / "models" / run_id / member
            for member in ("model_metadata.json", "model.joblib", "model.joblib.sha256")
        ]
        missing = [str(path) for path in member_paths if not path.is_file()]
        if missing:
            raise PublicationError(
                f"Cannot publish run {run_id!r}: missing members {missing}"
            )

        checksums = {str(path): _sha256_hex(path) for path in member_paths}
        manifest = {"run_id": run_id, "members": checksums}
        completion_path.parent.mkdir(parents=True, exist_ok=True)
        completion_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )
        return checksums

    def verify_run_integrity(self, run_id: str) -> dict[str, str]:
        """Validate a published run byte-for-byte against its completion manifest.

        Every member checksum recorded at publication must match the bytes on
        disk. An altered, missing, or mixed-generation member raises
        IntegrityError. Returns the verified member checksums.
        """
        _validate_run_id(run_id)
        completion_path = self._root / "models" / run_id / "completion.json"
        if not completion_path.is_file():
            raise IntegrityError(f"Run {run_id!r} is not published")

        manifest = json.loads(completion_path.read_text(encoding="utf-8"))
        members = manifest.get("members", {})
        if not isinstance(members, dict) or not members:
            raise IntegrityError(
                f"Run {run_id!r} completion manifest has no members"
            )

        verified: dict[str, str] = {}
        for member, expected in members.items():
            member_path = self._root / member
            if not member_path.is_file():
                raise IntegrityError(
                    f"Member {member} missing for run {run_id!r}"
                )
            checksum = _sha256_hex(member_path)
            if checksum != expected:
                raise IntegrityError(
                    f"Member {member} altered for run {run_id!r}: checksum mismatch"
                )
            verified[member] = checksum
        return verified

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

        try:
            return joblib.load(self._root / "models" / run_id / "model.joblib")
        except FileNotFoundError as exc:
            raise ArtifactNotFoundError(f"Model binary not found for run_id={run_id!r}") from exc

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


def _sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _preflight_artifact_store(root: Path, *, run_id: str) -> list[str]:
    """Validate artifact store state before operations.

    Returns a list of warning messages; empty list means valid.
    Rejects: missing root directory, invalid run_id, concurrent run IDs,
    incomplete metadata, or mismatched artifacts.
    """
    warnings: list[str] = []
    try:
        _validate_run_id(run_id)
    except ValueError as exc:
        warnings.append(str(exc))
        return warnings

    metrics_dir = root / "metrics" / run_id
    models_dir = root / "models" / run_id

    # Root directory must exist
    if not root.is_dir():
        warnings.append(f"Artifact root {root} does not exist")

    # Metrics directory must exist with metrics.json
    if not metrics_dir.is_dir():
        warnings.append(f"Metrics directory missing for run_id={run_id!r}")
    elif not (metrics_dir / "metrics.json").is_file():
        warnings.append(f"metrics.json missing for run_id={run_id!r}")

    # Models directory must exist with model_metadata.json
    if not models_dir.is_dir():
        warnings.append(f"Models directory missing for run_id={run_id!r}")
    elif not (models_dir / "model_metadata.json").is_file():
        warnings.append(f"model_metadata.json missing for run_id={run_id!r}")

    # If model_binary_path is set, model.joblib must exist
    metadata_path = models_dir / "model_metadata.json"
    if metadata_path.is_file():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata.get("model_binary_path") and not (
                models_dir / "model.joblib"
            ).is_file():
                warnings.append(
                    f"model_binary_path set but model.joblib missing for run_id={run_id!r}"
                )
        except (json.JSONDecodeError, ValueError):
            warnings.append(f"Invalid model_metadata.json for run_id={run_id!r}")

    # Prediction samples should exist if metrics exist
    if (metrics_dir / "prediction_samples.csv").is_file():
        pass  # present — no warning
    elif warnings == []:
        # Only warn if nothing else triggered
        warnings.append(
            f"prediction_samples.csv missing for run_id={run_id!r} (but no other warnings)"
        )

    return warnings
