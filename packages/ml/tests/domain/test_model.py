"""Unit tests for domain model — education label mapping."""

from churn_ml.domain.model import POSITIVE_LABELS, label_to_int


class TestLabelToInt:
    """1.1-1.2: label_to_int with configurable positive-label set."""

    def test_high_maps_to_positive_class(self) -> None:
        """High burnout risk must map to 1 (positive class)."""
        assert label_to_int("High", positive_labels=POSITIVE_LABELS) == 1

    def test_medium_maps_to_negative_class(self) -> None:
        """Medium burnout risk must map to 0 (negative class)."""
        assert label_to_int("Medium", positive_labels=POSITIVE_LABELS) == 0

    def test_low_maps_to_negative_class(self) -> None:
        """Low burnout risk must map to 0 (negative class)."""
        assert label_to_int("Low", positive_labels=POSITIVE_LABELS) == 0

    def test_default_telco_yes_maps_to_positive_class(self) -> None:
        """Without positive_labels, the original Telco default must map
        'Yes' to 1 (regression guard for existing trainers)."""
        assert label_to_int("Yes") == 1

    def test_default_telco_no_maps_to_negative_class(self) -> None:
        """Without positive_labels, the original Telco default must map
        'No' to 0 (regression guard for existing trainers)."""
        assert label_to_int("No") == 0

    def test_default_telco_numeric_one_maps_to_positive_class(self) -> None:
        """Without positive_labels, integer 1 must map to 1 (Telco default)."""
        assert label_to_int(1) == 1

    def test_default_telco_numeric_zero_maps_to_negative_class(self) -> None:
        """Without positive_labels, integer 0 must map to 0 (Telco default)."""
        assert label_to_int(0) == 0

    def test_positive_labels_is_frozenset_of_high(self) -> None:
        """POSITIVE_LABELS must be the frozenset {'High'}."""
        assert isinstance(POSITIVE_LABELS, frozenset)
        assert POSITIVE_LABELS == frozenset({"High"})
