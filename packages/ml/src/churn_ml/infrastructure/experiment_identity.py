"""Local Git, source and runtime identity for reproducible experiment reports."""

import hashlib
import platform
import subprocess
from importlib.metadata import version
from pathlib import Path
from typing import Any


class LocalExperimentIdentity:
    def __init__(self, package_root: Path | None = None) -> None:
        self.package_root = (
            package_root.resolve()
            if package_root is not None
            else Path(__file__).resolve().parents[1]
        )

    def capture(self) -> dict[str, Any]:
        checksum = hashlib.sha256()
        for path in sorted(self.package_root.rglob("*.py")):
            checksum.update(path.relative_to(self.package_root).as_posix().encode())
            checksum.update(path.read_bytes())
        try:
            revision = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=self.package_root,
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            revision = "unavailable"
        return {
            "git_head": revision,
            "source_sha256": checksum.hexdigest(),
            "python": platform.python_version(),
            "libraries": {name: version(name) for name in ("scikit-learn", "pandas", "numpy")},
        }
