# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Rodrigo Rodrigues da Silva. See ../LICENSE.

"""Chapter 19: retrieve exact evidence and reject citations not in that evidence."""

from __future__ import annotations

from dataclasses import dataclass
from tempfile import TemporaryDirectory

from pavesdk.client import connect
from shared.lattice import seed


@dataclass(frozen=True)
class Evidence:
    code: str
    text: str


def citations_not_in(evidence: list[Evidence], citations: list[str]) -> list[str]:
    return sorted(set(citations) - {item.code for item in evidence})


def main() -> None:
    with TemporaryDirectory(prefix="pavedb-lattice-") as data_dir:
        with connect(data_dir, tenant="lattice") as db:
            standards = seed(db)
            matches = standards.search(
                "writing programs with selection and iteration",
                k=5,
                filters={"level": "key-stage-3", "jurisdiction": "england"},
            )
    evidence = [
        Evidence(hit["meta"]["code"], hit["text"])
        for hit in matches
    ]
    for item in evidence:
        print(f"[{item.code}] {item.text}")
    assert not citations_not_in(evidence, [item.code for item in evidence])


if __name__ == "__main__":
    main()
