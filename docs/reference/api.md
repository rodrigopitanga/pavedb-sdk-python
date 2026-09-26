<!-- (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Regenerate: python docs/generate_reference.py -->

# PaveDB Python SDK API Reference

This reference is generated from `pavesdk.__all__`, the SDK public API boundary.

## `pavesdk.BaseClient`

Transport-neutral client surface shared by HTTP and local providers.

### `BaseClient.close`

```python
close(self) -> None
```

Release resources held by this client.

### `BaseClient.create_collection`

```python
create_collection(
    self,
    name: str,
    *,
    tenant: str | None = None,
    display_name: str | None = None,
    embedder_type: str | None = None,
    embed_model: str | None = None,
    embedder_config: Mapping[str, Any] | None = None,
    embedder: str | None = None,
    search_mode: str | None = None,
    chunking: Mapping[str, Any] | None = None,
    priority_key: str | None = None,
) -> Collection
```

Create a collection and return its tenant-scoped handle.

### `BaseClient.collection`

```python
collection(self, name: str, *, tenant: str | None = None) -> Collection
```

Return a handle for an existing collection.

### `BaseClient.list_collections`

```python
list_collections(self, *, tenant: str | None = None) -> list[Collection]
```

List collection handles for a tenant.

### `BaseClient.list_tenants`

```python
list_tenants(self) -> list[str]
```

List tenants visible to this client.

### `BaseClient.embedders`

```python
embedders(self, *, tenant: str | None = None) -> JsonMap
```

Return the configured embedders for a tenant.

### `BaseClient.delete_collection`

```python
delete_collection(self, name: str, *, tenant: str | None = None) -> JsonMap
```

Delete a collection and return the server response.

### `BaseClient.dump_archive`

```python
dump_archive(self, path: str | os.PathLike[str] | None = None) -> Any
```

Return an archive, or write it to ``path`` and return that path.

### `BaseClient.restore_archive`

```python
restore_archive(self, archive_bytes: bytes) -> JsonMap
```

Restore an archive payload and return the server response.

### `BaseClient.pause_reindex`

```python
pause_reindex(self, job_id: str) -> JsonMap
```

Pause a running reindex job (admin) and return the job.

### `BaseClient.resume_reindex`

```python
resume_reindex(self, job_id: str) -> JsonMap
```

Resume a paused reindex job (admin) and return the job.

## `pavesdk.Collection`

Handle for one tenant-scoped PaveDB collection.

```python
Collection(client: BaseClient, tenant: str, name: str)
```

Create a handle for an existing tenant-scoped collection.

### `Collection.ingest`

```python
ingest(
    self,
    file: str | os.PathLike[str],
    *,
    docid: str | None = None,
    metadata: Metadata | None = None,
    csv_options: Mapping[str, Any] | None = None,
) -> JsonMap
```

Upload a document file to this collection.

### `Collection.add`

```python
add(
    self,
    text: str | None = None,
    *,
    vector: list[float] | None = None,
    docid: str | None = None,
    metadata: Metadata | None = None,
) -> JsonMap
```

Add text or a precomputed vector to this collection.

### `Collection.add_many`

```python
add_many(self, documents: list[object]) -> JsonMap
```

Add a batch of text or vector documents to this collection.

### `Collection.search`

```python
search(
    self,
    q: str | None = None,
    k: int = 5,
    *,
    vector: list[float] | None = None,
    filters: FilterSpec | None = None,
    include_common: bool | None = None,
    mode: str | None = None,
    content_filter: Mapping[str, Any] | None = None,
) -> list[JsonMap]
```

Search this collection by text or a precomputed vector.

### `Collection.get`

```python
get(self, docid: str) -> JsonMap
```

Return one document by its document ID.

### `Collection.list_documents`

```python
list_documents(self) -> list[JsonMap]
```

List documents in this collection.

### `Collection.delete`

```python
delete(self, docid: str) -> JsonMap
```

Delete one document by its document ID.

### `Collection.detail`

```python
detail(self) -> JsonMap
```

Return this collection's metadata and summary.

### `Collection.list_chunks`

```python
list_chunks(self, docid: str) -> list[JsonMap]
```

List indexed chunks for a document.

### `Collection.get_chunk`

```python
get_chunk(self, rid: str) -> JsonMap
```

Return one indexed chunk by its record ID.

### `Collection.get_chunk_content`

```python
get_chunk_content(self, rid: str) -> JsonMap
```

Return the raw content and content type for one chunk.

### `Collection.queries`

```python
queries(self, limit: int = 50, offset: int = 0) -> list[JsonMap]
```

List recorded queries for this collection.

### `Collection.get_query`

```python
get_query(self, qid: str) -> JsonMap
```

Return one recorded query by its ID.

### `Collection.replay`

```python
replay(self, qid: str) -> list[JsonMap]
```

Replay a recorded query and return its current matches.

### `Collection.dump_archive`

```python
dump_archive(self, path: str | os.PathLike[str] | None = None) -> Any
```

Return this collection's archive, or write it to ``path``.

### `Collection.restore_archive`

```python
restore_archive(self, archive_bytes: bytes, *, replace: bool = False) -> JsonMap
```

Restore an archive as this new collection, or over it with ``replace=True``.

### `Collection.reindex`

```python
reindex(
    self,
    *,
    embedder_type: str | None = None,
    embed_model: str | None = None,
    embedder_config: Mapping[str, Any] | None = None,
) -> JsonMap
```

Start rebuilding this collection into another embedder space.

### `Collection.reindex_job`

```python
reindex_job(self, job_id: str) -> JsonMap
```

Return one of this collection's reindex jobs.

### `Collection.cancel_reindex`

```python
cancel_reindex(self, job_id: str) -> JsonMap
```

Cancel one of this collection's reindex jobs.

### `Collection.rename`

```python
rename(self, new_name: str) -> Collection
```

Rename this collection and return the same handle.

### `Collection.update`

```python
update(self, *, display_name: str) -> JsonMap
```

Update this collection's display name.

## `pavesdk.Conflict`

Request conflicts with existing state.

## `pavesdk.HttpClient`

Synchronous client for the PaveDB ``/v1`` HTTP API.

```python
HttpClient(
    base_url: str,
    *,
    api_key: str | None = None,
    tenant: str = 'default',
    timeout: float | httpx.Timeout = 30.0,
    headers: Mapping[str, str] | None = None,
    http_client: httpx.Client | None = None,
)
```

Create a client with optional bearer authentication and transport.

### `HttpClient.close`

```python
close(self) -> None
```

Close the HTTP connection pool when this client owns it.

## `pavesdk.InvalidRequest`

Request shape or arguments are invalid.

## `pavesdk.LocalClientUnavailable`

A local target was requested without a local provider installed.

## `pavesdk.NotFoundError`

Requested resource was not found.

## `pavesdk.PaveError`

Base PaveDB client error.

## `pavesdk.PAVEDB_API_PREFIX`

`'/v1'`

## `pavesdk.PAVEDB_API_VERSION`

`'v1'`

## `pavesdk.Unavailable`

The server or an underlying dependency is unavailable.

## `pavesdk.__version__`

Installed `pavedb-sdk` distribution version.

## `pavesdk.batch_item`

```python
batch_item(document: object) -> JsonMap
```

Normalize one text or vector item for ``Collection.add_many``.

## `pavesdk.connect`

```python
connect(
    target: str | os.PathLike[str] | None = None,
    *,
    api_key: str | None = None,
    tenant: str = 'default',
    timeout: float | httpx.Timeout = 30.0,
) -> HttpClient | Any
```

Connect to an HTTP server or an installed local PaveDB provider.

Omit ``target`` for an ephemeral local store. HTTP URLs return ``HttpClient``.
