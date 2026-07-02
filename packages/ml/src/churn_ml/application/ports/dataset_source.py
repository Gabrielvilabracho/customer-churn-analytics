from dataclasses import dataclass
from enum import StrEnum


class LicenseRedistribution(StrEnum):
    RAW_ALLOWED = "raw_allowed"
    METADATA_ONLY = "metadata_only"


class MetadataValidationError(ValueError):
    """Raised when dataset source metadata is incomplete or unsafe."""


@dataclass(frozen=True)
class DatasetSourceMetadata:
    source_id: str
    source_type: str
    license_name: str
    redistribution: LicenseRedistribution
    download_instructions: str
    credential_guidance: str


def validate_source_metadata(metadata: DatasetSourceMetadata) -> DatasetSourceMetadata:
    if not metadata.source_id.strip():
        raise MetadataValidationError("Dataset source id is required.")
    if metadata.source_type not in {"kaggle", "manual"}:
        raise MetadataValidationError("Dataset source type must be kaggle or manual.")
    if not metadata.license_name.strip():
        raise MetadataValidationError("Dataset license name is required.")
    if metadata.redistribution is LicenseRedistribution.METADATA_ONLY:
        if not metadata.download_instructions.strip():
            raise MetadataValidationError("Metadata-only datasets require download instructions.")
    if not metadata.credential_guidance.strip():
        raise MetadataValidationError("Local-only credential guidance is required.")
    return metadata
