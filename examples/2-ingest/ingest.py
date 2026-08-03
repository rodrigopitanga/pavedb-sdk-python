# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Rodrigo Rodrigues da Silva. See ../LICENSE.

"""Chapter 5: ingest the Lattice sample corpus into persistent local storage."""

from __future__ import annotations

from pathlib import Path

from pavesdk.client import connect
from shared.lattice import seed

DATA_DIR = Path(__file__).parent / "lattice-data"


def main() -> None:
    with connect(DATA_DIR, tenant="lattice") as db:
        standards = seed(db)
        hit = standards.search("teach selection and iteration", k=1)[0]
        print(f"stored data: {DATA_DIR}")
        print(f"top match: {hit['meta']['code']} ({hit['score']:.3f})")


if __name__ == "__main__":
    main()
