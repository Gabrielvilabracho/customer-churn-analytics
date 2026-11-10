"""Immutable local experiment report storage and checksum verification."""

import hashlib
import json
from io import BytesIO
from pathlib import Path
from typing import Any

from churn_ml.domain.education import validate_identity


def publish_report(
    root: Path, report_id: str, report: dict[str, Any], *, model: Any = None
) -> Path:
    validate_identity(report_id)
    directory = root.resolve() / report_id
    if directory.resolve() != directory:
        raise ValueError("Report symlinks are forbidden")
    members = {
        "report.json": json.dumps(report, sort_keys=True, indent=2, allow_nan=False).encode()
    }
    if model is not None:
        import joblib

        buffer = BytesIO()
        joblib.dump(model, buffer)
        members["model.joblib"] = buffer.getvalue()
    try:
        directory.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise ValueError("Report identity already exists; choose a new ID") from exc
    for name, data in members.items():
        with (directory / name).open("xb") as stream:
            stream.write(data)
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in members.items()}
    with (directory / "completion.json").open("x", encoding="utf-8") as stream:
        json.dump({"report_id": report_id, "members": manifest}, stream, sort_keys=True)
    return directory


def read_report(directory: Path) -> dict[str, Any]:
    if directory.absolute() != directory.resolve():
        raise ValueError("Report symlinks are forbidden")
    manifest_path = directory / "completion.json"
    if manifest_path.is_symlink():
        raise ValueError("Report symlinks are forbidden")
    manifest = json.loads(manifest_path.read_bytes())
    if manifest["report_id"] != directory.name or "report.json" not in manifest["members"]:
        raise ValueError("Invalid report identity or members")
    for name, expected in manifest["members"].items():
        if name not in ("report.json", "model.joblib") or (directory / name).is_symlink():
            raise ValueError("Invalid report member")
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected:
            raise ValueError("Report checksum mismatch")
    result: dict[str, Any] = json.loads((directory / "report.json").read_bytes())
    return result
