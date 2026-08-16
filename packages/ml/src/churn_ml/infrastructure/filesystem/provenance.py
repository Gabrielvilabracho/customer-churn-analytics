"""Local-only dataset provenance validation.

The education CSV has no verified public license and must remain local.
This module validates the ignored ``source-metadata.json`` record before any
training run touches the data, rejecting contradictory metadata.
"""

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

LICENSE_STATUSES = frozenset({"verified", "unverified"})
REDISTRIBUTION_DECISIONS = frozenset({"prohibited", "permitted"})

REQUIRED_FIELDS = (
    "source",
    "acquired_at_utc",
    "raw_file_path",
    "sha256",
    "license_status",
    "redistribution_decision",
)

_HEX_DIGITS = frozenset("0123456789abcdef")


def validate_provenance_metadata(metadata: dict[str, Any]) -> list[str]:
    """Validate provenance metadata and return human-readable errors.

    Returns an empty list when the metadata is coherent. Contradictory or
    incomplete records produce one error message per problem.
    """
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if not metadata.get(field):
            errors.append(f"Missing required field {field!r}")
    if errors:
        return errors

    license_status = metadata["license_status"]
    redistribution = metadata["redistribution_decision"]

    if license_status not in LICENSE_STATUSES:
        errors.append(
            f"Invalid license_status {license_status!r}; "
            f"expected one of {sorted(LICENSE_STATUSES)}"
        )
    if redistribution not in REDISTRIBUTION_DECISIONS:
        errors.append(
            f"Invalid redistribution_decision {redistribution!r}; "
            f"expected one of {sorted(REDISTRIBUTION_DECISIONS)}"
        )

    # Contradiction: an unverified license can never permit redistribution.
    if license_status == "unverified" and redistribution == "permitted":
        errors.append(
            "Contradictory metadata: license_status 'unverified' forbids "
            "redistribution, but redistribution_decision is 'permitted'"
        )

    try:
        acquired = datetime.fromisoformat(
            metadata["acquired_at_utc"].replace("Z", "+00:00")
        )
        if acquired > datetime.now(UTC):
            errors.append("acquired_at_utc is in the future")
    except ValueError:
        errors.append("acquired_at_utc is not a valid ISO-8601 timestamp")

    if not _is_safe_raw_path(metadata["raw_file_path"]):
        errors.append(
            f"raw_file_path {metadata['raw_file_path']!r} must be a relative "
            "path under data/raw/"
        )

    sha256 = metadata["sha256"].lower()
    if len(sha256) != 64 or any(char not in _HEX_DIGITS for char in sha256):
        errors.append("sha256 must be a 64-character lowercase hex digest")

    return errors


def verify_checksum(metadata: dict[str, Any], csv_bytes: bytes) -> list[str]:
    """Verify the recorded sha256 against the actual CSV bytes."""
    digest = hashlib.sha256(csv_bytes).hexdigest()
    if digest != metadata.get("sha256"):
        return [
            f"sha256 mismatch: recorded {metadata.get('sha256')!r}, "
            f"actual {digest!r}"
        ]
    return []


def _is_safe_raw_path(path: str) -> bool:
    raw_path = Path(path)
    if raw_path.is_absolute() or ".." in raw_path.parts:
        return False
    return raw_path.parts[:2] == ("data", "raw")