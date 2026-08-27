# Dataset Limitations Validation

## Scenario: Dataset has limitations (portfolio-documentation spec)

### Requirement
The documentation MUST state that provenance or licensing is uncertain, restricted, biased, or otherwise limited. The product impact MUST be stated plainly. The documentation MUST NOT instruct reviewers to commit or redistribute raw data.

### Evidence

#### 1. Dataset Card (`docs/dataset-card.md`)
- **License status**: "unverified on acquisition; the acquisition workflow records an `unverified`/`unknown` license status as the `prohibited` redistribution decision"
- **Redistribution decision**: "prohibited" — raw data never committed to git
- **Content**: Explicitly states the dataset is a portfolio sample with unverified provenance
- **Limitation statement**: "The repository contains dataset acquisition primitives and local directory placeholders only. No raw data has been committed."

#### 2. Modeling Report (`docs/modeling-report.md`)
- **Known limitations section**: 
  - "The education dataset is a portfolio dataset with unverified provenance, not a live production stream."
  - "Business impact, intervention costs, and retention offer outcomes are simulated through threshold/workload tradeoffs."
  - "The current education pipeline emits prediction samples without the public cohort fields of the dashboard contract, so the dashboard endpoint degrades (`503`) instead of fabricating analytics."
- **Responsible use section**: 
  - "Burnout-risk analytics are decision-support-only."
  - "They require qualified human review before any consequential use."
  - "Automated student actions (discipline, grading, enrollment, accommodations, access to services) are prohibited."

#### 3. Architecture (`docs/architecture.md`)
- **Boundaries section**: Documents that education dataset provenance is outside the domain
- **Design guarantees**: 
  - "Missing or tampered artifacts return degraded states (`503`) instead of invented values."
  - "Student-risk outputs are decision-support-only and require qualified human review; automated student actions are prohibited."
- **Verification map**: References `docs/modeling-report.md` and `docs/api-contract.md` for documentation traceability.

#### 4. API Contract (`docs/api-contract.md`)
- **Degraded responses section**: Documents that missing/tampered artifacts return `503 degraded` instead of fabricated analytics
- **Education limitation note**: Documents that the education pipeline emits prediction samples without public cohort fields, so the dashboard degrades for real education runs

### Conclusion
All documentation requirements for the "Dataset has limitations" scenario are satisfied. The uncertainty and product impact are stated plainly across multiple artifacts, and no instruction to commit or redistribute raw data is present.
