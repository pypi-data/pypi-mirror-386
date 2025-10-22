# src/coda_mcp/tools/analytics.py
"""Analytics-level Coda API operations for usage metrics (v0.7.0)."""
from __future__ import annotations

from datetime import datetime, timedelta

from coda_mcp.coda_client import coda_request
from coda_mcp.logging import get_logger

log = get_logger("coda_mcp.tools.analytics")


async def get_coda_doc_analytics(
    doc_id: str,
    start_date: str | None = None,
    end_date: str | None = None
) -> dict:
    """
    Get analytics for a specific document.

    Args:
        doc_id: ID of the document
        start_date: Start date for analytics period (ISO format: YYYY-MM-DD)
        end_date: End date for analytics period (ISO format: YYYY-MM-DD)

    Returns:
        Dictionary with analytics metrics (sessions, views, edits, users)
    """
    try:
        log.info(f"Getting analytics for document: {doc_id}")

        # Default to last 30 days if not specified
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        params = {
            "startDate": start_date,
            "endDate": end_date
        }

        result = await coda_request("GET", "docs", doc_id, "analytics", params=params)

        log.info(f"Retrieved analytics for doc {doc_id}: {result.get('totalSessions', 0)} sessions")

        return {
            "success": True,
            "doc_id": doc_id,
            "totalSessions": result.get("totalSessions", 0),
            "totalViews": result.get("totalViews", 0),
            "totalEdits": result.get("totalEdits", 0),
            "uniqueUsers": result.get("uniqueUsers", 0),
            "period": {
                "start": start_date,
                "end": end_date
            }
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to get document analytics: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def list_coda_doc_analytics_summary(
    start_date: str | None = None,
    end_date: str | None = None
) -> dict:
    """
    Get analytics summary across all accessible documents.

    Args:
        start_date: Start date for analytics period (ISO format: YYYY-MM-DD)
        end_date: End date for analytics period (ISO format: YYYY-MM-DD)

    Returns:
        Dictionary with aggregated analytics metrics
    """
    try:
        log.info("Getting analytics summary across all documents")

        # Default to last 30 days if not specified
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        params = {
            "startDate": start_date,
            "endDate": end_date
        }

        result = await coda_request("GET", "analytics", "docs", "summary", params=params)

        log.info(f"Retrieved analytics summary: {result.get('totalDocs', 0)} documents")

        return {
            "success": True,
            "totalDocs": result.get("totalDocs", 0),
            "totalSessions": result.get("totalSessions", 0),
            "totalViews": result.get("totalViews", 0),
            "totalEdits": result.get("totalEdits", 0),
            "uniqueUsers": result.get("uniqueUsers", 0),
            "period": {
                "start": start_date,
                "end": end_date
            }
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to get analytics summary: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}
