# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Rodrigo Rodrigues da Silva. See ../LICENSE.

"""Chapter 2: numeric cosine intuition and an ephemeral semantic search."""

from __future__ import annotations

import math
from tempfile import TemporaryDirectory

from pavesdk.client import connect


def cosine(left: tuple[int, ...], right: tuple[int, ...]) -> float:
    return sum(a * b for a, b in zip(left, right)) / math.sqrt(
        sum(a * a for a in left) * sum(b * b for b in right)
    )


def main() -> None:
    query, on_topic, off_topic = (2, 1, 0), (4, 2, 1), (0, 1, 3)
    print(f"cosine(query, on-topic) = {cosine(query, on_topic):.2f}")
    print(f"cosine(query, off-topic) = {cosine(query, off_topic):.2f}")
    with TemporaryDirectory(prefix="pavedb-lattice-") as data_dir:
        with connect(data_dir, tenant="lattice") as db:
            standards = db.create_collection("standards")
            standards.add(
                "Pupils should be taught about chlorophyll absorbing light.",
                docid="ks3-sci-photosynthesis",
                metadata={"code": "KS3-SCI-01", "topic": "science"},
            )
            standards.add(
                "Pupils should write programs using selection and iteration.",
                docid="ks3-cs-01",
                metadata={"code": "KS3-CS-01", "topic": "computing"},
            )
            for hit in standards.search("energy from sunlight", k=2):
                print(f"{hit['score']:.3f} {hit['meta']['code']} {hit['text']}")


if __name__ == "__main__":
    main()
