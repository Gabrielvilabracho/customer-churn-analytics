---
type: architecture
title: Artifact Contracts and Persistence
description: Authoritative analytical files, immutable publication manifests, identity binding, and downstream validation boundaries.
tags: [artifacts, persistence, integrity, contracts]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-15T19:20:50.688Z
sources:
  - id: openwiki-source-f87320bda72212b258018a47
    resource: repo://apps/api/src/churn_api/adapters/filesystem.py
  - id: openwiki-source-9288354fe66885f2a6a09d16
    resource: repo://packages/ml/src/churn_ml/infrastructure/filesystem/artifact_store.py
  - id: openwiki-source-74278f81fe4608fe3cf58291
    resource: repo://packages/ml/src/churn_ml/infrastructure/filesystem/education_analysis_adapters.py
  - id: openwiki-source-9289f3e3574caa365d4423ad
    resource: repo://packages/ml/src/churn_ml/infrastructure/filesystem/education_analysis_store.py
generated: { by: "opencode", at: "2026-11-15T19:20:50.688Z" }
---

# Artifact Contracts and Persistence

CSV and JSON outputs are the platform's authoritative integration boundary. The ML package owns their schemas and publication lifecycle; the API reads verified snapshots; the web application consumes the API contracts. Model binaries support scoring and education analysis, but they are accepted only as members of a checksum-bound publication.

## Storage layout

A published ML run is identified by `run_id` and distributed across three namespaces:

```text
artifacts/
├── processed/<run_id>/
│   ├── train.csv
│   ├── train.metadata.json
│   ├── test.csv
│   └── test.metadata.json
├── metrics/<run_id>/
│   ├── metrics.json
│   └── prediction_samples.csv
└── models/<run_id>/
    ├── model_metadata.json
    ├── model.joblib
    ├── model.joblib.sha256
    └── completion.json
```

`metrics.json` contains the serialized artifact bundle: manifest identity, evaluation metrics, and threshold selection. `prediction_samples.csv` supplies the bounded sample used by the dashboard. `model_metadata.json` carries the model identity and feature schema. The joblib binary and its sidecar checksum support verified model loading.

The processed train and test splits are not members of the base run completion manifest, but education analysis verifies them separately and binds their metadata to the same run, dataset, target, and feature schema.

## Run publication protocol

`FilesystemArtifactStore` separates writing from publication. The production CLI uses this order:

1. `save_cleaned_split` writes processed rows and split metadata.
2. `save_bundle` writes metrics, prediction samples, and merged model metadata.
3. `save_model_binary` serializes to `model.joblib.tmp` and atomically replaces the final binary, then writes its SHA-256 sidecar and metadata reference.
4. `publish_run` checks that every required metrics/model member exists, hashes each one, and writes `completion.json` **last**.

The completion file is the publication marker. A directory containing partial files without it is not published. Publishing the same run twice is rejected, which makes a completed run immutable by contract.

Per-run lease files detect an already-recorded different owner. Reacquiring an existing lease is idempotent only for the same owner; a different owner receives a lease conflict. Lease acquisition checks for the file and writes it in separate operations, so it does not guarantee mutual exclusion when processes race to create the first lease. The completion-file existence check and write are likewise separate operations; callers must avoid concurrent publication of the same run identity.

## Integrity verification

`verify_run_integrity` requires a non-empty completion manifest and recomputes every recorded member checksum. A missing completion file, missing member, altered member, or checksum mismatch raises `IntegrityError`.

The API's filesystem adapter performs this verification before loading `metrics.json` and `prediction_samples.csv`. It then checks that the loaded manifest identity matches the selected `run_id`. Consequently, a mixed-generation or partially changed run becomes a deterministic degraded API response rather than a partially served snapshot.

Checksums prove that bytes still match the publication manifest; they do not establish that the producer or model is trustworthy. In particular, joblib deserialization executes Python code, so education workflows must use only locally trusted publications.

## Education source binding

Education analysis uses a stricter source reader, `read_education_sources`, to assemble a verified snapshot. It:

- validates the requested run identity;
- refuses symlinks and paths outside the selected artifact root;
- accepts only the exact allowlisted metrics and model members;
- verifies completion-manifest and model-sidecar checksums;
- rejects mixed model/metrics identities;
- loads train and test splits and verifies their run, dataset, split name, target, and feature schema;
- returns both the bytes and a SHA-256 map covering every source member.

The analysis input adapter deserializes the model directly from the verified in-memory bytes, not by reopening an unchecked path. It also checks that the model's declared name and feature columns match publication metadata. Before publication, the workflow reads and hashes the sources again; any change during computation aborts the analysis.

## Education analysis publication

Education analyses use a two-part identity, `<run_id>/<analysis_id>`:

```text
artifacts/education/<run_id>/<analysis_id>/
├── analysis.json
└── completion.json
```

Publication first validates the complete analysis payload, then reserves the destination directory exclusively. Existing directories are never overwritten; a duplicate or concurrent publisher must choose a new analysis ID. `analysis.json` is written first and `completion.json` is created exclusively afterward with schema version, run ID, analysis ID, and payload checksum.

Reading an analysis verifies:

1. completion identity and payload checksum;
2. the full domain analysis schema;
3. payload identity against the selected path;
4. the stored source-hash map against the current verified source publication;
5. dataset and model identity against source metadata.

An analysis therefore becomes unavailable if its own payload changes, its completion marker is absent, its source artifacts become stale or altered, or its model/dataset identity no longer agrees with the source run.

## Failure and security boundaries

Artifact identifiers are validated before path construction. The education source and analysis readers resolve paths beneath a canonical root and reject symlinks or traversal outside that root. Their compatibility logic never follows stored historical paths: it extracts only allowlisted suffixes and reads those files from the currently selected local root.

The base `FilesystemArtifactStore.verify_run_integrity` reader has a narrower contract: it joins each manifest-provided member with the store root, checks that the resulting path is a file, and validates its checksum. It does not perform the education reader's explicit resolution, containment, or symlink checks, so callers must treat a base completion manifest as trusted local metadata.

Persistence failures are translated at subsystem boundaries:

- ML publication raises specific lease, publication, not-found, integrity, or validation errors.
- API filesystem adapters translate unavailable or malformed artifacts into `ArtifactUnavailableError`.
- HTTP routes convert that error into the common `503` degraded contract.

This layering keeps storage diagnostics useful while preventing raw persistence exceptions from defining the public API.

## Extension rules

When adding an artifact member, update the writer, completion-manifest allowlist, integrity reader, domain serializer, and focused contract tests together. A file that is written but not included in completion/integrity validation is not an authoritative published member.

When changing an existing schema, preserve identity fields across metrics, model metadata, split metadata, and education source bindings. Downstream readers intentionally fail closed on mismatched identities rather than attempting to infer which generation is correct.

## Related pages

- [ML Training and Artifact Publication](../workflows/ml-training-and-publication.md)
- [Education Impact Analysis Workflow](../workflows/education-analysis.md)
- [FastAPI Serving Boundary](api-serving.md)
