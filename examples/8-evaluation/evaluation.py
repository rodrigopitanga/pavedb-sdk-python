# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Rodrigo Rodrigues da Silva. See ../LICENSE.

"""Chapter 20: evaluate retrieval on stable curriculum codes, not document IDs."""

from __future__ import annotations

from tempfile import TemporaryDirectory

from pavesdk.client import connect
from shared.lattice import seed

GOLDEN = [
    (
        "teach selection and iteration in a programming language",
        {"KS3-CS-01", "KS3-CS-02"},
    ),
    (
        "how computers represent numbers and text in binary",
        {"KS3-CS-04", "KS3-CS-08"},
    ),
]


def recall_at_k(matches: list[dict], relevant: set[str], k: int) -> float:
    found = {match["meta"].get("code") for match in matches[:k]}
    return len(found & relevant) / len(relevant)


def main() -> None:
    with TemporaryDirectory(prefix="pavedb-lattice-") as data_dir:
        with connect(data_dir, tenant="lattice") as db:
            standards = seed(db)
            for query, relevant in GOLDEN:
                matches = standards.search(query, k=5)
                print(f"recall@5={recall_at_k(matches, relevant, 5):.3f} {query}")


if __name__ == "__main__":
    main()
