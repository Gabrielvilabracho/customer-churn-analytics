from churn_api import __version__


def test_api_package_exposes_bootstrap_version() -> None:
    assert __version__ == "0.1.0"
