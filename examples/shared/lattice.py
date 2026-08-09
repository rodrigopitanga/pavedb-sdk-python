# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Rodrigo Rodrigues da Silva. See ../LICENSE.

"""Shared data setup for the runnable Lattice examples."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from pavesdk import Conflict

DATA = Path(__file__).parents[1] / "data" / "ks3-computing.sample.csv"
DOCID = "ks3-computing"


def rows() -> list[dict[str, Any]]:
    with DATA.open(newline="", encoding="utf-8") as source:
        return [
            {
                "text": row.pop("text"),
                "docid": f"{DOCID}-{row['code']}",
                "metadata": row,
            }
            for row in csv.DictReader(source)
        ]


def standards(db: Any):
    try:
        return db.create_collection("standards", display_name="Curriculum standards")
    except Conflict:
        return db.collection("standards")


def seed(db: Any):
    collection = standards(db)
    collection.add_many(rows())
    return collection
