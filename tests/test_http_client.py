# (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from importlib.metadata import version

import httpx
import pavesdk
import pytest

from pavesdk import (
    HttpClient,
    InvalidRequest,
    LocalClientUnavailable,
    NotFoundError,
    PaveError,
    connect,
)


def test_package_version_matches_distribution():
    assert pavesdk.__version__ == version("pavedb-sdk")


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


def test_collection_vector_methods_map_to_existing_payloads():
    vector = [0.1, 0.2, 0.3]

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if request.url.path.endswith("/documents"):
            assert body == {
                "vector": vector,
                "docid": "vec-1",
                "metadata": {"kind": "vector"},
            }
            return httpx.Response(201, json={"ok": True, "docid": "vec-1"})
        if request.url.path.endswith("/documents:batch"):
            assert body == {
                "documents": [
                    {"vector": vector, "docid": "vec-2", "metadata": None},
                    {"vector": vector, "docid": "vec-3", "metadata": None},
                ]
            }
            return httpx.Response(201, json={"ok": True, "succeeded": 2})
        assert request.url.path.endswith("/search")
        assert body == {"v": vector, "k": 2}
        return httpx.Response(
            200,
            json={"ok": True, "matches": [{"id": "vec-1"}]},
        )

    with _client(handler) as db:
        collection = db.collection("vectors")
        assert collection.add(
            vector=vector,
            docid="vec-1",
            metadata={"kind": "vector"},
        )["docid"] == "vec-1"
        assert collection.add_many([
            {"vector": vector, "docid": "vec-2"},
            (vector, "vec-3"),
        ])['succeeded'] == 2
        assert collection.search(vector=vector, k=2) == [{"id": "vec-1"}]


def test_pavedb_097_surface_maps_to_http_endpoints():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        seen.append((request.method, path))
        if path == "/v1/collections/acme/books" and request.method == "POST":
            assert json.loads(request.content) == {
                "search_mode": "hybrid",
                "chunking": {"strategy": "none"},
                "priority_key": "rank",
            }
            return httpx.Response(201, json={"ok": True, "name": "books"})
        if path.endswith("/search"):
            assert json.loads(request.content) == {
                "q": "nemo",
                "k": 3,
                "mode": "boost",
                "content_filter": {"op": "phrase", "value": "captain nemo"},
            }
            return httpx.Response(200, json={"ok": True, "matches": []})
        if path.endswith("/archive") and request.method == "GET":
            return httpx.Response(200, content=b"zip")
        if path.endswith("/archive"):
            assert b"zip" in request.content
            return httpx.Response(200, json={"ok": True})
        if path.endswith("/reindex"):
            assert json.loads(request.content) == {"embed_model": "m2"}
            return httpx.Response(202, json={"ok": True, "job_id": "j1"})
        return httpx.Response(200, json={"ok": True, "job_id": "j1"})

    with _client(handler) as db:
        books = db.create_collection(
            "books",
            tenant="acme",
            search_mode="hybrid",
            chunking={"strategy": "none"},
            priority_key="rank",
        )
        assert books.search(
            "nemo",
            k=3,
            mode="boost",
            content_filter={"op": "phrase", "value": "captain nemo"},
        ) == []
        archive = books.dump_archive()
        assert archive == b"zip"
        db.collection("copy", tenant="acme").restore_archive(archive)
        books.restore_archive(archive, replace=True)
        assert books.reindex(embed_model="m2")["job_id"] == "j1"
        books.reindex_job("j1")
        books.cancel_reindex("j1")
        db.pause_reindex("j1")
        db.resume_reindex("j1")

    assert seen[2:] == [
        ("GET", "/v1/collections/acme/books/archive"),
        ("POST", "/v1/collections/acme/copy/archive"),
        ("PUT", "/v1/collections/acme/books/archive"),
        ("POST", "/v1/collections/acme/books/reindex"),
        ("GET", "/v1/collections/acme/books/reindex/j1"),
        ("DELETE", "/v1/collections/acme/books/reindex/j1"),
        ("POST", "/v1/admin/reindex/j1/pause"),
        ("POST", "/v1/admin/reindex/j1/resume"),
    ]


def test_tenant_provisioning_contract_preserves_null_limits():
    seen = []

    def handler(request):
        seen.append((request.method, request.url.raw_path.decode(),
                     json.loads(request.content) if request.content else None))
        return httpx.Response(200, json={"ok": True})

    with _client(handler) as client:
        client.create_tenant("acme", limits={"max_rpm": 0}, create_key=False)
        client.get_tenant("acme")
        client.update_tenant("acme", limits={"max_rpm": None})
        client.create_tenant_key("acme", label="rotation")
        client.list_tenant_keys("acme")
        client.revoke_tenant_key("acme", "key/id")
        client.delete_tenant("acme")
    assert [(m, p) for m, p, _ in seen] == [
        ("POST", "/v1/admin/tenants"),
        ("GET", "/v1/admin/tenants/acme"),
        ("PATCH", "/v1/admin/tenants/acme"),
        ("POST", "/v1/admin/tenants/acme/keys"),
        ("GET", "/v1/admin/tenants/acme/keys"),
        ("DELETE", "/v1/admin/tenants/acme/keys/key%2Fid"),
        ("DELETE", "/v1/admin/tenants/acme"),
    ]
    assert seen[0][2] == {
        "tenant": "acme", "limits": {"max_rpm": 0}, "create_key": False,
    }
    assert seen[2][2] == {"limits": {"max_rpm": None}}
    assert seen[3][2] == {"label": "rotation"}
