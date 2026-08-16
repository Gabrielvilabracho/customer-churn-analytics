import hashlib
import json
import sys
from pathlib import Path

import pytest
from churn_ml.domain.model import TELCO_POSITIVE_LABELS
from churn_ml.infrastructure.filesystem.artifact_store import PublicationError

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
FIXTURE_CSV = FIXTURE_DIR / "telco_churn_sample.csv"

# ---------------------------------------------------------------------------
# B1 — Happy-path: main() writes model.joblib and metrics.json
# ---------------------------------------------------------------------------


def test_main_happy_path_writes_model_binary_and_metrics(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """main() with a valid CSV must produce model.joblib and metrics.json in tmp_path."""
    import churn_ml.__main__ as cli_module
    from churn_ml.__main__ import main

    run_id = "cli-happy-001"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "churn_ml",
            "--csv-path", str(FIXTURE_DIR / "telco_churn_sample.csv"),
            "--dataset-id", "telco-sample",
            "--run-id", run_id,
            "--artifact-root", str(tmp_path),
            "--customer-key", "customerID",
            "--target-column", "Churn",
        ],
    )
    # Fixture CSV only has 4 feature columns; patch the default to match.
    monkeypatch.setattr(
        cli_module,
        "_DEFAULT_FEATURE_COLUMNS",
        ("gender", "SeniorCitizen", "tenure", "MonthlyCharges"),
    )
    monkeypatch.setattr(cli_module, "_POSITIVE_LABELS", TELCO_POSITIVE_LABELS)

    main()

    assert (tmp_path / "models" / run_id / "model.joblib").is_file()
    assert (tmp_path / "metrics" / run_id / "metrics.json").is_file()


# ---------------------------------------------------------------------------
# F5 — CLI must exit cleanly when the CSV file does not exist
# ---------------------------------------------------------------------------


def test_main_exits_with_error_on_missing_csv_file(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() must call parser.error() and raise SystemExit for a nonexistent CSV path."""
    from churn_ml.__main__ import main

    monkeypatch.setattr(
        sys,
        "argv",
        ["churn_ml", "--csv-path", "/nonexistent/does_not_exist.csv", "--dataset-id", "test-ds"],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code != 0


# ---------------------------------------------------------------------------
# PR 7 — Provenance preflight: validate before any artifact write
# ---------------------------------------------------------------------------


def _run_main(monkeypatch: pytest.MonkeyPatch, argv: list[str]) -> None:
    """Run main() with the Telco fixture patched in, like the happy-path test."""
    import churn_ml.__main__ as cli_module
    from churn_ml.__main__ import main

    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(
        cli_module,
        "_DEFAULT_FEATURE_COLUMNS",
        ("gender", "SeniorCitizen", "tenure", "MonthlyCharges"),
    )
    monkeypatch.setattr(cli_module, "_POSITIVE_LABELS", TELCO_POSITIVE_LABELS)
    main()


def _setup_canonical_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[str, str, dict[str, str]]:
    """Place the fixture CSV at a canonical data/raw/ path and chdir there.

    Returns (csv_rel_path, raw_file_path, valid_metadata) all relative to the
    new working directory, mirroring the real local dataset layout.
    """
    monkeypatch.chdir(tmp_path)
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    csv_path = raw_dir / "telco_churn_sample.csv"
    csv_path.write_bytes(FIXTURE_CSV.read_bytes())
    csv_rel = "data/raw/telco_churn_sample.csv"
    metadata = {
        "source": "Test fixture",
        "acquired_at_utc": "2026-07-15T00:00:00Z",
        "raw_file_path": csv_rel,
        "sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "license_status": "verified",
        "redistribution_decision": "prohibited",
    }
    return csv_rel, csv_rel, metadata


def _write_metadata(tmp_path: Path, metadata: dict[str, str]) -> Path:
    import json

    metadata_path = tmp_path / "source-metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    return metadata_path


def _argv_for(
    tmp_path: Path,
    csv_rel: str,
    metadata_path: Path,
    run_id: str = "cli-prov-001",
) -> list[str]:
    return [
        "churn_ml",
        "--csv-path", csv_rel,
        "--dataset-id", "telco-sample",
        "--run-id", run_id,
        "--artifact-root", "artifacts",
        "--customer-key", "customerID",
        "--target-column", "Churn",
        "--provenance-json", str(metadata_path),
    ]


def test_main_with_valid_provenance_passes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A coherent provenance record must not block training writes."""
    csv_rel, _, metadata = _setup_canonical_fixture(tmp_path, monkeypatch)
    metadata_path = _write_metadata(tmp_path, metadata)

    _run_main(monkeypatch, _argv_for(tmp_path, csv_rel, metadata_path))

    assert (tmp_path / "artifacts" / "models" / "cli-prov-001" / "model.joblib").is_file()
    assert (tmp_path / "artifacts" / "metrics" / "cli-prov-001" / "metrics.json").is_file()


def test_main_rejects_contradictory_provenance_before_any_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Unverified license + permitted redistribution must abort before writes."""
    csv_rel, _, metadata = _setup_canonical_fixture(tmp_path, monkeypatch)
    metadata["license_status"] = "unverified"
    metadata["redistribution_decision"] = "permitted"
    metadata_path = _write_metadata(tmp_path, metadata)

    with pytest.raises(SystemExit) as exc_info:
        _run_main(monkeypatch, _argv_for(tmp_path, csv_rel, metadata_path))

    assert exc_info.value.code != 0
    assert not (tmp_path / "artifacts").exists()


def test_main_rejects_checksum_mismatch_before_any_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A recorded sha256 that does not match the CSV must abort before writes."""
    csv_rel, _, metadata = _setup_canonical_fixture(tmp_path, monkeypatch)
    metadata["sha256"] = "0" * 64
    metadata_path = _write_metadata(tmp_path, metadata)

    with pytest.raises(SystemExit) as exc_info:
        _run_main(monkeypatch, _argv_for(tmp_path, csv_rel, metadata_path))

    assert exc_info.value.code != 0
    assert not (tmp_path / "artifacts").exists()


def test_main_rejects_raw_path_mismatch_before_any_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A raw_file_path that does not match --csv-path must abort before writes."""
    csv_rel, _, metadata = _setup_canonical_fixture(tmp_path, monkeypatch)
    metadata["raw_file_path"] = "data/raw/some_other_file.csv"
    metadata_path = _write_metadata(tmp_path, metadata)

    with pytest.raises(SystemExit) as exc_info:
        _run_main(monkeypatch, _argv_for(tmp_path, csv_rel, metadata_path))

    assert exc_info.value.code != 0
    assert not (tmp_path / "artifacts").exists()


def test_main_rejects_unsafe_run_id_before_any_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A run_id that could escape the artifact root must abort before writes."""
    csv_rel, _, metadata = _setup_canonical_fixture(tmp_path, monkeypatch)
    metadata_path = _write_metadata(tmp_path, metadata)

    with pytest.raises(SystemExit) as exc_info:
        _run_main(
            monkeypatch,
            _argv_for(tmp_path, csv_rel, metadata_path, run_id="../../escape"),
        )

    assert exc_info.value.code != 0
    assert not (tmp_path / "artifacts").exists()


# ---------------------------------------------------------------------------
# PR 8 — CLI publication: lease, publish, and cleanup
# ---------------------------------------------------------------------------


def _completion_path(tmp_path: Path, run_id: str = "cli-prov-001") -> Path:
    return tmp_path / "artifacts" / "models" / run_id / "completion.json"


def _lease_path(tmp_path: Path, run_id: str = "cli-prov-001") -> Path:
    return tmp_path / "artifacts" / "models" / run_id / ".lease"


def test_main_publishes_run_and_releases_lease(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A successful run must be published and its lease released."""
    csv_rel, _, metadata = _setup_canonical_fixture(tmp_path, monkeypatch)
    metadata_path = _write_metadata(tmp_path, metadata)

    _run_main(monkeypatch, _argv_for(tmp_path, csv_rel, metadata_path))

    completion_path = _completion_path(tmp_path)
    assert completion_path.is_file(), "completion.json must exist after publish"
    manifest = json.loads(completion_path.read_text(encoding="utf-8"))
    assert manifest["run_id"] == "cli-prov-001"
    assert len(manifest["members"]) == 5
    assert not _lease_path(tmp_path).exists(), "lease must be released after success"


def test_main_releases_lease_on_training_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A failing training run must still release its lease (no dangling lock)."""
    import churn_ml.__main__ as cli_module

    csv_rel, _, metadata = _setup_canonical_fixture(tmp_path, monkeypatch)
    metadata_path = _write_metadata(tmp_path, metadata)

    def _boom(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError("training exploded")

    monkeypatch.setattr(cli_module, "run_training", _boom)

    with pytest.raises(RuntimeError, match="training exploded"):
        _run_main(monkeypatch, _argv_for(tmp_path, csv_rel, metadata_path))

    assert not _lease_path(tmp_path).exists(), "lease must be released on failure"
    assert not _completion_path(tmp_path).exists(), "no manifest on failure"


def test_main_rejects_republication_of_same_run(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A second run with the same ID must fail: published runs are immutable."""
    csv_rel, _, metadata = _setup_canonical_fixture(tmp_path, monkeypatch)
    metadata_path = _write_metadata(tmp_path, metadata)

    _run_main(monkeypatch, _argv_for(tmp_path, csv_rel, metadata_path))

    with pytest.raises(PublicationError, match="already published"):
        _run_main(monkeypatch, _argv_for(tmp_path, csv_rel, metadata_path))

    assert not _lease_path(tmp_path).exists(), "lease must be released even on failure"
