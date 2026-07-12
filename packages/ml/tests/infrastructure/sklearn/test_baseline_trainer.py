"""Unit tests for BaselineChurnRateTrainer — shared positive-label set."""

from churn_ml.domain.model import POSITIVE_LABELS, label_to_int
from churn_ml.infrastructure.sklearn.baseline import BaselineChurnRateTrainer


class TestBaselineTrainerPositiveLabels:
    """1.3-1.4: BaselineChurnRateTrainer shares POSITIVE_LABELS with label_to_int."""

    def test_baseline_trainer_default_uses_pos_high(self) -> None:
        """Baseline must treat only 'High' as positive by default."""
        trainer = BaselineChurnRateTrainer()
        rows = [
            {"target": "High"},
            {"target": "High"},
            {"target": "Low"},
            {"target": "Medium"},
        ]
        model = trainer.train(rows, target_column="target")
        assert model.probability == 0.5  # 2 High / 4 total

    def test_baseline_and_label_to_int_agree_on_same_value(self) -> None:
        """Both call sites must produce identical binary labels for the
        same raw education values (consistency scenario from spec)."""
        raw_values = ["High", "Medium", "Low"]
        trainer = BaselineChurnRateTrainer()

        for value in raw_values:
            label_from_func = label_to_int(value, positive_labels=POSITIVE_LABELS)

            # Create single-row train set to check what the trainer counts
            rows = [{"target": value}] * 2
            # The trainer computes probability = positives / total
            # If value is positive, probability = 1.0; else 0.0
            model = trainer.train(rows, target_column="target")

            expected_prob = 1.0 if value == "High" else 0.0
            assert model.probability == expected_prob, (
                f"Trainer got prob={model.probability} for '{value}', expected {expected_prob}"
            )
            assert (model.probability == 1.0) == (label_from_func == 1), (
                f"label_to_int returned {label_from_func} for '{value}' but "
                f"trainer probability={model.probability} — call sites disagree"
            )

    def test_baseline_trainer_can_accept_custom_positive_labels(self) -> None:
        """Trainer must accept a caller-supplied positive_labels for
        scenarios where the default education set does not apply."""
        trainer = BaselineChurnRateTrainer()
        rows = [
            {"target": "Yes"},
            {"target": "Yes"},
            {"target": "No"},
        ]
        model = trainer.train(
            rows,
            target_column="target",
            positive_labels=frozenset({"Yes"}),
        )
        assert model.probability == 2 / 3
