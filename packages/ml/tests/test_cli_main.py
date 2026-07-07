import sys
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

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
        ],
    )
    # Fixture CSV only has 4 feature columns; patch the default to match.
    monkeypatch.setattr(
        cli_module,
        "_DEFAULT_FEATURE_COLUMNS",
        ("gender", "SeniorCitizen", "tenure", "MonthlyCharges"),
    )

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
