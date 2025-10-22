import pytest

from coda_mcp import server
from coda_mcp.tools import tables as tables_module

pytestmark = pytest.mark.asyncio


async def test_list_coda_docs_passes_keyword_arguments(monkeypatch):
    captured = {}

    async def fake_list_coda_docs(**kwargs):
        captured["kwargs"] = kwargs
        return {"success": True}

    monkeypatch.setattr(server.documents, "list_coda_docs", fake_list_coda_docs)

    result = await server.list_coda_docs(
        is_owner=True,
        is_published=False,
        query="roadmap",
        source_doc="doc-123",
        is_starred=True,
        in_gallery=False,
        workspace_id="ws-1",
        folder_id="folder-1",
        limit=50,
        page_token="token-xyz",
    )

    assert result == {"success": True}
    assert captured["kwargs"] == {
        "is_owner": True,
        "is_published": False,
        "query": "roadmap",
        "source_doc": "doc-123",
        "is_starred": True,
        "in_gallery": False,
        "workspace_id": "ws-1",
        "folder_id": "folder-1",
        "limit": 50,
        "page_token": "token-xyz",
    }


async def test_list_coda_tables_normalizes_table_types_from_string(monkeypatch):
    captured_params = {}

    async def fake_coda_request(method, *path_segments, params=None, json=None):
        captured_params.update(params or {})
        return {"items": [], "href": None, "nextPageToken": None, "nextPageLink": None}

    monkeypatch.setattr(tables_module, "coda_request", fake_coda_request)

    await server.list_coda_tables(
        "doc-1",
        table_types="table, view",
        limit=10,
        sort_by="name",
    )

    assert captured_params.get("tableTypes") == "table,view"


async def test_list_coda_tables_normalizes_table_types_from_sequence(monkeypatch):
    captured_params = {}

    async def fake_coda_request(method, *path_segments, params=None, json=None):
        captured_params.update(params or {})
        return {"items": [], "href": None, "nextPageToken": None, "nextPageLink": None}

    monkeypatch.setattr(tables_module, "coda_request", fake_coda_request)

    await server.list_coda_tables(
        "doc-1",
        table_types=["table", "view"],
    )

    assert captured_params.get("tableTypes") == "table,view"


async def test_get_coda_table_supports_layout_flag_alias(monkeypatch):
    captured_params = []

    async def fake_coda_request(method, *path_segments, params=None, json=None):
        captured_params.append(dict(params or {}))
        return {"id": "tbl-1", "name": "Test"}

    monkeypatch.setattr(tables_module, "coda_request", fake_coda_request)

    await server.get_coda_table(
        "doc-1",
        "tbl",
        use_column_names=True,
    )
    await server.get_coda_table(
        "doc-1",
        "tbl",
        use_updated_table_layouts=False,
    )
    await server.get_coda_table(
        "doc-1",
        "tbl",
    )

    assert captured_params[0].get("useUpdatedTableLayouts") == "true"
    assert captured_params[1].get("useUpdatedTableLayouts") == "false"
    assert "useUpdatedTableLayouts" not in captured_params[2]
