"""Tests for local-only provenance validation.

Covers license, timestamp, checksum, and path cases; contradictory metadata
must be rejected before any training run touches the data.
"""
import hashlib

from churn_ml.infrastructure.filesystem.provenance import (
    validate_provenance_metadata,
    verify_checksum,
)


def _valid_metadata() -> dict[str, str]:
    return {
        "source": "Operator-provided local CSV",
        "acquired_at_utc": "2026-07-15T00:00:00Z",
        "raw_file_path": "data/raw/ai-student-impact/ai_student_impact_dataset.csv",
        "sha256": "4d911088c4b12d60a450a9acae6b606f4119ebbb48679518e427a4fc00778472",
        "license_status": "unverified",
        "redistribution_decision": "prohibited",
        "refresh_instructions": "Recalculate SHA-256 after any replacement.",
    }


# ---------------------------------------------------------------------------
# Coherent metadata
# ---------------------------------------------------------------------------

class TestValidMetadata:
    def test_valid_metadata_passes(self) -> None:
        assert validate_provenance_metadata(_valid_metadata()) == []

    def test_verified_license_with_prohibited_redistribution_passes(self) -> None:
        metadata = _valid_metadata()
        metadata["license_status"] = "verified"

        assert validate_provenance_metadata(metadata) == []


# ---------------------------------------------------------------------------
# Missing / invalid fields
# ---------------------------------------------------------------------------

class TestRequiredFields:
    def test_missing_required_field_reported(self) -> None:
        metadata = _valid_metadata()
        del metadata["sha256"]

        errors = validate_provenance_metadata(metadata)

        assert any("sha256" in error for error in errors)

    def test_empty_required_field_reported(self) -> None:
        metadata = _valid_metadata()
        metadata["source"] = ""

        errors = validate_provenance_metadata(metadata)

        assert any("source" in error for error in errors)

    def test_invalid_license_status_reported(self) -> None:
        metadata = _valid_metadata()
        metadata["license_status"] = "maybe"

        errors = validate_provenance_metadata(metadata)

        assert any("license_status" in error for error in errors)

    def test_invalid_redistribution_decision_reported(self) -> None:
        metadata = _valid_metadata()
        metadata["redistribution_decision"] = "sure"

        errors = validate_provenance_metadata(metadata)

        assert any("redistribution_decision" in error for error in errors)


# ---------------------------------------------------------------------------
# Contradictory metadata
# ---------------------------------------------------------------------------

class TestContradictions:
    def test_unverified_license_with_permitted_redistribution_rejected(
        self,
    ) -> None:
        metadata = _valid_metadata()
        metadata["redistribution_decision"] = "permitted"

        errors = validate_provenance_metadata(metadata)

        assert any("Contradictory" in error for error in errors)


# ---------------------------------------------------------------------------
# Timestamp cases
# ---------------------------------------------------------------------------

class TestTimestamp:
    def test_invalid_timestamp_reported(self) -> None:
        metadata = _valid_metadata()
        metadata["acquired_at_utc"] = "not-a-date"

        errors = validate_provenance_metadata(metadata)

        assert any("ISO-8601" in error for error in errors)

    def test_future_timestamp_reported(self) -> None:
        metadata = _valid_metadata()
        metadata["acquired_at_utc"] = "2999-01-01T00:00:00Z"

        errors = validate_provenance_metadata(metadata)

        assert any("future" in error for error in errors)


# ---------------------------------------------------------------------------
# Path cases
# ---------------------------------------------------------------------------

class TestPath:
    def test_absolute_path_reported(self) -> None:
        metadata = _valid_metadata()
        metadata["raw_file_path"] = "/etc/passwd.csv"

        errors = validate_provenance_metadata(metadata)

        assert any("data/raw" in error for error in errors)

    def test_parent_escape_reported(self) -> None:
        metadata = _valid_metadata()
        metadata["raw_file_path"] = "data/raw/../other/escape.csv"

        errors = validate_provenance_metadata(metadata)

        assert any("data/raw" in error for error in errors)

    def test_path_outside_raw_reported(self) -> None:
        metadata = _valid_metadata()
        metadata["raw_file_path"] = "data/processed/train.csv"

        errors = validate_provenance_metadata(metadata)

        assert any("data/raw" in error for error in errors)


# ---------------------------------------------------------------------------
# Checksum cases
# ---------------------------------------------------------------------------

class TestChecksum:
    def test_non_hex_sha256_reported(self) -> None:
        metadata = _valid_metadata()
        metadata["sha256"] = "z" * 64

        errors = validate_provenance_metadata(metadata)

        assert any("sha256" in error for error in errors)

    def test_short_sha256_reported(self) -> None:
        metadata = _valid_metadata()
        metadata["sha256"] = "abc123"

        errors = validate_provenance_metadata(metadata)

        assert any("sha256" in error for error in errors)

    def test_checksum_matches_csv_bytes(self) -> None:
        metadata = _valid_metadata()
        csv_bytes = b"Student_ID,Major_Category\n100001,Humanities\n"

        errors = verify_checksum(metadata, csv_bytes)

        assert "sha256 mismatch" in errors[0]
        metadata["sha256"] = hashlib.sha256(csv_bytes).hexdigest()
        assert verify_checksum(metadata, csv_bytes) == []

    def test_checksum_mismatch_reported(self) -> None:
        metadata = _valid_metadata()
        csv_bytes = b"different bytes"

        errors = verify_checksum(metadata, csv_bytes)

        assert any("mismatch" in error for error in errors)