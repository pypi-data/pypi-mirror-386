# src/coda_mcp/tools/tables.py
"""Table-level Coda API operations."""
from __future__ import annotations

from typing import Any

from coda_mcp.coda_client import coda_request
from coda_mcp.logging import get_logger

log = get_logger("coda_mcp.tools.tables")


async def list_coda_tables(
    doc_id: str,
    limit: int = 25,
    page_token: str | None = None,
    sort_by: str | None = None,
    table_types: list[str] | None = None
) -> dict:
    """
    List all tables in a document.

    Args:
        doc_id: ID of the document
        limit: Maximum results to return (default 25)
        page_token: Token for pagination
        sort_by: Sort order (name, createdAt, updatedAt)
        table_types: Filter by table types (table, view)

    Returns:
        Dictionary with 'items' list and pagination info
    """
    try:
        log.info(f"Listing tables in document: {doc_id}")

        params = {"limit": limit}

        if page_token:
            params["pageToken"] = page_token
        if sort_by:
            params["sortBy"] = sort_by
        if table_types:
            if isinstance(table_types, str):
                normalized_types = [t.strip() for t in table_types.split(",") if t.strip()]
            else:
                normalized_types = [str(t).strip() for t in table_types if str(t).strip()]
            if normalized_types:
                params["tableTypes"] = ",".join(normalized_types)

        result = await coda_request("GET", "docs", doc_id, "tables", params=params)

        table_count = len(result.get("items", []))
        log.info(f"Found {table_count} tables in doc {doc_id}")

        return {
            "success": True,
            "tables": result.get("items", []),
            "href": result.get("href"),
            "nextPageToken": result.get("nextPageToken"),
            "nextPageLink": result.get("nextPageLink"),
            "next_page_token": result.get("nextPageToken")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to list tables: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def get_coda_table(
    doc_id: str,
    table_id_or_name: str,
    use_updated_table_layouts: bool | None = None
) -> dict:
    """
    Get detailed information about a table.

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        use_updated_table_layouts: Use updated table layout format

    Returns:
        Table metadata including columns, display column, etc.
    """
    try:
        log.info(f"Getting table {table_id_or_name} from doc {doc_id}")

        params = {}
        if use_updated_table_layouts is not None:
            params["useUpdatedTableLayouts"] = str(bool(use_updated_table_layouts)).lower()

        result = await coda_request(
            "GET", "docs", doc_id, "tables", table_id_or_name,
            params=params if params else None
        )

        log.info(f"Retrieved table: {result.get('name')}")

        return {
            "success": True,
            "id": result.get("id"),
            "type": result.get("type"),
            "href": result.get("href"),
            "browserLink": result.get("browserLink"),
            "name": result.get("name"),
            "parent": result.get("parent"),
            "parentTable": result.get("parentTable"),
            "displayColumn": result.get("displayColumn"),
            "rowCount": result.get("rowCount"),
            "sorts": result.get("sorts"),
            "layout": result.get("layout"),
            "createdAt": result.get("createdAt"),
            "updatedAt": result.get("updatedAt"),
            "filter": result.get("filter")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to get table: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def list_coda_columns(
    doc_id: str,
    table_id_or_name: str,
    limit: int = 25,
    page_token: str | None = None,
    visible_only: bool = False
) -> dict:
    """
    List columns in a table.

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        limit: Maximum results to return (default 25)
        page_token: Token for pagination
        visible_only: Only return visible columns

    Returns:
        Dictionary with 'items' list and pagination info
    """
    try:
        log.info(f"Listing columns in table {table_id_or_name} from doc {doc_id}")

        params = {
            "limit": limit,
            "visibleOnly": str(visible_only).lower()
        }

        if page_token:
            params["pageToken"] = page_token

        result = await coda_request(
            "GET", "docs", doc_id, "tables", table_id_or_name, "columns",
            params=params
        )

        column_count = len(result.get("items", []))
        log.info(f"Found {column_count} columns")

        return {
            "success": True,
            "columns": result.get("items", []),
            "href": result.get("href"),
            "nextPageToken": result.get("nextPageToken"),
            "nextPageLink": result.get("nextPageLink"),
            "next_page_token": result.get("nextPageToken")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to list columns: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def get_coda_column(
    doc_id: str,
    table_id_or_name: str,
    column_id_or_name: str
) -> dict:
    """
    Get detailed information about a column.

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        column_id_or_name: ID or name of the column

    Returns:
        Column metadata including type, format, etc.
    """
    try:
        log.info(f"Getting column {column_id_or_name} from table {table_id_or_name}")

        result = await coda_request(
            "GET", "docs", doc_id, "tables", table_id_or_name, "columns", column_id_or_name
        )

        log.info(f"Retrieved column: {result.get('name')}")

        return {
            "success": True,
            "id": result.get("id"),
            "type": result.get("type"),
            "href": result.get("href"),
            "name": result.get("name"),
            "parent": result.get("parent"),
            "display": result.get("display"),
            "calculated": result.get("calculated"),
            "formula": result.get("formula"),
            "defaultValue": result.get("defaultValue"),
            "format": result.get("format")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to get column: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def create_coda_table(
    doc_id: str,
    name: str,
    columns: list[dict[str, Any]],
    rows: list[dict[str, Any]] | None = None,
    display_column: str | None = None
) -> dict:
    """
    Create a new table with a defined schema.

    Args:
        doc_id: ID of the document to create the table in
        name: Name for the new table
        columns: Column definitions: [{name, type, format?, default_value?, options?}]
        rows: Optional seed data: [{column_name: value, ...}]
        display_column: Name of column to use as display column

    Returns:
        Dictionary with success, table_id, browser_link, etc.
    """
    try:
        log.info(f"Creating table '{name}' in document: {doc_id}")

        # Build request body
        data: dict[str, Any] = {
            "name": name,
            "columns": columns
        }

        # Add optional parameters
        if rows is not None:
            data["rows"] = rows

        if display_column:
            # Find the column by name to get its ID/reference
            # For now, just pass the display column name
            # The API will handle resolving it
            data["displayColumn"] = display_column

        result = await coda_request("POST", "docs", doc_id, "tables", json=data)

        log.info(f"Table created: {result.get('id')}")

        return {
            "success": True,
            "table_id": result.get("id"),
            "id": result.get("id"),
            "browser_link": result.get("browserLink"),
            "browserLink": result.get("browserLink"),
            "request_id": result.get("requestId"),
            "requestId": result.get("requestId"),
            "name": result.get("name")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to create table: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}
