# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Rodrigo Rodrigues da Silva. See ../LICENSE.

"""Chapter 6: semantic search narrowed by Lattice metadata."""

from __future__ import annotations

from tempfile import TemporaryDirectory

from pavesdk.client import connect
from shared.lattice import seed


def main() -> None:
    with TemporaryDirectory(prefix="pavedb-lattice-") as data_dir:
        with connect(data_dir, tenant="lattice") as db:
            standards = seed(db)
            hits = standards.search(
                "design and evaluate algorithms",
                k=5,
                filters={
                    "level": "key-stage-3",
                    "topic": "computing",
                    "section": "*program*",
                },
            )
            for hit in hits:
                print(f"{hit['score']:.3f} {hit['meta']['code']} {hit['text']}")


if __name__ == "__main__":
    main()
