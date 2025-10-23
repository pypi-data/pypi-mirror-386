# src/coda_mcp/tools/formulas.py
"""Formula-level Coda API operations (v0.6.0)."""
from __future__ import annotations

from coda_mcp.coda_client import coda_request
from coda_mcp.logging import get_logger

log = get_logger("coda_mcp.tools.formulas")


async def list_coda_formulas(
    doc_id: str,
    limit: int = 25,
    page_token: str | None = None
) -> dict:
    """
    List all formulas in a document.

    Args:
        doc_id: ID of the document
        limit: Maximum results to return (default 25, max 100)
        page_token: Token for pagination

    Returns:
        Dictionary with 'formulas' list and pagination info
    """
    try:
        log.info(f"Listing formulas in document: {doc_id}")

        # Cap limit at 100 (Coda API max)
        effective_limit = min(limit, 100)

        params = {"limit": effective_limit}
        if page_token:
            params["pageToken"] = page_token

        result = await coda_request("GET", "docs", doc_id, "formulas", params=params)

        formula_count = len(result.get("items", []))
        log.info(f"Found {formula_count} formulas in doc {doc_id}")

        return {
            "success": True,
            "formulas": result.get("items", []),
            "href": result.get("href"),
            "nextPageToken": result.get("nextPageToken"),
            "nextPageLink": result.get("nextPageLink"),
            "next_page_token": result.get("nextPageToken")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to list formulas: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def get_coda_formula(
    doc_id: str,
    formula_id_or_name: str
) -> dict:
    """
    Get detailed information about a specific formula.

    Args:
        doc_id: ID of the document
        formula_id_or_name: ID (format: formula-*) or name of the formula

    Returns:
        Formula object with id, name, formula expression, parent, etc.
    """
    try:
        log.info(f"Getting formula {formula_id_or_name} from doc {doc_id}")

        result = await coda_request("GET", "docs", doc_id, "formulas", formula_id_or_name)

        log.info(f"Retrieved formula: {result.get('name')}")

        return {
            "success": True,
            "id": result.get("id"),
            "name": result.get("name"),
            "formula": result.get("formula"),
            "type": result.get("type"),
            "parent": result.get("parent"),
            "browserLink": result.get("browserLink"),
            "href": result.get("href")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to get formula: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}
