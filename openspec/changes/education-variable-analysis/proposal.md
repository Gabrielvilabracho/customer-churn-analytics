# Education variable analysis

Implement reproducible interpretability for the existing education logistic-regression model and a separate interactive `/education` dashboard.

## Scope
- Coefficients/odds ratios and direction with correct units and category contrasts.
- Held-out permutation importance, independent linear SHAP, numeric/categorical associations and student cohorts.
- Standalone analysis CLI over trusted local published model artifacts and saved train/test splits.
- Immutable analysis publication, source checksums, additive `GET /analytics/education`, and a typed interactive page.
- Tests and operational guidance. The existing prediction stub, training CLI, root dashboard and published run bytes remain unchanged.

## Decisions
- New analysis IDs refer to an existing run; model retraining is not necessary for explanation.
- Compute exact independent linear SHAP analytically in log-odds for this linear model, not a fabricated probability waterfall or correlation-dependent SHAP.
- Never follow arbitrary paths from historical manifests or deserialize unverified bytes. Verify expected members under the explicitly selected root.
- The original manifest does not authenticate training splits; bind current splits and disclose that limitation.
- User approved a size exception and later authorized local work-unit commits. No push, pull request, remote operation or in-worktree dependency installation is authorized.

## Rollback
Remove the additive education router/composition input and route; leave existing CLI, model runs and legacy endpoints unchanged. Analysis artifacts are local-only and ignored.

## Implementation record
See `odd/tasks/education-variable-analysis.md` for specs, task status and observed verification.
