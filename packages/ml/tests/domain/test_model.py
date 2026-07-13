"""Unit tests for domain model — education label mapping (Slice 2)."""

from churn_ml.domain.model import POSITIVE_LABELS, TELCO_POSITIVE_LABELS, label_to_int


class TestLabelToIntEducationDefault:
    """Slice 2: label_to_int defaults to education POSITIVE_LABELS."""

    def test_high_maps_to_positive_class_by_default(self) -> None:
        """High burnout risk must map to 1 without explicit positive_labels."""
        assert label_to_int("High") == 1

    def test_medium_maps_to_negative_class_by_default(self) -> None:
        """Medium burnout risk must map to 0 without explicit positive_labels."""
        assert label_to_int("Medium") == 0

    def test_low_maps_to_negative_class_by_default(self) -> None:
        """Low burnout risk must map to 0 without explicit positive_labels."""
        assert label_to_int("Low") == 0

    def test_high_maps_to_positive_class_explicit(self) -> None:
        """High burnout risk must map to 1 with explicit POSITIVE_LABELS."""
        assert label_to_int("High", positive_labels=POSITIVE_LABELS) == 1

    def test_medium_maps_to_negative_class_explicit(self) -> None:
        """Medium burnout risk must map to 0 with explicit POSITIVE_LABELS."""
        assert label_to_int("Medium", positive_labels=POSITIVE_LABELS) == 0

    def test_low_maps_to_negative_class_explicit(self) -> None:
        """Low burnout risk must map to 0 with explicit POSITIVE_LABELS."""
        assert label_to_int("Low", positive_labels=POSITIVE_LABELS) == 0


class TestLabelToIntTelcoExplicit:
    """Slice 2: Telco callers must pass the Telco positive-label set explicitly."""

    def test_telco_yes_maps_with_explicit_labels(self) -> None:
        """'Yes' must map to 1 with the Telco positive-label set."""
        assert label_to_int("Yes", positive_labels=TELCO_POSITIVE_LABELS) == 1

    def test_telco_no_maps_with_explicit_labels(self) -> None:
        """'No' must map to 0 with the Telco positive-label set."""
        assert label_to_int("No", positive_labels=TELCO_POSITIVE_LABELS) == 0

    def test_all_telco_positive_label_variants_map_to_positive_class(self) -> None:
        """Telco's string and integer positive-label variants must map to 1."""
        assert label_to_int(1, positive_labels=TELCO_POSITIVE_LABELS) == 1
        assert label_to_int("1", positive_labels=TELCO_POSITIVE_LABELS) == 1
        assert label_to_int("Yes", positive_labels=TELCO_POSITIVE_LABELS) == 1
        assert label_to_int("yes", positive_labels=TELCO_POSITIVE_LABELS) == 1

    def test_telco_numeric_zero_maps_with_explicit_labels(self) -> None:
        """0 must map to 0 with the Telco positive-label set."""
        assert label_to_int(0, positive_labels=TELCO_POSITIVE_LABELS) == 0

    def test_telco_yes_does_not_map_without_explicit_labels(self) -> None:
        """'Yes' must map to 0 with education default (not in {'High'})."""
        assert label_to_int("Yes") == 0

    def test_telco_no_does_not_map_without_explicit_labels(self) -> None:
        """'No' must map to 0 with education default."""
        assert label_to_int("No") == 0


class TestDomainConstants:
    """Slice 2: domain constants are well-defined."""

    def test_positive_labels_is_frozenset_of_high(self) -> None:
        """POSITIVE_LABELS must be the frozenset {'High'}."""
        assert isinstance(POSITIVE_LABELS, frozenset)
        assert POSITIVE_LABELS == frozenset({"High"})

    def test_telco_positive_labels_preserve_all_supported_variants(self) -> None:
        """TELCO_POSITIVE_LABELS must retain the legacy Telco label variants."""
        assert isinstance(TELCO_POSITIVE_LABELS, frozenset)
        assert TELCO_POSITIVE_LABELS == frozenset({1, "1", "Yes", "yes"})
