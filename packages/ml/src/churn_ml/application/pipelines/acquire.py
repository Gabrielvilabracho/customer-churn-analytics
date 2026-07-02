from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from churn_ml.application.ports.dataset_source import (
    DatasetSourceMetadata,
    validate_source_metadata,
)


@dataclass(frozen=True)
class AcquisitionManifest:
    metadata: DatasetSourceMetadata
    raw_file_path: Path
    sha256: str
    acquired_at_utc: str


def create_acquisition_manifest(
    *, metadata: DatasetSourceMetadata, raw_file_path: Path
) -> AcquisitionManifest:
    validated = validate_source_metadata(metadata)
    if not raw_file_path.is_file():
        raise FileNotFoundError(f"Raw dataset file not found: {raw_file_path}")

    return AcquisitionManifest(
        metadata=validated,
        raw_file_path=raw_file_path,
        sha256=_sha256(raw_file_path),
        acquired_at_utc=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    )


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as raw_file:
        for chunk in iter(lambda: raw_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
