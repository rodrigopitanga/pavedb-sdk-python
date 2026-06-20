# (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json

import httpx
import pytest

from pavesdk import (
    HttpClient,
    InvalidRequest,
    LocalClientUnavailable,
    NotFoundError,
    PaveError,
    connect,
)


def _client(handler):
    transport = httpx.MockTransport(handler)
    raw = httpx.Client(base_url="http://pave.test", transport=transport)
    return HttpClient(
        "http://pave.test",
        api_key="secret",
        http_client=raw,
    )


def test_connect_dispatches_http_and_rejects_local_without_provider():
    client = connect("http://pave.test", api_key="secret")
    try:
        assert isinstance(client, HttpClient)
    finally:
        client.close()

    with pytest.raises(LocalClientUnavailable) as excinfo:
        connect("./data")
    assert excinfo.value.code == "localClientUnavailable"

    with pytest.raises(InvalidRequest) as blank:
        connect("")
    assert blank.value.code == "unsupportedTarget"


def test_collection_surface_maps_to_http_endpoints(tmp_path):
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        assert request.headers["authorization"] == "Bearer secret"

        if (
            request.method == "POST"
            and request.url.path == "/v1/collections/default/books"
        ):
            body = json.loads(request.content or b"{}")
            assert body == {"display_name": "Books"}
            return httpx.Response(
                201,
                json={"ok": True, "tenant": "default", "collection": "books"},
            )
        if request.method == "POST" and request.url.path.endswith("/documents"):
            if request.headers["content-type"].startswith("application/json"):
                body = json.loads(request.content)
                assert body["text"] == "Captain Nemo"
                return httpx.Response(
                    201,
                    json={
                        "ok": True,
                        "tenant": "default",
                        "collection": "books",
                        "docid": "note-1",
                        "chunks": 1,
                    },
                )
            assert request.url.params["csv_has_header"] == "yes"
            return httpx.Response(
                201,
                json={
                    "ok": True,
                    "tenant": "default",
                    "collection": "books",
                    "docid": "file-1",
                    "chunks": 1,
                },
            )
        if request.method == "POST" and request.url.path.endswith("/documents:batch"):
            body = json.loads(request.content)
            assert body["documents"][1]["docid"] == "note-2"
            return httpx.Response(
                201,
                json={"ok": True, "succeeded": 2, "failed": 0, "documents": []},
            )
        if request.method == "POST" and request.url.path.endswith("/search"):
            body = json.loads(request.content)
            if body["q"] == "local":
                assert body == {
                    "q": "local",
                    "k": 1,
                }
            elif body["q"] == "no-common":
                assert body == {
                    "q": "no-common",
                    "k": 1,
                    "include_common": False,
                }
            else:
                assert body == {
                    "q": "captain",
                    "k": 3,
                    "include_common": True,
                    "filters": {"kind": "note"},
                }
            return httpx.Response(
                200,
                json={
                    "ok": True,
                    "matches": [{"id": "r1", "score": 0.9, "meta": {}}],
                },
            )
        if request.method == "GET" and request.url.path.endswith("/documents"):
            return httpx.Response(
                200,
                json={"ok": True, "documents": [{"docid": "note-1"}]},
            )
        if request.method == "GET" and request.url.path.endswith("/documents/note-1"):
            return httpx.Response(
                200,
                json={"ok": True, "docid": "note-1", "metadata": {}},
            )
        if request.method == "GET" and request.url.path.endswith("/detail"):
            return httpx.Response(
                200,
                json={"ok": True, "name": "books", "doc_count": 1},
            )
        if request.method == "GET" and request.url.path.endswith("/chunks/r1/content"):
            return httpx.Response(
                200,
                content=b"Captain Nemo",
                headers={"content-type": "text/plain; charset=utf-8"},
            )
        if request.method == "POST" and request.url.path.endswith("/move"):
            body = json.loads(request.content)
            assert body == {"new_name": "library"}
            return httpx.Response(200, json={"ok": True, "name": "library"})
        raise AssertionError(f"unexpected request: {request.method} {request.url}")

    file_path = tmp_path / "book.txt"
    file_path.write_text("Captain Nemo", encoding="utf-8")

    with _client(handler) as db:
        books = db.create_collection("books", display_name="Books")
        assert books.name == "books"
        assert books.add("Captain Nemo", docid="note-1")["docid"] == "note-1"
        assert books.ingest(
            file_path,
            docid="file-1",
            csv_options={"has_header": "yes"},
        )["docid"] == "file-1"
        assert books.add_many(["A", ("B", "note-2", None)])["succeeded"] == 2
        assert books.search(
            "captain",
            k=3,
            filters={"kind": "note"},
            include_common=True,
        )[0]["id"] == "r1"
        assert books.search("local", k=1)[0]["id"] == "r1"
        assert books.search(
            "no-common",
            k=1,
            include_common=False,
        )[0]["id"] == "r1"
        assert books.list_documents() == [{"docid": "note-1"}]
        assert books.get("note-1")["docid"] == "note-1"
        assert books.detail()["doc_count"] == 1
        assert books.get_chunk_content("r1")["content"] == b"Captain Nemo"
        assert books.rename("library") is books
        assert books.name == "library"

    assert ("POST", "/v1/collections/default/books") in seen


def test_instance_methods_and_error_mapping(tmp_path):
    archive_bytes = b"PK\x03\x04"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/admin/tenants":
            return httpx.Response(200, json={"ok": True, "tenants": ["default"]})
        if request.url.path == "/v1/embedders/acme":
            return httpx.Response(
                200,
                json={"ok": True, "tenant": "acme", "embedders": []},
            )
        if request.method == "GET" and request.url.path == "/v1/admin/archive":
            return httpx.Response(200, content=archive_bytes)
        if request.method == "PUT" and request.url.path == "/v1/admin/archive":
            return httpx.Response(200, json={"ok": True, "restored": True})
        if request.url.path.endswith("/missing/detail"):
            return httpx.Response(
                404,
                json={
                    "ok": False,
                    "code": "collection_not_found",
                    "error": "missing",
                    "error_type": "not_found",
                },
            )
        if request.url.path.endswith("/invalid/detail"):
            return httpx.Response(
                400,
                json={
                    "detail": {
                        "code": "invalid_collection_name",
                        "error": "invalid",
                    },
                },
            )
        return httpx.Response(500, text="boom")

    out = tmp_path / "dump.zip"
    with _client(handler) as db:
        assert db.list_tenants() == ["default"]
        assert db.embedders(tenant="acme")["tenant"] == "acme"
        assert db.dump_archive() == archive_bytes
        assert db.dump_archive(out) == str(out)
        assert out.read_bytes() == archive_bytes
        assert db.restore_archive(archive_bytes)["restored"] is True
        with pytest.raises(NotFoundError) as missing:
            db.collection("missing").detail()
        assert missing.value.code == "collection_not_found"
        with pytest.raises(InvalidRequest) as invalid:
            db.collection("invalid").detail()
        assert invalid.value.code == "invalid_collection_name"
        with pytest.raises(PaveError) as generic:
            db.collection("boom").detail()
        assert generic.value.code == "http_500"
