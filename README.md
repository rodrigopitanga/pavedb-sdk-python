<!-- (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# PaveDB Python SDK

Python SDK package for the PaveDB `/v1` API.

Use `pavedb-sdk` when your code should talk to PaveDB from Python.

There are three runtime paths:

- Connect to a PaveDB server over HTTP.
- Install `pavedb` alongside the SDK and use the same `Client` /
  `Collection` handle API with a local embedded engine.
- Use ephemeral local mode for temporary in-process stores during tests,
  notebooks, and short-lived experiments.

To run your own server instance, use the PaveDB core repository:
[GitLab](https://gitlab.com/flowlexi/pavedb) /
[GitHub](https://github.com/rodrigopitanga/pavedb). The core repository
remains the source of truth for the OpenAPI contract.

SDK source lives on
[GitLab](https://gitlab.com/flowlexi/pavedb-sdk-python) and
[GitHub](https://github.com/rodrigopitanga/pavedb-sdk-python).

## Install

```bash
pip install pavedb-sdk
```

SDK `0.1.x` targets the PaveDB `/v1` API. SDK package versions are
independent from PaveDB core release versions; use `pavesdk.__version__`
for the SDK release and `pavesdk.PAVEDB_API_PREFIX` for the wire API.

For local embedded/persisted mode:

```bash
pip install pavedb-sdk pavedb
```

## Local Package Build

Build the local PyPI package artifacts with GNU Make:

```bash
gmake package
```

That creates the source distribution (`.tar.gz`) and wheel in `dist/`,
checks them with Twine, and copies them to `artifacts/`.

Upload targets are explicit and do not infer release channels from the version:

```bash
gmake pypitest-push
gmake pypi-push
```

Runnable HTTP examples are installed with the package:

```bash
python -m pavesdk.examples.http_search
python -m pavesdk.examples.observability
```

The SDK checkout also includes `demo/20k_leagues.txt`, which the examples use
via a hardcoded relative path.

## HTTP Client

```python
from pavesdk.client import connect

db = connect(
    "http://localhost:8086",
    api_key="super-sekret",
    tenant="demo",
)
books = db.collection("books")

hits = books.search("captain nemo", k=3)
hits
```

```text
[
    {
        "id": "note-1:0000",
        "score": 0.86,
        "text": "Captain Nemo commands the Nautilus.",
        "meta": {"docid": "note-1", "kind": "note"},
    },
    {
        "id": "note-2:0000",
        "score": 0.73,
        "text": "The Nautilus dives beneath the ice.",
        "meta": {"docid": "note-2", "kind": "note"},
    },
]
```

```python
for hit in hits:
    print(hit["score"], hit["meta"]["docid"], hit["text"][:80])
```

```text
0.86 note-1 Captain Nemo commands the Nautilus.
0.73 note-2 The Nautilus dives beneath the ice.
```

`connect("http://...")` and `connect("https://...")` create an `HttpClient`.
Bare paths are local targets and require `pavedb` to be installed.

## Collections

The API is handle-based: pick a collection once, then call methods on it.

```python
from pavesdk.client import connect

db = connect("http://localhost:8086", api_key="super-sekret")
books = db.create_collection("books", tenant="demo")

books.add(
    "Captain Nemo commands the Nautilus.",
    docid="note-1",
    metadata={"kind": "note"},
)
books.add_many([
    ("The Nautilus dives beneath the ice.", "note-2", None),
    {
        "text": "Nemo studies ocean currents.",
        "docid": "note-3",
        "metadata": {"kind": "note"},
    },
])

matches = books.search(
    "submarine captain",
    k=5,
    filters={"kind": "note"},
)
matches
```

```text
[
    {
        "id": "note-1:0000",
        "score": 0.81,
        "text": "Captain Nemo commands the Nautilus.",
        "meta": {"docid": "note-1", "kind": "note"},
    },
    {
        "id": "note-3:0000",
        "score": 0.69,
        "text": "Nemo studies ocean currents.",
        "meta": {"docid": "note-3", "kind": "note"},
    },
]
```

## Observability

Searches are logged by PaveDB. Use query inspection to see what ran, replay it
against current data, and inspect the source chunks behind a document.

```python
from pavesdk.client import connect

db = connect("http://localhost:8086", api_key="super-sekret")
books = db.collection("books", tenant="demo")

books.search("captain nemo", k=3)

latest = books.queries(limit=1)[0]
latest
```

```text
{
    "query_id": "0d4f5a1b-9e4b-41c7-8b3f-8f6b5de3e74a",
    "tenant": "demo",
    "collection": "books",
    "query_text": "captain nemo",
    "k": 3,
    "filters": None,
    "result_count": 2,
    "latency_ms": 12.4,
    "created_at": "2026-06-20T18:42:16.153201Z",
}
```

```python
query = books.get_query(latest["query_id"])
query
```

```text
{
    "query_id": "0d4f5a1b-9e4b-41c7-8b3f-8f6b5de3e74a",
    "tenant": "demo",
    "collection": "books",
    "query_text": "captain nemo",
    "k": 3,
    "filters": None,
    "result_ids": ["note-1:0000", "note-2:0000"],
    "result_count": 2,
    "latency_ms": 12.4,
}
```

```python
replayed = books.replay(query["query_id"])
replayed
```

```text
[
    {
        "id": "note-1:0000",
        "score": 0.86,
        "text": "Captain Nemo commands the Nautilus.",
        "meta": {"docid": "note-1", "kind": "note"},
    },
    {
        "id": "note-2:0000",
        "score": 0.73,
        "text": "The Nautilus dives beneath the ice.",
        "meta": {"docid": "note-2", "kind": "note"},
    },
]
```

```python
docid = replayed[0]["meta"]["docid"]
chunks = books.list_chunks(docid)
chunks
```

```text
[
    {
        "rid": "note-1:0000",
        "docid": "note-1",
        "chunk": 0,
        "text": "Captain Nemo commands the Nautilus.",
        "metadata": {"kind": "note"},
    }
]
```

```python
chunk = books.get_chunk(chunks[0]["rid"])
chunk
```

```text
{
    "rid": "note-1:0000",
    "docid": "note-1",
    "chunk": 0,
    "text": "Captain Nemo commands the Nautilus.",
    "metadata": {"kind": "note"},
}
```

```python
content = books.get_chunk_content(chunk["rid"])
content
```

```text
{
    "content": b"Captain Nemo commands the Nautilus.",
    "content_type": "text/plain; charset=utf-8",
}
```

## Local Mode

With `pavedb` installed, the same API can use a local persisted store:

```python
from pavesdk.client import connect

with connect("./data", tenant="demo") as db:
    books = db.create_collection("books")
    books.add("Captain Nemo commands the Nautilus.", docid="note-1")
    print(books.search("captain", k=3))
```

If `pavedb` is not installed, local targets raise `LocalClientUnavailable`.

## Archives

```python
from pathlib import Path
from pavesdk.client import connect

with connect("http://localhost:8086", api_key="super-sekret") as db:
    archive_bytes = db.dump_archive()
    Path("pavedb-data.zip").write_bytes(archive_bytes)

    saved_path = db.dump_archive("pavedb-data.zip")
    db.restore_archive(Path(saved_path).read_bytes())
```
