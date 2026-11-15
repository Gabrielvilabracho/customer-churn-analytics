# Application and infrastructure boundaries

Application use cases depend on framework-independent ports for loading verified
inputs, interpreting models and publishing results. The CLI is the composition
root that selects local filesystem and scikit-learn adapters.

Verified model deserialization and CSV/JSON member parsing belong in the input
adapter. It must reuse the existing source reader and deserialize exactly the
verified bytes once. Source stability is checked again before publication.
Statistical inspection remains in its existing infrastructure implementation;
the application never imports joblib, sklearn or concrete storage adapters.

Historical reevaluation receives a verified input loader and an experiment
identity provider. The filesystem adapter verifies source bytes before the
single trusted deserialization and checks the same source hashes again after
prediction. Source/runtime identity capture, immutable report publication and
checksum-verified report reads are infrastructure responsibilities; aggregate
diagnostic arithmetic remains framework-independent application logic.

The offline CLI flags, messages, source checksums, payload schema, namespace and
immutability guarantees remain unchanged. Existing API test helpers use the CLI
composition facade; in-memory port tests prove the application can run without
concrete storage or ML frameworks. This correction changes architecture, not
model fitting, evaluation results or published files.

## Planned comparable-candidate extension

The application candidate-provider port remains the model-family boundary.
Logistic regression stays the mandatory baseline adapter; XGBoost and LightGBM
may be added as optional infrastructure adapters without importing either
framework into application or domain modules. Candidate availability must be
explicit, dependency-locked, and incapable of changing the baseline path when an
optional package is absent.

All adapters receive the same feature contract and train/validation/test
identities. They return probability models plus losslessly attributable
parameters. Application logic continues to own validation-only selection,
threshold choice, final-test isolation, diagnostics, and report construction.
MLflow mirrors allowlisted immutable report evidence; it never becomes the
selection authority.

Selected-model SHAP, Registry promotion, serving, and monitoring are downstream
phases. Their adapters and contracts must not be introduced through the
candidate-provider boundary before the preceding evidence gate closes.

## Commit-review transport

OpenCode activity events are not the final reviewer verdict. For GGA's implicit
non-interactive run, use structured JSON events and render the complete final
assistant answer without tool traces. Never search for a favorable status or
manufacture approval. Invalid, errored or incomplete transport must fail closed;
GGA strict mode remains enabled. Preserve Git isolation, prompt/model/agent and
explicit caller format choices. This is a tooling boundary, not ML behavior.
