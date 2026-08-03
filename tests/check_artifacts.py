# (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com>
# SPDX-License-Identifier: Apache-2.0

"""Assert that book examples are shipped in the sdist, not the wheel."""

from __future__ import annotations

import sys
import tarfile
import zipfile
from pathlib import Path

EXPECTED = (
    "examples/LICENSE",
    "examples/data/ks3-computing.sample.csv",
    "examples/1-intuition/README.md",
    "examples/8-evaluation/evaluation.py",
)


def members(path: Path) -> set[str]:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            return set(archive.namelist())
    with tarfile.open(path) as archive:
        return set(archive.getnames())


def main(paths: list[str]) -> None:
    for raw_path in paths:
        path = Path(raw_path)
        names = members(path)
        if path.suffix == ".whl":
            assert not any(name.startswith("examples/") for name in names), path
            continue
        root = next(name.split("/", 1)[0] for name in names if "/" in name)
        missing = [item for item in EXPECTED if f"{root}/{item}" not in names]
        assert not missing, f"{path}: missing {', '.join(missing)}"
    print("Artifact contents are correct.")


if __name__ == "__main__":
    main(sys.argv[1:])
