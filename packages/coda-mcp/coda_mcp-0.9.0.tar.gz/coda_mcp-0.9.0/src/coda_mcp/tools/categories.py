# src/coda_mcp/tools/categories.py
"""Category-level Coda API operations for Gallery discovery (v0.7.0)."""
from __future__ import annotations

from coda_mcp.coda_client import coda_request
from coda_mcp.logging import get_logger

log = get_logger("coda_mcp.tools.categories")


async def list_coda_categories() -> dict:
    """
    List all available Coda Gallery categories.

    Returns:
        Dictionary with 'categories' list containing name, slug, description
    """
    try:
        log.info("Listing Coda Gallery categories")

        result = await coda_request("GET", "categories")

        category_count = len(result.get("items", []))
        log.info(f"Found {category_count} categories")

        return {
            "success": True,
            "categories": result.get("items", []),
            "href": result.get("href")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to list categories: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def get_coda_category(category_slug: str) -> dict:
    """
    Get detailed information about a specific Coda Gallery category.

    Args:
        category_slug: Category slug (e.g., "project-management")

    Returns:
        Category object with name, slug, description, docCount, href
    """
    try:
        log.info(f"Getting category: {category_slug}")

        result = await coda_request("GET", "categories", category_slug)

        log.info(f"Retrieved category: {result.get('name')}")

        return {
            "success": True,
            "name": result.get("name"),
            "slug": result.get("slug"),
            "description": result.get("description"),
            "docCount": result.get("docCount", 0),
            "href": result.get("href")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to get category: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}
