# src/coda_mcp/tools/rows.py
"""Row-level Coda API operations."""
from __future__ import annotations

from typing import Any

from coda_mcp.coda_client import coda_request
from coda_mcp.logging import get_logger

log = get_logger("coda_mcp.tools.rows")


async def list_coda_rows(
    doc_id: str,
    table_id_or_name: str,
    query: str | None = None,
    sort_by: str | None = None,
    use_column_names: bool = False,
    value_format: str = "simple",
    visible_only: bool | None = None,
    limit: int = 25,
    page_token: str | None = None,
    sync_token: str | None = None
) -> dict:
    """
    List rows in a table with optional filtering and sorting.

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        query: Query to filter rows
        sort_by: Sort order (createdAt, natural, updatedAt)
        use_column_names: Use column names instead of IDs in response
        value_format: Value format (simple, simpleWithArrays, rich)
        visible_only: Only return visible rows
        limit: Maximum results to return (default 25)
        page_token: Token for pagination
        sync_token: Token for incremental sync

    Returns:
        Dictionary with 'items' list and pagination info
    """
    try:
        log.info(f"Listing rows in table {table_id_or_name} from doc {doc_id}")

        params = {
            "useColumnNames": str(use_column_names).lower(),
            "valueFormat": value_format,
            "limit": limit
        }

        if query:
            params["query"] = query
        if sort_by:
            params["sortBy"] = sort_by
        if visible_only is not None:
            params["visibleOnly"] = str(visible_only).lower()
        if page_token:
            params["pageToken"] = page_token
        if sync_token:
            params["syncToken"] = sync_token

        result = await coda_request(
            "GET", "docs", doc_id, "tables", table_id_or_name, "rows",
            params=params
        )

        row_count = len(result.get("items", []))
        log.info(f"Found {row_count} rows")

        return {
            "success": True,
            "rows": result.get("items", []),
            "href": result.get("href"),
            "nextPageToken": result.get("nextPageToken"),
            "nextPageLink": result.get("nextPageLink"),
            "nextSyncToken": result.get("nextSyncToken"),
            "next_page_token": result.get("nextPageToken")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to list rows: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def get_coda_row(
    doc_id: str,
    table_id_or_name: str,
    row_id_or_name: str,
    use_column_names: bool = False,
    value_format: str = "simple"
) -> dict:
    """
    Get a specific row from a table.

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        row_id_or_name: ID or name of the row
        use_column_names: Use column names instead of IDs in response
        value_format: Value format (simple, simpleWithArrays, rich)

    Returns:
        Row data with all column values
    """
    try:
        log.info(f"Getting row {row_id_or_name} from table {table_id_or_name}")

        params = {
            "useColumnNames": str(use_column_names).lower(),
            "valueFormat": value_format
        }

        result = await coda_request(
            "GET", "docs", doc_id, "tables", table_id_or_name, "rows", row_id_or_name,
            params=params
        )

        log.info(f"Retrieved row: {result.get('name')}")

        return {
            "success": True,
            "id": result.get("id"),
            "type": result.get("type"),
            "href": result.get("href"),
            "name": result.get("name"),
            "index": result.get("index"),
            "browserLink": result.get("browserLink"),
            "createdAt": result.get("createdAt"),
            "updatedAt": result.get("updatedAt"),
            "values": result.get("values"),
            "parent": result.get("parent")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to get row: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def create_coda_row(
    doc_id: str,
    table_id_or_name: str,
    row_data: dict[str, Any],
    key_columns: list | None = None,
    disable_parsing: bool = True
) -> dict:
    """
    Create a new row in a table (with optional upsert).

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        row_data: Dictionary of column names/IDs to values
        key_columns: List of columns for upsert matching
        disable_parsing: Disable automatic parsing of values

    Returns:
        Request ID and added row IDs
    """
    try:
        log.info(f"Creating row in table {table_id_or_name}")

        params = {"disableParsing": str(disable_parsing).lower()}

        # Build request body
        cells = [{"column": col, "value": val} for col, val in row_data.items()]
        data: dict[str, Any] = {"rows": [{"cells": cells}]}

        if key_columns:
            data["keyColumns"] = key_columns

        result = await coda_request(
            "POST", "docs", doc_id, "tables", table_id_or_name, "rows",
            params=params,
            json=data
        )

        log.info(f"Row created with request ID: {result.get('requestId')}")

        return {
            "success": True,
            "requestId": result.get("requestId"),
            "addedRowIds": result.get("addedRowIds", [])
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to create row: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def update_coda_row(
    doc_id: str,
    table_id_or_name: str,
    row_id_or_name: str,
    row_data: dict[str, Any],
    disable_parsing: bool = True
) -> dict:
    """
    Update an existing row in a table.

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        row_id_or_name: ID or name of the row
        row_data: Dictionary of column names/IDs to new values
        disable_parsing: Disable automatic parsing of values

    Returns:
        Request ID for tracking mutation status
    """
    try:
        log.info(f"Updating row {row_id_or_name} in table {table_id_or_name}")

        params = {"disableParsing": str(disable_parsing).lower()}

        # Build request body
        cells = [{"column": col, "value": val} for col, val in row_data.items()]
        data = {"row": {"cells": cells}}

        result = await coda_request(
            "PUT", "docs", doc_id, "tables", table_id_or_name, "rows", row_id_or_name,
            params=params,
            json=data
        )

        log.info(f"Row updated with request ID: {result.get('requestId')}")

        return {
            "success": True,
            "requestId": result.get("requestId")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to update row: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def delete_coda_row(
    doc_id: str,
    table_id_or_name: str,
    row_id_or_name: str
) -> dict:
    """
    Delete a row from a table.

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        row_id_or_name: ID or name of the row to delete

    Returns:
        Request ID for tracking mutation status
    """
    try:
        log.info(f"Deleting row {row_id_or_name} from table {table_id_or_name}")

        result = await coda_request(
            "DELETE", "docs", doc_id, "tables", table_id_or_name, "rows", row_id_or_name
        )

        log.info(f"Row deleted with request ID: {result.get('requestId')}")

        return {
            "success": True,
            "requestId": result.get("requestId")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to delete row: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def bulk_delete_coda_rows(
    doc_id: str,
    table_id_or_name: str,
    row_ids: list[str]
) -> dict:
    """
    Delete multiple rows from a table in a single request.

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        row_ids: List of row IDs to delete

    Returns:
        Request ID for tracking mutation status
    """
    try:
        log.info(f"Deleting {len(row_ids)} rows from table {table_id_or_name}")

        delete_data = {
            "rowIds": row_ids
        }

        result = await coda_request(
            "DELETE", "docs", doc_id, "tables", table_id_or_name, "rows",
            json=delete_data
        )

        log.info(f"Bulk delete completed with request ID: {result.get('requestId')}")

        return {
            "success": True,
            "requestId": result.get("requestId"),
            "rowsDeleted": len(row_ids)
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to delete rows: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}
