# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Rodrigo Rodrigues da Silva. See ../LICENSE.

"""Chapters 7-8: a small retrieval layer over a collection handle."""

from __future__ import annotations

from typing import Any


class Retrieval:
    def __init__(self, db: Any) -> None:
        self._db = db
        self.standards = db.collection("standards")

    def search(self, query: str, k: int = 8, filters: dict | None = None) -> list[dict]:
        return self.standards.search(query, k=k, filters=filters)


def main() -> None:
    from tempfile import TemporaryDirectory

    from pavesdk.client import connect
    from shared.lattice import seed

    with TemporaryDirectory(prefix="pavedb-lattice-") as data_dir:
        with connect(data_dir, tenant="lattice") as db:
            seed(db)
            for hit in Retrieval(db).search("numbers and text in binary", k=3):
                print(f"{hit['score']:.3f} {hit['meta']['code']} {hit['text']}")


if __name__ == "__main__":
    main()
