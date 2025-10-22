# src/coda_mcp/tools/automations.py
"""Automation and mutation tracking operations."""
from __future__ import annotations

from typing import Any

from coda_mcp.coda_client import coda_request
from coda_mcp.logging import get_logger

log = get_logger("coda_mcp.tools.automations")


async def push_coda_button(
    doc_id: str,
    table_id_or_name: str,
    row_id_or_name: str,
    column_id_or_name: str
) -> dict:
    """
    Push a button in a table row.

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        row_id_or_name: ID or name of the row
        column_id_or_name: ID or name of the button column

    Returns:
        Request ID, row ID, and column ID
    """
    try:
        log.info(f"Pushing button {column_id_or_name} in row {row_id_or_name}")

        result = await coda_request(
            "POST",
            "docs", doc_id,
            "tables", table_id_or_name,
            "rows", row_id_or_name,
            "buttons", column_id_or_name
        )

        log.info(f"Button pushed with request ID: {result.get('requestId')}")

        return {
            "success": True,
            "requestId": result.get("requestId"),
            "rowId": result.get("rowId"),
            "columnId": result.get("columnId")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to push button: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def trigger_coda_automation(
    doc_id: str,
    rule_id: str,
    payload: dict[str, Any]
) -> dict:
    """
    Trigger a webhook-invoked automation rule.

    Args:
        doc_id: ID of the document
        rule_id: ID of the automation rule
        payload: Data to send with the automation trigger

    Returns:
        Request ID for the automation trigger
    """
    try:
        log.info(f"Triggering automation {rule_id} in doc {doc_id}")

        result = await coda_request(
            "POST",
            "docs", doc_id,
            "hooks", "automation", rule_id,
            json=payload
        )

        log.info(f"Automation triggered with request ID: {result.get('requestId')}")

        return {
            "success": True,
            "requestId": result.get("requestId")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to trigger automation: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def list_coda_automations(
    doc_id: str,
    limit: int = 100,
    page_token: str | None = None
) -> dict:
    """
    List automation rules configured in a document.

    Args:
        doc_id: ID of the document
        limit: Maximum number of automations to return (default 100)
        page_token: Token for pagination

    Returns:
        Dictionary with automations list and pagination info
    """
    try:
        log.info(f"Listing automations in document: {doc_id}")

        params = {"limit": limit}
        if page_token:
            params["pageToken"] = page_token

        result = await coda_request("GET", "docs", doc_id, "automations", params=params)

        automation_count = len(result.get("items", []))
        log.info(f"Found {automation_count} automations in doc {doc_id}")

        return {
            "success": True,
            "automations": result.get("items", []),
            "href": result.get("href"),
            "next_page_token": result.get("nextPageToken"),
            "nextPageToken": result.get("nextPageToken"),
            "next_page_link": result.get("nextPageLink"),
            "nextPageLink": result.get("nextPageLink")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to list automations: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def get_mutation_status(
    request_id: str
) -> dict:
    """
    Check the status of an asynchronous mutation.

    Args:
        request_id: ID of the mutation request

    Returns:
        Completion status and optional warning message
    """
    try:
        log.info(f"Checking mutation status for request: {request_id}")

        result = await coda_request("GET", "mutationStatus", request_id)

        completed = result.get("completed", False)
        log.info(f"Mutation {request_id} completed: {completed}")

        return {
            "success": True,
            "completed": result.get("completed"),
            "warning": result.get("warning")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to get mutation status: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}
