import sys

import pytest

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
