"""CLI-to-API integration: a CLI-published run serves the configured API.

End-to-end proof that the ML CLI's published runs compose into the FastAPI
runtime without caller-side injection (tasks.md PR 12 / design.md testing
strategy: "CLI publishes a run; API returns 200, then tampering returns 503").
"""

import sys
from pathlib import Path

import pytest
from churn_api.main import create_runtime_app
from fastapi.testclient import TestClient

FIXTURE_CSV = (
    Path(__file__).resolve().parents[3]
    / "packages"
    / "ml"
    / "tests"
    / "fixtures"
    / "education_sample.csv"
)


def _publish_via_cli(
    monkeypatch: pytest.MonkeyPatch,
    *,
    artifact_root: Path,
    run_id: str,
) -> None:
    """Run the real CLI entrypoint against the education fixture."""
    from churn_ml.__main__ import main

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "churn_ml",
            "--csv-path",
            str(FIXTURE_CSV),
            "--dataset-id",
            "ai-student-impact",
            "--run-id",
            run_id,
            "--artifact-root",
            str(artifact_root),
        ],
    )
    main()


def _runtime_client(artifact_root: Path, run_id: str) -> TestClient:
    return TestClient(
        create_runtime_app(
            {
                "CHURN_ARTIFACT_RUN_ID": run_id,
                "CHURN_ARTIFACT_ROOT": str(artifact_root),
            }
        )
    )


def test_cli_published_run_serves_health_metadata_and_predict(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run_id = "cli-api-001"
    _publish_via_cli(monkeypatch, artifact_root=tmp_path, run_id=run_id)

    client = _runtime_client(tmp_path, run_id)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["artifact_version"] == run_id

    metadata = client.get("/model/metadata")
    assert metadata.status_code == 200
    assert metadata.json()["run_id"] == run_id

    features = {
        name: "value" if expected == "string" else 0
        for name, expected in metadata.json()["feature_schema"].items()
    }
    prediction = client.post("/predict", json={"customer_features": features})
    assert prediction.status_code == 200
    assert prediction.json()["model_version"] == run_id


def test_cli_published_run_dashboard_degrades_instead_of_fabricating(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # The education pipeline emits no public cohort fields, so the dashboard
    # degrades instead of fabricating analytics from real CLI output (PR 10).
    run_id = "cli-api-002"
    _publish_via_cli(monkeypatch, artifact_root=tmp_path, run_id=run_id)

    client = _runtime_client(tmp_path, run_id)

    dashboard = client.get("/analytics/dashboard")
    assert dashboard.status_code == 503
    assert dashboard.json()["status"] == "degraded"
    assert "cohort field" in dashboard.json()["reason"]
    assert "prediction_samples" not in dashboard.json()


def test_tampered_cli_run_degrades_health(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run_id = "cli-api-003"
    _publish_via_cli(monkeypatch, artifact_root=tmp_path, run_id=run_id)
    metrics_path = tmp_path / "metrics" / run_id / "metrics.json"
    metrics_path.write_text(metrics_path.read_text(encoding="utf-8") + " ")

    client = _runtime_client(tmp_path, run_id)

    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert "checksum mismatch" in response.json()["reason"]