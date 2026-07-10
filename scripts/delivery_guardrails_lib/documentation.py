from __future__ import annotations

from pathlib import Path

from scripts.delivery_guardrails_lib.result import GuardrailResult


def check_documentation_guardrails(project_root: Path) -> GuardrailResult:
    documents = _required_documents(project_root)
    missing = [name for name, path in documents.items() if not path.exists()]
    if missing:
        return GuardrailResult(False, {"documents": f"missing: {', '.join(missing)}"})

    readme = documents["README.md"].read_text(encoding="utf-8").lower()
    architecture = documents["docs/architecture.md"].read_text(encoding="utf-8").lower()
    api_contract = documents["docs/api-contract.md"].read_text(encoding="utf-8").lower()
    checks = _documentation_checks(readme, architecture, api_contract)
    return GuardrailResult(all(checks.values()), _documentation_details(checks))


def _required_documents(project_root: Path) -> dict[str, Path]:
    return {
        "README.md": project_root / "README.md",
        "docs/architecture.md": project_root / "docs" / "architecture.md",
        "docs/api-contract.md": project_root / "docs" / "api-contract.md",
    }


def _documentation_checks(readme: str, architecture: str, api_contract: str) -> dict[str, bool]:
    return {
        "review_path": all(
            marker in readme for marker in ("quick start", "artifact", "verification commands")
        ),
        "architecture_trace": all(
            marker in architecture for marker in ("dataset", "ml artifact", "api", "dashboard")
        ),
        "artifact_contracts": "artifact contracts" in architecture and "artifact-backed" in readme,
        "no_fabricated_analytics": "fabricated analytics" in api_contract
        and "degraded" in api_contract,
        "shortcut_policy": all(
            marker in architecture
            for marker in (
                "bypass artifact contracts",
                "hardcoded dashboard metrics",
                "non-compliant",
            )
        ),
    }


def _documentation_details(checks: dict[str, bool]) -> dict[str, str]:
    return {
        "review_path": "documented" if checks["review_path"] else "missing",
        "architecture_trace": "documented" if checks["architecture_trace"] else "missing",
        "artifact_contracts": "documented" if checks["artifact_contracts"] else "missing",
        "no_fabricated_analytics": "documented" if checks["no_fabricated_analytics"] else "missing",
        "shortcut_policy": "documented" if checks["shortcut_policy"] else "missing",
    }
