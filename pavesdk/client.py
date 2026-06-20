# (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from importlib import metadata
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

import httpx

from .batch import batch_item
from .errors import (
    InvalidRequest,
    LocalClientUnavailable,
    PaveError,
    error_class,
)
from .interface import BaseClient, FilterSpec, JsonMap, Metadata
from .providers import LOCAL_ENTRY_POINT_GROUP


def connect(
    target: str | os.PathLike[str] | None = None,
    *,
    api_key: str | None = None,
    tenant: str = "default",
    timeout: float | httpx.Timeout = 30.0,
) -> HttpClient | Any:
    """Connect over HTTP, or dispatch to an installed local provider."""
    if target is None:
        return _connect_local(target, tenant=tenant)

    raw = os.fspath(target)
    if raw == "":
        raise InvalidRequest(
            "unsupportedTarget",
            "empty connect() target; omit the argument for an ephemeral store",
        )
    parsed = urlparse(raw)
    if parsed.scheme in {"http", "https"}:
        return HttpClient(
            raw,
            api_key=api_key,
            tenant=tenant,
            timeout=timeout,
        )
    if parsed.scheme and len(parsed.scheme) > 1:
        raise InvalidRequest(
            "unsupported_scheme",
            f"unsupported connect() scheme: {parsed.scheme}",
        )
    return _connect_local(raw, tenant=tenant)


def _connect_local(target: str | os.PathLike[str] | None, *, tenant: str) -> Any:
    for provider in _local_providers():
        return provider(target, tenant=tenant)
    raise LocalClientUnavailable(
        "localClientUnavailable",
        "local mode requires installing pavedb alongside pavedb-sdk",
    )


def _local_providers() -> list[Any]:
    try:
        entry_points = metadata.entry_points()
    except Exception:
        return []
    if hasattr(entry_points, "select"):
        selected = entry_points.select(group=LOCAL_ENTRY_POINT_GROUP)
    else:
        selected = entry_points.get(LOCAL_ENTRY_POINT_GROUP, [])
    providers = []
    for entry_point in selected:
        try:
            providers.append(entry_point.load())
        except Exception:
            continue
    return providers


def segment(value: str) -> str:
    return quote(value, safe="")


class HttpClient(BaseClient):
    """Synchronous HTTP transport."""

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        tenant: str = "default",
        timeout: float | httpx.Timeout = 30.0,
        headers: Mapping[str, str] | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.tenant = tenant
        self._prefix = "" if self.base_url.endswith("/v1") else "/v1"
        self._owns_client = http_client is None
        self._closed = False

        request_headers = dict(headers or {})
        if api_key:
            request_headers["Authorization"] = f"Bearer {api_key}"

        self._client = http_client or httpx.Client(
            base_url=self.base_url,
            headers=request_headers,
            timeout=timeout,
        )
        if http_client is not None:
            self._client.headers.update(request_headers)

    def close(self) -> None:
        if self._closed:
            return
        if self._owns_client:
            self._client.close()
        self._closed = True

    def _path(self, path: str) -> str:
        return f"{self._prefix}{path}"

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        self._ensure_open()
        try:
            response = self._client.request(method, self._path(path), **kwargs)
        except httpx.TimeoutException as exc:
            raise PaveError("request_timeout", str(exc)) from exc
        except httpx.RequestError as exc:
            raise PaveError("request_failed", str(exc)) from exc
        if response.status_code >= 400:
            self._raise_response(response)
        return response

    def _json(self, method: str, path: str, **kwargs: Any) -> JsonMap:
        response = self._request(method, path, **kwargs)
        try:
            data = response.json()
        except ValueError as exc:
            raise PaveError(
                "invalid_response",
                "server returned non-JSON response",
            ) from exc
        if not isinstance(data, dict):
            raise PaveError("invalid_response", "server returned non-object JSON")
        if data.get("ok") is False:
            self._raise_data(data)
        return {k: v for k, v in data.items() if k != "ok"}

    def _raise_response(self, response: httpx.Response) -> None:
        try:
            payload = response.json()
        except ValueError:
            payload = {
                "code": f"http_{response.status_code}",
                "error": response.text or response.reason_phrase,
            }
        if isinstance(payload, dict) and isinstance(payload.get("detail"), dict):
            payload = payload["detail"]
        if not isinstance(payload, dict):
            payload = {
                "code": f"http_{response.status_code}",
                "error": str(payload),
            }
        self._raise_data(payload)

    def _raise_data(self, data: Mapping[str, Any]) -> None:
        code = str(data.get("code") or "pave_error")
        message = str(data.get("error") or data.get("message") or code)
        error_type = data.get("error_type")
        cls = error_class(code, str(error_type) if error_type else None)
        raise cls(code, message)

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
        body = {
            "display_name": display_name,
            "embedder_type": embedder_type,
            "embed_model": embed_model,
            "embedder_config": dict(embedder_config)
            if embedder_config is not None else None,
        }
        payload = {key: value for key, value in body.items() if value is not None}
        return self._json(
            "POST",
            f"/collections/{segment(tenant)}/{segment(name)}",
            json=payload or None,
        )

    def _list_collections(self, tenant: str) -> list[Mapping[str, Any]]:
        data = self._json("GET", f"/collections/{segment(tenant)}")
        return list(data["collections"])

    def _list_tenants(self) -> list[str]:
        data = self._json("GET", "/admin/tenants")
        return list(data["tenants"])

    def _embedders(self, tenant: str) -> JsonMap:
        return self._json("GET", f"/embedders/{segment(tenant)}")

    def _delete_collection(self, tenant: str, name: str) -> JsonMap:
        return self._json(
            "DELETE",
            f"/collections/{segment(tenant)}/{segment(name)}",
        )

    def _dump_archive(
        self,
        path: str | os.PathLike[str] | None = None,
    ) -> bytes | str:
        response = self._request("GET", "/admin/archive")
        if path is None:
            return response.content
        archive_path = os.fspath(path)
        Path(archive_path).write_bytes(response.content)
        return archive_path

    def _restore_archive(self, archive_bytes: bytes) -> JsonMap:
        return self._json(
            "PUT",
            "/admin/archive",
            files={"file": ("archive.zip", archive_bytes, "application/zip")},
        )

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
        params = {}
        if csv_options:
            mapping = {
                "has_header": "csv_has_header",
                "meta_cols": "csv_meta_cols",
                "include_cols": "csv_include_cols",
            }
            for key, query_key in mapping.items():
                value = csv_options.get(key)
                if value is not None:
                    params[query_key] = str(value)

        file_path = Path(file)
        files = {"file": (file_path.name, file_path.read_bytes())}
        form: dict[str, str] = {}
        if docid is not None:
            form["docid"] = docid
        if metadata is not None:
            form["metadata"] = json.dumps(metadata)

        return self._json(
            "POST",
            f"/collections/{segment(tenant)}/{segment(collection)}/documents",
            params=params or None,
            files=files,
            data=form or None,
        )

    def _add(
        self,
        tenant: str,
        collection: str,
        text: str,
        *,
        docid: str | None = None,
        metadata: Metadata | None = None,
    ) -> JsonMap:
        body = {"text": text, "docid": docid, "metadata": metadata}
        return self._json(
            "POST",
            f"/collections/{segment(tenant)}/{segment(collection)}/documents",
            json={key: value for key, value in body.items() if value is not None},
        )

    def _add_many(
        self,
        tenant: str,
        collection: str,
        documents: list[object],
    ) -> JsonMap:
        return self._json(
            "POST",
            f"/collections/{segment(tenant)}/{segment(collection)}/documents:batch",
            json={"documents": [batch_item(document) for document in documents]},
        )

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
        body: JsonMap = {"q": q, "k": k}
        if filters is not None:
            body["filters"] = filters
        if include_common is not None:
            body["include_common"] = include_common
        data = self._json(
            "POST",
            f"/collections/{segment(tenant)}/{segment(collection)}/search",
            json=body,
        )
        return list(data["matches"])

    def _get_document(self, tenant: str, collection: str, docid: str) -> JsonMap:
        return self._json(
            "GET",
            (
                f"/collections/{segment(tenant)}/{segment(collection)}"
                f"/documents/{segment(docid)}"
            ),
        )

    def _list_documents(self, tenant: str, collection: str) -> list[JsonMap]:
        data = self._json(
            "GET",
            f"/collections/{segment(tenant)}/{segment(collection)}/documents",
        )
        return list(data["documents"])

    def _delete_document(self, tenant: str, collection: str, docid: str) -> JsonMap:
        return self._json(
            "DELETE",
            (
                f"/collections/{segment(tenant)}/{segment(collection)}"
                f"/documents/{segment(docid)}"
            ),
        )

    def _collection_detail(self, tenant: str, collection: str) -> JsonMap:
        return self._json(
            "GET",
            f"/collections/{segment(tenant)}/{segment(collection)}/detail",
        )

    def _list_chunks(
        self,
        tenant: str,
        collection: str,
        docid: str,
    ) -> list[JsonMap]:
        data = self._json(
            "GET",
            (
                f"/collections/{segment(tenant)}/{segment(collection)}"
                f"/documents/{segment(docid)}/chunks"
            ),
        )
        return list(data["chunks"])

    def _get_chunk(self, tenant: str, collection: str, rid: str) -> JsonMap:
        return self._json(
            "GET",
            (
                f"/collections/{segment(tenant)}/{segment(collection)}"
                f"/chunks/{segment(rid)}"
            ),
        )

    def _get_chunk_content(
        self,
        tenant: str,
        collection: str,
        rid: str,
    ) -> JsonMap:
        response = self._request(
            "GET",
            (
                f"/collections/{segment(tenant)}/{segment(collection)}"
                f"/chunks/{segment(rid)}/content"
            ),
        )
        return {
            "content": response.content,
            "content_type": response.headers.get("content-type", "text/plain"),
        }

    def _queries(
        self,
        tenant: str,
        collection: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[JsonMap]:
        data = self._json(
            "GET",
            f"/collections/{segment(tenant)}/{segment(collection)}/queries",
            params={"limit": limit, "offset": offset},
        )
        return list(data["queries"])

    def _get_query(self, tenant: str, collection: str, qid: str) -> JsonMap:
        data = self._json(
            "GET",
            (
                f"/collections/{segment(tenant)}/{segment(collection)}"
                f"/queries/{segment(qid)}"
            ),
        )
        return data["query"]

    def _replay(self, tenant: str, collection: str, qid: str) -> list[JsonMap]:
        data = self._json(
            "POST",
            (
                f"/collections/{segment(tenant)}/{segment(collection)}"
                f"/queries/{segment(qid)}/replay"
            ),
        )
        return list(data["matches"])

    def _rename(
        self,
        tenant: str,
        old_name: str,
        new_name: str,
    ) -> None:
        self._json(
            "POST",
            f"/admin/collections/{segment(tenant)}/{segment(old_name)}/move",
            json={"new_name": new_name},
        )

    def _update_collection(
        self,
        tenant: str,
        collection: str,
        *,
        display_name: str,
    ) -> JsonMap:
        return self._json(
            "PATCH",
            f"/collections/{segment(tenant)}/{segment(collection)}",
            json={"display_name": display_name},
        )
