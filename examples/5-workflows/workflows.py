# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Rodrigo Rodrigues da Silva. See ../LICENSE.

"""Chapter 8: batch loading, chunk inspection, replay, and archive recovery."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from pavesdk.client import connect
from shared.lattice import rows, standards

ARCHIVE = Path(__file__).parent / "lattice-archive.zip"


def main() -> None:
    with TemporaryDirectory(prefix="pavedb-lattice-") as data_dir:
        with connect(data_dir, tenant="lattice") as db:
            collection = standards(db)
            batch = collection.add_many(rows())
            print(f"loaded {batch['succeeded']}/{batch['count']} outcomes")
            hit = collection.search("how instructions are executed", k=1)[0]
            chunk = collection.get_chunk(hit["id"])
            content = collection.get_chunk_content(chunk["rid"])
            print(content["content"].decode("utf-8"))
            query = collection.get_query(collection.queries(limit=1)[0]["query_id"])
            replayed = collection.replay(query["query_id"])
            print(f"replayed {len(replayed)} results")
            db.dump_archive(ARCHIVE)
            db.restore_archive(ARCHIVE.read_bytes())
    print(f"archive: {ARCHIVE}")


if __name__ == "__main__":
    main()
