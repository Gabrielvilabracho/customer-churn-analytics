from scripts import delivery_guardrails
from scripts.delivery_guardrails_lib import (
    cli,
    documentation,
    metadata,
    review_budget,
    workflow,
)


def test_delivery_guardrails_wrapper_preserves_public_import_contract() -> None:
    assert delivery_guardrails.GuardrailResult is metadata.GuardrailResult
    assert delivery_guardrails.REVIEW_LINE_BUDGET == review_budget.REVIEW_LINE_BUDGET
    assert delivery_guardrails.check_pr_metadata is metadata.check_pr_metadata
    assert delivery_guardrails.check_environment_pr_metadata is (
        metadata.check_environment_pr_metadata
    )
    assert delivery_guardrails.check_pull_request_workflow is workflow.check_pull_request_workflow
    assert delivery_guardrails.check_pr_changed_line_budget is (
        review_budget.check_pr_changed_line_budget
    )
    assert delivery_guardrails.check_current_review_budget is (
        review_budget.check_current_review_budget
    )
    assert delivery_guardrails.check_documentation_guardrails is (
        documentation.check_documentation_guardrails
    )
    assert delivery_guardrails.main is cli.main
