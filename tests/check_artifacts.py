# (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com>
# SPDX-License-Identifier: Apache-2.0

"""Assert that book examples are shipped in the sdist, not the wheel."""

from __future__ import annotations

import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def members(path: Path) -> set[str]:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            return set(archive.namelist())
    with tarfile.open(path) as archive:
        return set(archive.getnames())


def expected_members() -> list[str]:
    return [
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "examples").rglob("*")
        if path.is_file()
        and path.suffix != ".zip"
        and "__pycache__" not in path.parts
        and "lattice-data" not in path.parts
    ]


def main(paths: list[str]) -> None:
    for raw_path in paths:
        path = Path(raw_path)
        names = members(path)
        if path.suffix == ".whl":
            assert not any(name.startswith("examples/") for name in names), path
            continue
        root = next(name.split("/", 1)[0] for name in names if "/" in name)
        missing = [item for item in expected_members() if f"{root}/{item}" not in names]
        assert not missing, f"{path}: missing {', '.join(missing)}"
    print("Artifact contents are correct.")


if __name__ == "__main__":
    main(sys.argv[1:])
