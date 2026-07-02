from pathlib import Path

import pytest
from churn_ml.application.pipelines.acquire import create_acquisition_manifest
from churn_ml.application.ports.dataset_source import (
    DatasetSourceMetadata,
    LicenseRedistribution,
    MetadataValidationError,
    validate_source_metadata,
)


def test_valid_kaggle_source_metadata_records_local_only_guidance() -> None:
    metadata = DatasetSourceMetadata(
        source_id="blastchar/telco-customer-churn",
        source_type="kaggle",
        license_name="CC BY-NC-SA 4.0",
        redistribution=LicenseRedistribution.METADATA_ONLY,
        download_instructions=(
            "Download with the Kaggle CLI and place the CSV under data/raw/telco/."
        ),
        credential_guidance="Keep kaggle.json outside the repository.",
    )

    validated = validate_source_metadata(metadata)

    assert validated.source_id == "blastchar/telco-customer-churn"
    assert validated.redistribution is LicenseRedistribution.METADATA_ONLY
    assert "outside the repository" in validated.credential_guidance


def test_metadata_only_source_requires_download_instructions() -> None:
    metadata = DatasetSourceMetadata(
        source_id="manual/telco-customer-churn",
        source_type="manual",
        license_name="Restricted educational license",
        redistribution=LicenseRedistribution.METADATA_ONLY,
        download_instructions="",
        credential_guidance="Do not commit raw files.",
    )

    with pytest.raises(MetadataValidationError, match="download instructions"):
        validate_source_metadata(metadata)


@pytest.mark.parametrize(
    ("metadata", "message"),
    [
        (
            DatasetSourceMetadata(
                source_id=" ",
                source_type="kaggle",
                license_name="CC BY 4.0",
                redistribution=LicenseRedistribution.RAW_ALLOWED,
                download_instructions="Use the Kaggle CLI.",
                credential_guidance="Keep kaggle.json outside the repository.",
            ),
            "source id",
        ),
        (
            DatasetSourceMetadata(
                source_id="blastchar/telco-customer-churn",
                source_type="s3",
                license_name="CC BY 4.0",
                redistribution=LicenseRedistribution.RAW_ALLOWED,
                download_instructions="Use the approved internal mirror.",
                credential_guidance="No Kaggle credentials are required.",
            ),
            "kaggle or manual",
        ),
        (
            DatasetSourceMetadata(
                source_id="manual/telco-customer-churn",
                source_type="manual",
                license_name=" ",
                redistribution=LicenseRedistribution.RAW_ALLOWED,
                download_instructions="Copy the approved CSV into data/raw/telco/.",
                credential_guidance="No credentials are required for the manual file.",
            ),
            "license name",
        ),
        (
            DatasetSourceMetadata(
                source_id="manual/telco-customer-churn",
                source_type="manual",
                license_name="CC BY 4.0",
                redistribution=LicenseRedistribution.RAW_ALLOWED,
                download_instructions="Copy the approved CSV into data/raw/telco/.",
                credential_guidance=" ",
            ),
            "credential guidance",
        ),
    ],
)
def test_source_metadata_rejects_incomplete_or_unknown_source_fields(
    metadata: DatasetSourceMetadata, message: str
) -> None:
    with pytest.raises(MetadataValidationError, match=message):
        validate_source_metadata(metadata)


def test_acquisition_manifest_blocks_missing_local_raw_file(tmp_path: Path) -> None:
    metadata = DatasetSourceMetadata(
        source_id="manual/telco-customer-churn",
        source_type="manual",
        license_name="CC BY 4.0",
        redistribution=LicenseRedistribution.RAW_ALLOWED,
        download_instructions="Copy the approved CSV into data/raw/telco/.",
        credential_guidance="No credentials are required for the manual file.",
    )

    missing_file = tmp_path / "data" / "raw" / "telco" / "customers.csv"

    with pytest.raises(FileNotFoundError, match="Raw dataset file not found"):
        create_acquisition_manifest(metadata=metadata, raw_file_path=missing_file)


def test_acquisition_manifest_captures_checksum_and_timestamp(tmp_path: Path) -> None:
    raw_file = tmp_path / "customers.csv"
    raw_file.write_text("customer_id,churn\nC001,Yes\n", encoding="utf-8")
    metadata = DatasetSourceMetadata(
        source_id="manual/telco-customer-churn",
        source_type="manual",
        license_name="CC BY 4.0",
        redistribution=LicenseRedistribution.RAW_ALLOWED,
        download_instructions="Copy the approved CSV into data/raw/telco/.",
        credential_guidance="No credentials are required for the manual file.",
    )

    manifest = create_acquisition_manifest(metadata=metadata, raw_file_path=raw_file)

    assert manifest.raw_file_path == raw_file
    assert manifest.sha256 == "7ae351856b721332e0fa0f49f57c5358d5756650383605fb5598369b2891eac8"
    assert manifest.acquired_at_utc.endswith("Z")
