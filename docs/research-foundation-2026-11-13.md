# Research Foundation — Evidence Checked on 2026-11-13

**Phase 1 closed with explicit limitations on 2026-11-14:** dataset binding to Kaggle version 1 and `education-v1`, declared CC0 license and historical publication integrity are verified; Python/API and frontend checks pass, isolated API probes confirm publication-integrity degradation, and the targeted literature matrix covers learning outcomes plus student-burnout/dependency instruments. Notebook training is explicitly not applicable by user decision. Generator-label methods remain unavailable and literature coverage remains targeted and non-systematic; the user accepted both as permanent Phase 1 limitations. This is not project completion or deployment approval.

## Repository and preservation

Baseline: `b3b1df72ce7cdc30f6f01baf977de29c2d027dad`, branch `feat/education-variable-analysis`. Preexisting modified `apps/web/next-env.d.ts` and untracked `odd/` were preserved. The human file retained SHA-256 `85ae5aee75f011967cf2d25cbc342f62d69314e9d925f7f4aa3456fc2cffcca6` across checks.

No installs, new research training, historical model deserialization, raw-data redistribution, commits, pushes or remote delivery checks occurred. The user explicitly authorized training/deserialization of **test-created fixtures only** for the baseline suite. Pytest updated ignored `.coverage`; its prior bytes were not captured and preservation is not claimed for that generated file.

## Dataset identity

Standard-library CSV inspection found 50,000 records, 16 columns, no empty cells, no duplicate full rows and 50,000 unique IDs. Target counts: High 12,487; Medium 21,144; Low 16,369. These checks are not psychological measurement validation.

Raw SHA-256 `4d911088c4b12d60a450a9acae6b606f4119ebbb48679518e427a4fc00778472` equals the experiment's `input_csv_sha256`. Parsed-row digest `4fe368598a6bbcaffaa4f2e08fb57ecd79803655ef99ad3e18cd8a11695c5cca` equals its `dataset_sha256`.

Reproduce the identity check without training or loading model binaries:

```bash
PYTHONPATH=packages/ml/src .venv/bin/python -B -c 'import csv,hashlib,json; from pathlib import Path; from churn_ml.application.pipelines.experiment_reports import digest; p=Path("data/01-raw/ai-student-impact/ai_student_impact_dataset.csv"); data=p.read_bytes(); rows=list(csv.DictReader(data.decode("utf-8-sig").splitlines())); r=json.loads(Path("artifacts/experiments/education-v1/report.json").read_text()); assert hashlib.sha256(data).hexdigest()==r["input_csv_sha256"]; assert digest(rows)==r["dataset_sha256"]; print("CSV and parsed-row identities match education-v1")'
```

Implementation: `packages/ml/src/churn_ml/experiments.py:98–104` records file bytes; `application/pipelines/experiments.py:117` records parsed rows; `application/pipelines/experiment_reports.py:9–10` defines the digest. The original acquisition checksum and experiment digests are not contradictory.

## Saved report byte identities

| Artifact (beneath `artifacts/`) | Fresh SHA-256 |
| --- | --- |
| `experiments/education-v1/report.json` | `efb624495d10186455246fb56cc48aeb399f018b5caa3ff731a2f3db84605f83` |
| `experiments/reevaluation-metrics-v3/report.json` | `7131a69df28db76d16bf3963979a75285e73aa10e7add999ac55b77e94e23069` |
| `education/student-analysis-20261108/variables-v1/analysis.json` | `0ae6ffc665c0019131d6bb2b00bb21e4bcbc8472a9ea66da472b659548546c92` |

`EducationAnalysisStore(Path("artifacts")).read("student-analysis-20261108", "variables-v1")` passed payload/source-binding validation without model deserialization. Hashing reports is not metric recomputation or proof of publisher authenticity.

## Fresh check matrix

Commands ran with existing local executables; no package resolution/install. `<scratch>` denotes the external temporary directory recorded in the execution handoff, not a repository path.

| Check / command | Observed result |
| --- | --- |
| `PYTHONPATH=packages/ml/src:apps/api/src .venv/bin/python -B -m pytest -q -p no:cacheprovider --basetemp <scratch>/pytest packages/ml/tests apps/api/tests` | 332 passed, 3 skipped, 218 warnings in 17.20s; coverage 89% |
| `.venv/bin/ruff check --no-cache packages/ml apps/api` | All checks passed |
| `PYTHONPATH=packages/ml/src:apps/api/src .venv/bin/python -B -m mypy --cache-dir <scratch>/mypy packages/ml/src apps/api/src` | No issues in 68 source files |
| Initial recorded Kaggle URL, public fetch | HTTP 404; subsequently corrected using user-supplied metadata and independent checks below |
| Isolated web typecheck | Pass; no TypeScript errors or warnings |
| Isolated web unit tests | 5 files, 22 tests passed; 0 failures/skips; 541ms |
| Isolated web lint | Pass; no ESLint errors or warnings |
| Isolated web E2E | 7 Chromium tests passed; 0 failures/skips; 10.2s |
| Valid education publication through runtime-composed `GET /analytics/education` | HTTP 200; `student-analysis-20261108` / `variables-v1` |
| Missing education publication through runtime-composed `GET /analytics/education` | HTTP 503 with the documented `degraded` contract |
| Tampered education publication through runtime-composed `GET /analytics/education` | HTTP 503 with the documented `degraded` contract |
| Runtime-composed `POST /predict` with a schema-valid education row | HTTP 200 but fixed `0.78` probability and `tenure_months` driver, which is absent from the education schema; deterministic legacy stub confirmed |
| Notebook isolated execution | Not run; not PASS; user selected `Close without retraining (Recommended)` because execution would start a fresh training run |
| New training, calibration, metric recomputation, operational inference | Not performed |

Warnings concern Starlette/httpx integration deprecation and joblib NumPy array-shape assignment. Skipped tests are not passing evidence. Web checks ran from a fresh external copy using the installed `node_modules`; generated Next.js/Playwright outputs stayed outside the workspace and the protected `next-env.d.ts` hash remained unchanged. API probes used FastAPI's public HTTP interface with runtime composition and copied publications in external scratch; they did not deserialize a historical model or run training. The temporary copy was removed. These checks provide local runtime evidence but not comprehensive notebook reproduction or a hosted production check.

## Source verification continuation — 2026-11-13

After the user supplied Croissant metadata and authorized continuation, a public version-1 ZIP from `laveshjadon/ai-impact-on-students` was downloaded to external temporary storage without credentials. The archive's MD5 matched the supplied metadata; its sole CSV member was compared directly against the existing study input and was byte-identical. Raw CSV SHA-256 remains the value above, so no replacement or retraining was needed. The public Kaggle API independently confirmed version 1 and CC0: Public Domain. Exact URLs, archive/CSV digests and evidence limits are in [dataset-source-verification.json](dataset-source-verification.json).

The inspected public description provides column meanings but not generator code/seed, a recruitment/collection protocol or exact burnout-label construction. License and byte identity do not establish those missing methods. The user-reported synthetic methodology is retained with that attribution. Historical acquisition metadata and all model publications remain unchanged.

## Remaining limitations and documentation drift

- **Publisher identity/license resolved; measurement limitation remains:** version 1 and declared CC0 now bind to this CSV. Exact burnout-generation rules and generator seed/code remain unknown, so only the bounded portfolio use is supported.
- **Research contract remains bounded:** the [literature matrix](literature-evidence-matrix.md) is targeted and non-systematic. Peer-reviewed burnout studies provide candidate validation methods, while three GenAI-dependency instruments remain exploratory; none validates the synthetic fields or supports a causal, clinical or population claim.
- **Reproduction boundary closed without retraining:** isolated web and public-interface publication probes pass. Notebook execution is intentionally not applicable by user decision because it starts a fresh experiment/training workflow and source verification created no need to retrain. This is not a notebook PASS or a blanket claim of application readiness.
- **Legacy prediction mismatch confirmed:** `/predict` accepts a schema-valid education row but returns fixed churn-stub evidence (`0.78`, `tenure_months`) even though `tenure_months` is not in the education schema. It is compatibility behavior, not model inference.
- **Legacy runtime/documentation mismatch:** actual raw path is `data/01-raw/`; the older provenance validator accepts `data/raw/`. CLI provenance validation is conditional on `--provenance-json`, not mandatory without that flag. No runtime contract is changed here.
- **Historical OpenSpec:** AGENTS.md's active-change path is absent; the activation artifacts are archived beneath `openspec/changes/archive/2026-08-22-activate-local-education-dashboard/`. This audit does not rewrite that historical change.

All three canonical Phase 1 TaskNotes are complete. Execution/resumption record: `odd/tasks/student-impact-research-foundation.md`. The dataset card is reconciled; broader historical-document wording is not silently declared fixed.
