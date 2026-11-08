"""Source-bound immutable analysis publications, without following stored paths.

Checksums establish byte integrity, not authenticity. Only analyze locally
trusted models: joblib deserialization executes Python code.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from churn_ml.domain.education import validate_analysis, validate_identity


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read(root: Path, relative: str) -> bytes:
    path = root / relative
    resolved = path.resolve()
    if resolved != path or not resolved.is_relative_to(root):
        raise ValueError("Artifact symlinks or paths outside the selected root are forbidden")
    return path.read_bytes()


@dataclass(frozen=True)
class EducationSources:
    members: dict[str, bytes]
    hashes: dict[str, str]
    metadata: dict[str, Any]
    metrics: dict[str, Any]


def read_education_sources(root: Path, run_id: str) -> EducationSources:
    validate_identity(run_id)
    root = root.resolve()
    completion_name = f"models/{run_id}/completion.json"
    try:
        completion_bytes = _read(root, completion_name)
        manifest = json.loads(completion_bytes)
        if manifest["run_id"] != run_id:
            raise ValueError("Source publication identity mismatch")
        expected_names = [
            f"{kind}/{run_id}/{name}"
            for kind, names in (
                ("metrics", ("metrics.json", "prediction_samples.csv")),
                ("models", ("model_metadata.json", "model.joblib", "model.joblib.sha256")),
            )
            for name in names
        ]
        # Historical manifests used absolute old-root paths. Compare only exact
        # allowlisted suffixes, then read the selected local root, never that path.
        recorded: dict[str, str] = {}
        for original, checksum in manifest["members"].items():
            suffix = "/".join(PurePosixPath(original).parts[-3:])
            if suffix not in expected_names or suffix in recorded:
                raise ValueError("Unexpected source publication member")
            recorded[suffix] = checksum
        if set(recorded) != set(expected_names):
            raise ValueError("Incomplete source publication")
        members = {name: _read(root, name) for name in expected_names}
        if any(_hash(data) != recorded[name] for name, data in members.items()):
            raise ValueError("Source publication checksum mismatch")
        if members[f"models/{run_id}/model.joblib.sha256"].decode().strip() != _hash(
            members[f"models/{run_id}/model.joblib"]
        ):
            raise ValueError("Model checksum sidecar mismatch")
        members[completion_name] = completion_bytes
        metadata = json.loads(members[f"models/{run_id}/model_metadata.json"])
        metrics = json.loads(members[f"metrics/{run_id}/metrics.json"])
        for key in ("run_id", "dataset_id", "model_name", "feature_schema"):
            if metadata[key] != metrics["manifest"][key]:
                raise ValueError("Mixed source model/metrics identities")
        if metadata["run_id"] != run_id:
            raise ValueError("Source run identity mismatch")
        for split in ("train", "test"):
            for name in (f"{split}.csv", f"{split}.metadata.json"):
                relative = f"processed/{run_id}/{name}"
                members[relative] = _read(root, relative)
            split_meta = json.loads(members[f"processed/{run_id}/{split}.metadata.json"])
            if (
                split_meta["run_id"] != run_id
                or split_meta["split_name"] != split
                or split_meta["dataset_id"] != metadata["dataset_id"]
                or split_meta["target_column"] != "Burnout_Risk_Level"
                or set(split_meta["feature_columns"]) != set(metadata["feature_schema"])
            ):
                raise ValueError("Source split schema or identity mismatch")
        return EducationSources(
            members, {k: _hash(v) for k, v in members.items()}, metadata, metrics
        )
    except (OSError, KeyError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Source education publication is missing or malformed") from exc


class EducationAnalysisStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def directory(self, run_id: str, analysis_id: str) -> Path:
        validate_identity(run_id)
        validate_identity(analysis_id)
        path = self.root / "education" / run_id / analysis_id
        if path.resolve() != path:
            raise ValueError("Analysis publication symlinks are forbidden")
        return path

    def publish(self, payload: dict[str, Any]) -> None:
        payload = validate_analysis(payload)
        directory = self.directory(payload["run_id"], payload["analysis_id"])
        try:
            # Exclusive directory reservation: concurrent/duplicate publishers
            # cannot overwrite a partial or completed publication.
            directory.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            raise ValueError("Analysis identity already exists; use a new analysis ID") from exc
        data = json.dumps(payload, sort_keys=True, indent=2, allow_nan=False).encode()
        (directory / "analysis.json").write_bytes(data)
        with (directory / "completion.json").open("x", encoding="utf-8") as stream:
            json.dump(
                {
                    "schema_version": 1,
                    "run_id": payload["run_id"],
                    "analysis_id": payload["analysis_id"],
                    "payload_sha256": _hash(data),
                },
                stream,
            )

    def read(self, run_id: str, analysis_id: str) -> dict[str, Any]:
        directory = self.directory(run_id, analysis_id)
        relative = directory.relative_to(self.root).as_posix()
        try:
            completion = json.loads(_read(self.root, f"{relative}/completion.json"))
            data = _read(self.root, f"{relative}/analysis.json")
            if (
                completion["run_id"] != run_id
                or completion["analysis_id"] != analysis_id
                or completion["schema_version"] != 1
                or completion["payload_sha256"] != _hash(data)
            ):
                raise ValueError("Analysis publication checksum or identity mismatch")
            payload = validate_analysis(json.loads(data))
            if payload["run_id"] != run_id or payload["analysis_id"] != analysis_id:
                raise ValueError("Analysis payload identity mismatch")
            sources = read_education_sources(self.root, run_id)
            if payload["source_hashes"] != sources.hashes:
                raise ValueError("Analysis source binding is stale or altered")
            for key in ("dataset_id", "model_name"):
                if payload.get(key) != sources.metadata[key]:
                    raise ValueError("Analysis model/dataset identity does not match its source")
            return payload
        except (OSError, KeyError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("Education analysis is missing, unpublished or malformed") from exc
