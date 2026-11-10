# Education interpretability

## Requirements

### Versioned analytical results
The system MUST explain the fitted education model without retraining it. It MUST bind model, metadata, metrics, current saved splits and analytical payload to explicit run/analysis IDs and hashes. Existing publications MUST NOT change. Unsupported estimators, nonfinite inputs, invalid labels, missing or altered sources MUST fail explicitly before publication.

#### Scenario: reusable local run
Given a trusted local published education logistic model and saved splits, when analysis succeeds, then it publishes coefficients, importance, associations, independent SHAP and cohorts with provenance limitations and reproducible sampling metadata.

#### Scenario: rejected or duplicate publication
Given an altered source or an already published analysis ID, when the command runs, then it exits unsuccessfully without overwriting the publication or changing model/split bytes.

### Statistically meaningful explanations
Numeric coefficients MUST distinguish standardized and original units. Categories MUST expose their names and explicit pairwise reference contrasts. SHAP MUST use training-only background and held-out samples, preserve signed grouped additivity in log-odds, and distinguish average absolute contribution from direction. Associations MUST use point-biserial/Spearman for numeric fields and Cramér's V for nominal categories. Cohorts MUST distinguish observed outcomes from predictions, show uncertainty and suppress small groups. Outputs MUST NOT claim causality or diagnostic validity.

#### Scenario: individual explanation
Given a held-out sample, when its contributions are read, then base log-odds plus all signed contributions equals model decision output, and sigmoid of that output matches its predicted probability.

### Additive serving and interaction
`GET /analytics/education` MUST return a validated source-bound publication or deterministic 503. It MUST NOT deserialize the model or compute analysis in the request path. The `/education` page MUST support variable, cohort and anonymized sample selection, show honest loading/error/empty states, output units and decision-support warnings. No Student_ID or raw CSV is served. Existing endpoints and the root dashboard MUST remain compatible.

#### Scenario: interactive educational analysis
Given a valid publication, when a reviewer opens `/education`, then they can inspect coefficients and importance, compare train/test associations and cohorts, and select a held-out explanation with accessible charts and tables.
