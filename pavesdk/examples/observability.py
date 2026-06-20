# (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from pprint import pprint

from pavesdk.client import connect
from pavesdk.errors import PaveError

SAMPLE_FILE = "demo/20k_leagues.txt"


def collection_handle(db, name: str):
    try:
        return db.create_collection(name)
    except PaveError as exc:
        if "already exists" in exc.message.lower():
            return db.collection(name)
        raise


def connection_settings() -> tuple[str, str | None, str, str]:
    return (
        os.environ.get("PAVEDB_URL", "http://localhost:8086"),
        os.environ.get("PAVEDB_API_KEY"),
        os.environ.get("PAVEDB_TENANT", "demo"),
        os.environ.get("PAVEDB_COLLECTION", "twenty-thousand-leagues"),
    )


def ingest_sample(collection) -> None:
    if not os.path.exists(SAMPLE_FILE):
        raise SystemExit(f"sample file not found: {SAMPLE_FILE}")
    collection.ingest(
        SAMPLE_FILE,
        docid="twenty-thousand-leagues",
        metadata={
            "author": "Jules Verne",
            "source": "Project Gutenberg eBook #164",
            "title": "Twenty Thousand Leagues under the Sea",
        },
    )


def main() -> None:
    url, api_key, tenant, collection = connection_settings()
    with connect(url, api_key=api_key, tenant=tenant) as db:
        books = collection_handle(db, collection)
        ingest_sample(books)
        books.search("Captain Nemo and the Nautilus", k=3)

        latest = books.queries(limit=1)[0]
        query = books.get_query(latest["query_id"])
        replayed = books.replay(query["query_id"])

        docid = replayed[0]["meta"]["docid"]
        chunks = books.list_chunks(docid)
        chunk = books.get_chunk(chunks[0]["rid"])
        content = books.get_chunk_content(chunk["rid"])

    print("latest query:")
    pprint(latest)
    print("\nquery detail:")
    pprint(query)
    print("\nreplay:")
    pprint(replayed)
    print("\nchunks:")
    pprint(chunks)
    print("\nchunk:")
    pprint(chunk)
    print("\nchunk content:")
    pprint(content)


if __name__ == "__main__":
    main()
