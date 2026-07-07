import argparse
import uuid
from pathlib import Path

from churn_ml.application.pipelines.run_training import run_training
from churn_ml.infrastructure.filesystem.artifact_store import FilesystemArtifactStore
from churn_ml.infrastructure.sklearn.baseline import BaselineChurnRateTrainer
from churn_ml.infrastructure.sklearn.candidate import SklearnLogisticRegressionTrainer

_DEFAULT_FEATURE_COLUMNS: tuple[str, ...] = (
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "tenure",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
    "MonthlyCharges",
    "TotalCharges",
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the churn ML training pipeline from a CSV file to versioned artifacts."
    )
    parser.add_argument("--csv-path", required=True, help="Path to the input CSV dataset.")
    parser.add_argument("--dataset-id", required=True, help="Dataset identifier string.")
    parser.add_argument(
        "--run-id",
        default=None,
        help="Run identifier (auto-generated UUID prefix if omitted).",
    )
    parser.add_argument(
        "--artifact-root",
        default="artifacts",
        help="Root directory for artifact outputs (default: artifacts/).",
    )
    parser.add_argument(
        "--customer-key",
        default="customerID",
        help="Column name of the customer identifier to exclude from features.",
    )
    parser.add_argument(
        "--target-column",
        default="Churn",
        help="Column name of the binary churn target (default: Churn).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic splits and training (default: 42).",
    )
    parser.add_argument(
        "--test-fraction",
        type=float,
        default=0.2,
        help="Fraction of rows held out for evaluation (default: 0.2).",
    )

    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    if not csv_path.is_file():
        parser.error(f"CSV not found: {csv_path}")

    artifact_root = Path(args.artifact_root)
    run_id: str = args.run_id or str(uuid.uuid4())[:8]

    store = FilesystemArtifactStore(root=artifact_root)

    result = run_training(
        csv_path,
        artifact_store=store,
        run_id=run_id,
        dataset_id=args.dataset_id,
        customer_key=args.customer_key,
        target_column=args.target_column,
        baseline_trainer=BaselineChurnRateTrainer(),
        candidate_trainer=SklearnLogisticRegressionTrainer(
            model_name="candidate_logistic_regression",
            feature_columns=_DEFAULT_FEATURE_COLUMNS,
            random_state=args.seed,
        ),
        test_fraction=args.test_fraction,
        seed=args.seed,
    )

    if result.trained_candidate is not None:
        store.save_model_binary(result.trained_candidate, run_id=run_id)
        print(f"Model binary saved: {artifact_root}/models/{run_id}/model.joblib")

    print(f"Run ID:          {run_id}")
    print(f"Selected model:  {result.comparison.selected_model_name}")
    print(f"Threshold:       {result.threshold.threshold:.2f}")
    print(f"Recall:          {result.metrics.recall:.2f}")
    print(f"PR-AUC:          {result.metrics.pr_auc:.2f}")
    print(f"Top-risk capture:{result.metrics.top_risk_capture:.2f}")


if __name__ == "__main__":
    main()
