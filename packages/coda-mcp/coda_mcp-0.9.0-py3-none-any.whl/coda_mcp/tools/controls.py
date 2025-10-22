# src/coda_mcp/tools/controls.py
"""Control-level Coda API operations (v0.6.0)."""
from __future__ import annotations

from typing import Any

from coda_mcp.coda_client import coda_request
from coda_mcp.logging import get_logger

log = get_logger("coda_mcp.tools.controls")


async def list_coda_controls(
    doc_id: str,
    limit: int = 25,
    page_token: str | None = None,
    sort_by: str = "name"
) -> dict:
    """
    List all controls in a document.

    Args:
        doc_id: ID of the document
        limit: Maximum results to return (default 25, max 100)
        page_token: Token for pagination
        sort_by: Sort order - "name" or "createdAt"

    Returns:
        Dictionary with 'controls' list and pagination info
    """
    try:
        log.info(f"Listing controls in document: {doc_id}")

        # Cap limit at 100 (Coda API max)
        effective_limit = min(limit, 100)

        params = {"limit": effective_limit, "sortBy": sort_by}
        if page_token:
            params["pageToken"] = page_token

        result = await coda_request("GET", "docs", doc_id, "controls", params=params)

        control_count = len(result.get("items", []))
        log.info(f"Found {control_count} controls in doc {doc_id}")

        return {
            "success": True,
            "controls": result.get("items", []),
            "href": result.get("href"),
            "nextPageToken": result.get("nextPageToken"),
            "nextPageLink": result.get("nextPageLink"),
            "next_page_token": result.get("nextPageToken")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to list controls: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def get_coda_control(
    doc_id: str,
    control_id_or_name: str
) -> dict:
    """
    Get detailed information about a specific control.

    Args:
        doc_id: ID of the document
        control_id_or_name: ID (format: ctrl-*) or name of the control

    Returns:
        Control object with id, name, type, value, etc.
    """
    try:
        log.info(f"Getting control {control_id_or_name} from doc {doc_id}")

        result = await coda_request("GET", "docs", doc_id, "controls", control_id_or_name)

        log.info(f"Retrieved control: {result.get('name')} (type: {result.get('type')})")

        return {
            "success": True,
            "id": result.get("id"),
            "name": result.get("name"),
            "type": result.get("type"),
            "controlType": result.get("controlType"),
            "value": result.get("value"),
            "browserLink": result.get("browserLink"),
            "href": result.get("href")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to get control: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def list_coda_control_types() -> dict:
    """
    Get list of available control types supported by Coda API.

    This is a static list based on Coda API v1 documentation.

    Returns:
        Dictionary with 'control_types' array
    """
    log.info("Listing available control types")

    # Control types from Coda API v1 documentation
    control_types = [
        "button",
        "checkbox",
        "datePicker",
        "dateRangePicker",
        "dateTimePicker",
        "lookup",
        "multiselect",
        "scale",
        "select",
        "slider",
        "textbox",
        "timePicker"
    ]

    log.info(f"Returning {len(control_types)} control types")

    return {
        "success": True,
        "control_types": control_types
    }


async def create_coda_control(
    doc_id: str,
    name: str,
    control_type: str,
    initial_value: Any = None,
    options: list | None = None
) -> dict:
    """
    Create a new control in a Coda document.

    Args:
        doc_id: ID of the document
        name: Name of the control
        control_type: Type of control (button, slider, select, etc.)
        initial_value: Initial value for the control
        options: Options for select/multiselect controls

    Returns:
        Dictionary with success status and created control details
    """
    try:
        log.info(f"Creating {control_type} control '{name}' in doc {doc_id}")

        # Validate required options for select/multiselect
        if control_type in ["select", "multiselect"] and not options:
            error_msg = f"Control type '{control_type}' requires 'options' parameter"
            log.error(error_msg)
            return {"success": False, "error": error_msg}

        # Build control creation payload
        control_data = {
            "name": name,
            "controlType": control_type
        }

        if initial_value is not None:
            control_data["initialValue"] = initial_value

        if options:
            control_data["options"] = options

        result = await coda_request("POST", "docs", doc_id, "controls", json=control_data)

        log.info(f"Created control: {result.get('id')} - {result.get('name')}")

        return {
            "success": True,
            "id": result.get("id"),
            "name": result.get("name"),
            "type": result.get("type"),
            "controlType": result.get("controlType"),
            "value": result.get("value"),
            "browserLink": result.get("browserLink"),
            "href": result.get("href")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to create control: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def update_coda_control(
    doc_id: str,
    control_id_or_name: str,
    value: Any
) -> dict:
    """
    Update the value of an existing control.

    Args:
        doc_id: ID of the document
        control_id_or_name: ID (format: ctrl-*) or name of the control
        value: New value for the control

    Returns:
        Dictionary with success status and requestId for tracking
    """
    try:
        log.info(f"Updating control {control_id_or_name} in doc {doc_id}")

        update_data = {"value": value}

        result = await coda_request(
            "PUT", "docs", doc_id, "controls", control_id_or_name,
            json=update_data
        )

        log.info(f"Control updated (requestId: {result.get('requestId')})")

        return {
            "success": True,
            "requestId": result.get("requestId"),
            "message": "Control value updated successfully"
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to update control: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}
