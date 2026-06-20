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


class BaseClient:
    """Transport-neutral public client surface."""

    tenant: str

    def __enter__(self) -> BaseClient:
        self._ensure_open()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
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
    ) -> Collection:
        active_tenant = self._tenant(tenant)
        self._create_collection(
            active_tenant,
            name,
            display_name=display_name,
            embedder_type=embedder_type,
            embed_model=embed_model,
            embedder_config=embedder_config,
        )
        return self.collection(name, tenant=active_tenant)

    def collection(self, name: str, *, tenant: str | None = None) -> Collection:
        self._ensure_open()
        return Collection(self, self._tenant(tenant), name)

    def list_collections(self, *, tenant: str | None = None) -> list[Collection]:
        active_tenant = self._tenant(tenant)
        return [
            Collection(self, active_tenant, str(item["name"]))
            for item in self._list_collections(active_tenant)
        ]

    def list_tenants(self) -> list[str]:
        return self._list_tenants()

    def embedders(self, *, tenant: str | None = None) -> JsonMap:
        return self._embedders(self._tenant(tenant))

    def delete_collection(self, name: str, *, tenant: str | None = None) -> JsonMap:
        return self._delete_collection(self._tenant(tenant), name)

    def dump_archive(self, path: str | os.PathLike[str] | None = None) -> Any:
        return self._dump_archive(path)

    def restore_archive(self, archive_bytes: bytes) -> JsonMap:
        return self._restore_archive(archive_bytes)

    def _create_collection(
        self,
        tenant: str,
        name: str,
        *,
        display_name: str | None,
        embedder_type: str | None,
        embed_model: str | None,
        embedder_config: Mapping[str, Any] | None,
    ) -> JsonMap:
        raise NotImplementedError

    def _list_collections(self, tenant: str) -> list[Mapping[str, Any]]:
        raise NotImplementedError

    def _list_tenants(self) -> list[str]:
        raise NotImplementedError

    def _embedders(self, tenant: str) -> JsonMap:
        raise NotImplementedError

    def _delete_collection(self, tenant: str, name: str) -> JsonMap:
        raise NotImplementedError

    def _dump_archive(self, path: str | os.PathLike[str] | None = None) -> Any:
        raise NotImplementedError

    def _restore_archive(self, archive_bytes: bytes) -> JsonMap:
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
        text: str,
        *,
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
        q: str,
        k: int = 5,
        *,
        filters: FilterSpec | None = None,
        include_common: bool | None = None,
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
    """Handle for a tenant-scoped collection."""

    def __init__(self, client: BaseClient, tenant: str, name: str) -> None:
        self.client = client
        self.tenant = tenant
        self.name = name

    def __enter__(self) -> Collection:
        self.client._ensure_open()
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def ingest(
        self,
        file: str | os.PathLike[str],
        *,
        docid: str | None = None,
        metadata: Metadata | None = None,
        csv_options: Mapping[str, Any] | None = None,
    ) -> JsonMap:
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
        text: str,
        *,
        docid: str | None = None,
        metadata: Metadata | None = None,
    ) -> JsonMap:
        return self.client._add(
            self.tenant,
            self.name,
            text,
            docid=docid,
            metadata=metadata,
        )

    def add_many(self, documents: list[object]) -> JsonMap:
        return self.client._add_many(self.tenant, self.name, documents)

    def search(
        self,
        q: str,
        k: int = 5,
        *,
        filters: FilterSpec | None = None,
        include_common: bool | None = None,
    ) -> list[JsonMap]:
        return self.client._search(
            self.tenant,
            self.name,
            q,
            k,
            filters=filters,
            include_common=include_common,
        )

    def get(self, docid: str) -> JsonMap:
        return self.client._get_document(self.tenant, self.name, docid)

    def list_documents(self) -> list[JsonMap]:
        return self.client._list_documents(self.tenant, self.name)

    def delete(self, docid: str) -> JsonMap:
        return self.client._delete_document(self.tenant, self.name, docid)

    def detail(self) -> JsonMap:
        return self.client._collection_detail(self.tenant, self.name)

    def list_chunks(self, docid: str) -> list[JsonMap]:
        return self.client._list_chunks(self.tenant, self.name, docid)

    def get_chunk(self, rid: str) -> JsonMap:
        return self.client._get_chunk(self.tenant, self.name, rid)

    def get_chunk_content(self, rid: str) -> JsonMap:
        return self.client._get_chunk_content(self.tenant, self.name, rid)

    def queries(self, limit: int = 50, offset: int = 0) -> list[JsonMap]:
        return self.client._queries(self.tenant, self.name, limit, offset)

    def get_query(self, qid: str) -> JsonMap:
        return self.client._get_query(self.tenant, self.name, qid)

    def replay(self, qid: str) -> list[JsonMap]:
        return self.client._replay(self.tenant, self.name, qid)

    def rename(self, new_name: str) -> Collection:
        self.client._rename(self.tenant, self.name, new_name)
        self.name = new_name
        return self

    def update(self, *, display_name: str) -> JsonMap:
        return self.client._update_collection(
            self.tenant,
            self.name,
            display_name=display_name,
        )
