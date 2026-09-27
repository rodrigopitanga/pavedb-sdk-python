# (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from .errors import PaveError

JsonMap = dict[str, Any]
Metadata = dict[str, Any]
FilterSpec = dict[str, Any]


def _set(**options: Any) -> JsonMap:
    """The options a caller actually set, so providers that predate one are
    not handed it."""
    return {key: value for key, value in options.items() if value is not None}


class BaseClient:
    """Transport-neutral client surface shared by HTTP and local providers."""

    tenant: str

    def __enter__(self) -> BaseClient:
        """Return this open client for use in a context manager."""
        self._ensure_open()
        return self

    def __exit__(self, *_exc: object) -> None:
        """Close this client when its context manager exits."""
        self.close()

    def close(self) -> None:
        """Release resources held by this client."""
        raise NotImplementedError

    def _ensure_open(self) -> None:
        if getattr(self, "_closed", False):
            raise PaveError("client_closed", "client is closed")

    def _tenant(self, tenant: str | None) -> str:
        return tenant or self.tenant

    def create_collection(
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
    ) -> Collection:
        """Create a collection and return its tenant-scoped handle."""
        active_tenant = self._tenant(tenant)
        self._create_collection(
            active_tenant,
            name,
            display_name=display_name,
            embedder_type=embedder_type,
            embed_model=embed_model,
            embedder_config=embedder_config,
            **_set(
                embedder=embedder,
                search_mode=search_mode,
                chunking=chunking,
                priority_key=priority_key,
            ),
        )
        return self.collection(name, tenant=active_tenant)

    def collection(self, name: str, *, tenant: str | None = None) -> Collection:
        """Return a handle for an existing collection."""
        self._ensure_open()
        return Collection(self, self._tenant(tenant), name)

    def list_collections(self, *, tenant: str | None = None) -> list[Collection]:
        """List collection handles for a tenant."""
        active_tenant = self._tenant(tenant)
        return [
            Collection(self, active_tenant, str(item["name"]))
            for item in self._list_collections(active_tenant)
        ]

    def list_tenants(self) -> list[str]:
        """List tenants visible to this client."""
        return self._list_tenants()

    def create_tenant(self, tenant: str, **options: Any) -> JsonMap:
        """Provision a tenant; an initial plaintext key is returned once."""
        self._ensure_open()
        return self._create_tenant(tenant, **options)

    def get_tenant(self, tenant: str) -> JsonMap:
        """Return the tenant profile and effective limits."""
        self._ensure_open()
        return self._get_tenant(tenant)

    def update_tenant(self, tenant: str, **changes: Any) -> JsonMap:
        """Patch supplied profile fields and nullable quota overrides."""
        self._ensure_open()
        return self._update_tenant(tenant, **changes)

    def delete_tenant(self, tenant: str) -> JsonMap:
        """Delete an empty tenant and revoke all of its keys."""
        self._ensure_open()
        return self._delete_tenant(tenant)

    def list_tenant_keys(self, tenant: str) -> JsonMap:
        """List public key metadata, including revoked keys."""
        self._ensure_open()
        return self._list_tenant_keys(tenant)

    def create_tenant_key(self, tenant: str, *, label: str = "primary") -> JsonMap:
        """Generate a tenant key and return its plaintext once."""
        self._ensure_open()
        return self._create_tenant_key(tenant, label=label)

    def revoke_tenant_key(self, tenant: str, key_id: str) -> JsonMap:
        """Revoke a tenant key by its public ID."""
        self._ensure_open()
        return self._revoke_tenant_key(tenant, key_id)

    def embedders(self, *, tenant: str | None = None) -> JsonMap:
        """Return the configured embedders for a tenant."""
        return self._embedders(self._tenant(tenant))

    def delete_collection(self, name: str, *, tenant: str | None = None) -> JsonMap:
        """Delete a collection and return the server response."""
        return self._delete_collection(self._tenant(tenant), name)

    def dump_archive(self, path: str | os.PathLike[str] | None = None) -> Any:
        """Return an archive, or write it to ``path`` and return that path."""
        return self._dump_archive(path)

    def restore_archive(self, archive_bytes: bytes) -> JsonMap:
        """Restore an archive payload and return the server response."""
        return self._restore_archive(archive_bytes)

    def pause_reindex(self, job_id: str) -> JsonMap:
        """Pause a running reindex job (admin) and return the job."""
        return self._pause_reindex(job_id)

    def resume_reindex(self, job_id: str) -> JsonMap:
        """Resume a paused reindex job (admin) and return the job."""
        return self._resume_reindex(job_id)

    def _create_collection(
        self,
        tenant: str,
        name: str,
        *,
        display_name: str | None,
        embedder_type: str | None,
        embed_model: str | None,
        embedder_config: Mapping[str, Any] | None,
        **options: Any,
    ) -> JsonMap:
        raise NotImplementedError

    def _list_collections(self, tenant: str) -> list[Mapping[str, Any]]:
        raise NotImplementedError

    def _list_tenants(self) -> list[str]:
        raise NotImplementedError

    def _create_tenant(self, tenant: str, **options: Any) -> JsonMap:
        raise NotImplementedError

    def _get_tenant(self, tenant: str) -> JsonMap:
        raise NotImplementedError

    def _update_tenant(self, tenant: str, **changes: Any) -> JsonMap:
        raise NotImplementedError

    def _delete_tenant(self, tenant: str) -> JsonMap:
        raise NotImplementedError

    def _list_tenant_keys(self, tenant: str) -> JsonMap:
        raise NotImplementedError

    def _create_tenant_key(self, tenant: str, *, label: str = "primary") -> JsonMap:
        raise NotImplementedError

    def _revoke_tenant_key(self, tenant: str, key_id: str) -> JsonMap:
        raise NotImplementedError

    def _embedders(self, tenant: str) -> JsonMap:
        raise NotImplementedError

    def _delete_collection(self, tenant: str, name: str) -> JsonMap:
        raise NotImplementedError

    def _dump_archive(self, path: str | os.PathLike[str] | None = None) -> Any:
        raise NotImplementedError

    def _restore_archive(self, archive_bytes: bytes) -> JsonMap:
        raise NotImplementedError

    def _dump_collection_archive(
        self,
        tenant: str,
        collection: str,
        path: str | os.PathLike[str] | None = None,
    ) -> Any:
        raise NotImplementedError

    def _restore_collection_archive(
        self,
        tenant: str,
        collection: str,
        archive_bytes: bytes,
        *,
        replace: bool = False,
    ) -> JsonMap:
        raise NotImplementedError

    def _reindex(
        self,
        tenant: str,
        collection: str,
        **target: Any,
    ) -> JsonMap:
        raise NotImplementedError

    def _reindex_job(self, tenant: str, collection: str, job_id: str) -> JsonMap:
        raise NotImplementedError

    def _cancel_reindex(
        self, tenant: str, collection: str, job_id: str
    ) -> JsonMap:
        raise NotImplementedError

    def _pause_reindex(self, job_id: str) -> JsonMap:
        raise NotImplementedError

    def _resume_reindex(self, job_id: str) -> JsonMap:
        raise NotImplementedError

    def _ingest(
        self,
        tenant: str,
        collection: str,
        file: str | os.PathLike[str],
        *,
        docid: str | None = None,
        metadata: Metadata | None = None,
        csv_options: Mapping[str, Any] | None = None,
    ) -> JsonMap:
        raise NotImplementedError

    def _add(
        self,
        tenant: str,
        collection: str,
        text: str | None = None,
        *,
        vector: list[float] | None = None,
        docid: str | None = None,
        metadata: Metadata | None = None,
    ) -> JsonMap:
        raise NotImplementedError

    def _add_many(
        self,
        tenant: str,
        collection: str,
        documents: list[object],
    ) -> JsonMap:
        raise NotImplementedError

    def _search(
        self,
        tenant: str,
        collection: str,
        q: str | None = None,
        k: int = 5,
        *,
        vector: list[float] | None = None,
        filters: FilterSpec | None = None,
        include_common: bool | None = None,
        **options: Any,
    ) -> list[JsonMap]:
        raise NotImplementedError

    def _get_document(self, tenant: str, collection: str, docid: str) -> JsonMap:
        raise NotImplementedError

    def _list_documents(self, tenant: str, collection: str) -> list[JsonMap]:
        raise NotImplementedError

    def _delete_document(
        self,
        tenant: str,
        collection: str,
        docid: str,
    ) -> JsonMap:
        raise NotImplementedError

    def _collection_detail(self, tenant: str, collection: str) -> JsonMap:
        raise NotImplementedError

    def _list_chunks(
        self,
        tenant: str,
        collection: str,
        docid: str,
    ) -> list[JsonMap]:
        raise NotImplementedError

    def _get_chunk(self, tenant: str, collection: str, rid: str) -> JsonMap:
        raise NotImplementedError

    def _get_chunk_content(
        self,
        tenant: str,
        collection: str,
        rid: str,
    ) -> JsonMap:
        raise NotImplementedError

    def _queries(
        self,
        tenant: str,
        collection: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[JsonMap]:
        raise NotImplementedError

    def _get_query(self, tenant: str, collection: str, qid: str) -> JsonMap:
        raise NotImplementedError

    def _replay(self, tenant: str, collection: str, qid: str) -> list[JsonMap]:
        raise NotImplementedError

    def _rename(self, tenant: str, old_name: str, new_name: str) -> None:
        raise NotImplementedError

    def _update_collection(
        self,
        tenant: str,
        collection: str,
        *,
        display_name: str,
    ) -> JsonMap:
        raise NotImplementedError


class Collection:
    """Handle for one tenant-scoped PaveDB collection."""

    def __init__(self, client: BaseClient, tenant: str, name: str) -> None:
        """Create a handle for an existing tenant-scoped collection."""
        self.client = client
        self.tenant = tenant
        self.name = name

    def __enter__(self) -> Collection:
        """Return this handle after checking that its client remains open."""
        self.client._ensure_open()
        return self

    def __exit__(self, *_exc: object) -> None:
        """Leave a collection context without closing its client."""
        return None

    def ingest(
        self,
        file: str | os.PathLike[str],
        *,
        docid: str | None = None,
        metadata: Metadata | None = None,
        csv_options: Mapping[str, Any] | None = None,
    ) -> JsonMap:
        """Upload a document file to this collection."""
        return self.client._ingest(
            self.tenant,
            self.name,
            file,
            docid=docid,
            metadata=metadata,
            csv_options=csv_options,
        )

    def add(
        self,
        text: str | None = None,
        *,
        vector: list[float] | None = None,
        docid: str | None = None,
        metadata: Metadata | None = None,
    ) -> JsonMap:
        """Add text or a precomputed vector to this collection."""
        return self.client._add(
            self.tenant,
            self.name,
            text,
            vector=vector,
            docid=docid,
            metadata=metadata,
        )

    def add_many(self, documents: list[object]) -> JsonMap:
        """Add a batch of text or vector documents to this collection."""
        return self.client._add_many(self.tenant, self.name, documents)

    def search(
        self,
        q: str | None = None,
        k: int = 5,
        *,
        vector: list[float] | None = None,
        filters: FilterSpec | None = None,
        include_common: bool | None = None,
        mode: str | None = None,
        content_filter: Mapping[str, Any] | None = None,
    ) -> list[JsonMap]:
        """Search this collection by text or a precomputed vector."""
        return self.client._search(
            self.tenant,
            self.name,
            q,
            k,
            vector=vector,
            filters=filters,
            include_common=include_common,
            **_set(mode=mode, content_filter=content_filter),
        )

    def get(self, docid: str) -> JsonMap:
        """Return one document by its document ID."""
        return self.client._get_document(self.tenant, self.name, docid)

    def list_documents(self) -> list[JsonMap]:
        """List documents in this collection."""
        return self.client._list_documents(self.tenant, self.name)

    def delete(self, docid: str) -> JsonMap:
        """Delete one document by its document ID."""
        return self.client._delete_document(self.tenant, self.name, docid)

    def detail(self) -> JsonMap:
        """Return this collection's metadata and summary."""
        return self.client._collection_detail(self.tenant, self.name)

    def list_chunks(self, docid: str) -> list[JsonMap]:
        """List indexed chunks for a document."""
        return self.client._list_chunks(self.tenant, self.name, docid)

    def get_chunk(self, rid: str) -> JsonMap:
        """Return one indexed chunk by its record ID."""
        return self.client._get_chunk(self.tenant, self.name, rid)

    def get_chunk_content(self, rid: str) -> JsonMap:
        """Return the raw content and content type for one chunk."""
        return self.client._get_chunk_content(self.tenant, self.name, rid)

    def queries(self, limit: int = 50, offset: int = 0) -> list[JsonMap]:
        """List recorded queries for this collection."""
        return self.client._queries(self.tenant, self.name, limit, offset)

    def get_query(self, qid: str) -> JsonMap:
        """Return one recorded query by its ID."""
        return self.client._get_query(self.tenant, self.name, qid)

    def replay(self, qid: str) -> list[JsonMap]:
        """Replay a recorded query and return its current matches."""
        return self.client._replay(self.tenant, self.name, qid)

    def dump_archive(self, path: str | os.PathLike[str] | None = None) -> Any:
        """Return this collection's archive, or write it to ``path``."""
        return self.client._dump_collection_archive(self.tenant, self.name, path)

    def restore_archive(
        self, archive_bytes: bytes, *, replace: bool = False
    ) -> JsonMap:
        """Restore an archive as this new collection, or over it with
        ``replace=True``."""
        return self.client._restore_collection_archive(
            self.tenant, self.name, archive_bytes, replace=replace
        )

    def reindex(
        self,
        *,
        embedder_type: str | None = None,
        embed_model: str | None = None,
        embedder_config: Mapping[str, Any] | None = None,
    ) -> JsonMap:
        """Start rebuilding this collection into another embedder space."""
        return self.client._reindex(
            self.tenant,
            self.name,
            **_set(
                embedder_type=embedder_type,
                embed_model=embed_model,
                embedder_config=embedder_config,
            ),
        )

    def reindex_job(self, job_id: str) -> JsonMap:
        """Return one of this collection's reindex jobs."""
        return self.client._reindex_job(self.tenant, self.name, job_id)

    def cancel_reindex(self, job_id: str) -> JsonMap:
        """Cancel one of this collection's reindex jobs."""
        return self.client._cancel_reindex(self.tenant, self.name, job_id)

    def rename(self, new_name: str) -> Collection:
        """Rename this collection and return the same handle."""
        self.client._rename(self.tenant, self.name, new_name)
        self.name = new_name
        return self

    def update(self, *, display_name: str) -> JsonMap:
        """Update this collection's display name."""
        return self.client._update_collection(
            self.tenant,
            self.name,
            display_name=display_name,
        )
