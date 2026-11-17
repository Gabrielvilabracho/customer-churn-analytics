# Education Analytics Delivery Chain

This tracker coordinates the reviewable pull requests that deliver the education analytics dashboard.

## Pull request order

1. Education analysis core
2. Verified analysis publication
3. Education analytics API
4. Education analytics dashboard

Each pull request targets the preceding branch. The chain keeps the data-analysis, publication, API, and web layers reviewable without changing the project's default review budget.

## Out of scope

- Review-tooling changes
- Optional MLflow and notebook tracking work
- Legacy dashboard degradation fixes
- Custom CI size-exception enforcement
