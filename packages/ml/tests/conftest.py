from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Protocol

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class GitCommand(Protocol):
    def __call__(self, repo: Path, *args: str) -> str: ...


class RequiredDocsWriter(Protocol):
    def __call__(
        self,
        root: Path,
        *,
        include_shortcut_policy: bool = True,
        include_delivery_guardrails: bool = True,
        include_dataset_limitations: bool = True,
    ) -> None: ...


@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def git_cmd() -> GitCommand:
    def _git(repo: Path, *args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=repo, text=True)

    return _git


@pytest.fixture
def write_required_docs() -> RequiredDocsWriter:
    def _write_required_docs(
        root: Path,
        *,
        include_shortcut_policy: bool = True,
        include_delivery_guardrails: bool = True,
        include_dataset_limitations: bool = True,
    ) -> None:
        (root / "docs").mkdir()
        (root / "README.md").write_text(
            "# Demo\n\n"
            "## Quick start\n\n"
            "Artifact-backed flow: dataset -> ML artifacts -> API -> dashboard.\n"
            "Verification commands: pytest packages/ml/tests.\n"
            "Export CHURN_ARTIFACT_RUN_ID before starting the API.\n",
            encoding="utf-8",
        )
        shortcut_policy = (
            "Changes that bypass artifact contracts or use hardcoded dashboard metrics are "
            "non-compliant until removed.\n"
            if include_shortcut_policy
            else "Dashboard metrics should look consistent.\n"
        )
        (root / "docs" / "architecture.md").write_text(
            "# Architecture\n\n"
            "Trace: dataset acquisition -> ML artifacts -> API adapters -> dashboard consumption.\n"
            f"{shortcut_policy}"
            "A completion manifest defines the published artifact boundary.\n",
            encoding="utf-8",
        )
        (root / "docs" / "api-contract.md").write_text(
            "# API Contract\n\n"
            "The API returns degraded health instead of fabricated analytics "
            "when artifacts are missing.\n",
            encoding="utf-8",
        )
        local_verification = (
            "Use data/raw/ai-student-impact/ai_student_impact_dataset.csv.\n"
            "Run --csv-path data/raw/ai-student-impact/ai_student_impact_dataset.csv.\n"
            "Use a new run ID for immutable reruns.\n"
            if include_delivery_guardrails
            else "This fixture intentionally omits the canonical local workflow and "
            "immutable rerun guarantees.\n"
        )
        (root / "docs" / "local-verification.md").write_text(
            f"# Local Verification\n\n{local_verification}",
            encoding="utf-8",
        )
        dataset_limitations = (
            "## Dataset limitations\n\n"
            "The dataset is limited and may be biased.\n\n"
            "## Product impact\n\n"
            "This dataset must not be used for automated decisions.\n"
            "Do not commit raw data. Do not redistribute raw data.\n"
            if include_dataset_limitations
            else "# Dataset Card\n\nLicense status is unverified.\n"
        )
        (root / "docs" / "dataset-card.md").write_text(
            dataset_limitations,
            encoding="utf-8",
        )

    return _write_required_docs
