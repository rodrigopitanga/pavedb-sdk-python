# (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from pprint import pprint

from pavesdk.client import connect
from pavesdk.errors import PaveError

SAMPLE_FILE = "demo/20k_leagues.txt"


def main() -> None:
    url = os.environ.get("PAVEDB_URL", "http://localhost:8086")
    api_key = os.environ.get("PAVEDB_API_KEY")
    tenant = os.environ.get("PAVEDB_TENANT", "demo")
    collection = os.environ.get("PAVEDB_COLLECTION", "twenty-thousand-leagues")

    if not os.path.exists(SAMPLE_FILE):
        raise SystemExit(f"sample file not found: {SAMPLE_FILE}")

    with connect(url, api_key=api_key, tenant=tenant) as db:
        try:
            books = db.create_collection(collection)
        except PaveError as exc:
            if "already exists" in exc.message.lower():
                books = db.collection(collection)
            else:
                raise

        books.ingest(
            SAMPLE_FILE,
            docid="twenty-thousand-leagues",
            metadata={
                "author": "Jules Verne",
                "source": "Project Gutenberg eBook #164",
                "title": "Twenty Thousand Leagues under the Sea",
            },
        )

        hits = books.search("Captain Nemo and the Nautilus", k=5)
        pprint(hits)


if __name__ == "__main__":
    main()
