from churn_ml import __version__


def test_ml_package_exposes_bootstrap_version() -> None:
    assert __version__ == "0.1.0"
