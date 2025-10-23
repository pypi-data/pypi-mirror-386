"""Coda Webhook Management Tools.

Provides tools for managing webhook subscriptions to receive real-time
event notifications when changes occur in Coda documents.

Event Types:
- rowAdded: Triggered when a new row is created
- rowUpdated: Triggered when an existing row is modified
- rowDeleted: Triggered when a row is removed

Tools:
- list_coda_webhooks: List all webhooks for a document
- create_coda_webhook: Create a new webhook subscription
- get_coda_webhook: Get webhook details by ID
- delete_coda_webhook: Delete a webhook subscription
"""

from coda_mcp.coda_client import coda_request
from coda_mcp.logging import get_logger

log = get_logger("coda_mcp.tools.webhooks")

# Valid webhook event types
VALID_EVENT_TYPES = frozenset(["rowAdded", "rowUpdated", "rowDeleted"])


async def list_coda_webhooks(
    doc_id: str,
    limit: int = 100,
    page_token: str | None = None
) -> dict:
    """List all webhook subscriptions for a document.

    Args:
        doc_id: Document ID (format: doc-*)
        limit: Maximum results per page (default: 100)
        page_token: Token for pagination

    Returns:
        Dictionary with webhooks list and pagination info
    """
    try:
        log.info(f"Listing webhooks for document: {doc_id}")

        params = {"limit": limit}
        if page_token:
            params["pageToken"] = page_token

        result = await coda_request("GET", "docs", doc_id, "webhooks", params=params)

        webhook_count = len(result.get("items", []))
        log.info(f"Found {webhook_count} webhooks for doc {doc_id}")

        return {
            "success": True,
            "items": result.get("items", []),
            "nextPageToken": result.get("nextPageToken"),
            "href": result.get("href")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to list webhooks: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def create_coda_webhook(
    doc_id: str,
    endpoint: str,
    event_types: list[str],
    table_id: str | None = None
) -> dict:
    """Create a new webhook subscription.

    Args:
        doc_id: Document ID (format: doc-*)
        endpoint: HTTPS URL to receive webhook events
        event_types: List of event types (rowAdded, rowUpdated, rowDeleted)
        table_id: Optional table ID to watch specific table

    Returns:
        Dictionary with created webhook details
    """
    try:
        log.info(f"Creating webhook for document: {doc_id}")

        # Validate endpoint is HTTPS
        if not endpoint.startswith("https://"):
            log.error(f"Invalid endpoint (must be HTTPS): {endpoint}")
            return {
                "success": False,
                "error": "Endpoint must use HTTPS protocol"
            }

        # Validate event types
        invalid_types = [et for et in event_types if et not in VALID_EVENT_TYPES]
        if invalid_types:
            log.error(f"Invalid event types: {invalid_types}")
            return {
                "success": False,
                "error": f"Invalid event types: {', '.join(invalid_types)}. "
                        f"Valid types: {', '.join(sorted(VALID_EVENT_TYPES))}"
            }

        if not event_types:
            log.error("No event types specified")
            return {
                "success": False,
                "error": "At least one event type must be specified"
            }

        # Build request payload
        payload = {
            "endpoint": endpoint,
            "eventTypes": event_types
        }

        if table_id:
            payload["tableId"] = table_id
            log.info(f"  Scoped to table: {table_id}")

        log.info(f"  Endpoint: {endpoint}")
        log.info(f"  Event types: {', '.join(event_types)}")

        result = await coda_request(
            "POST",
            "docs", doc_id, "webhooks",
            json=payload
        )

        webhook_id = result.get("id")
        log.info(f"Webhook created: {webhook_id}")

        return {
            "success": True,
            "id": result.get("id"),
            "endpoint": result.get("endpoint"),
            "eventTypes": result.get("eventTypes", []),
            "tableId": result.get("tableId"),
            "createdAt": result.get("createdAt"),
            "href": result.get("href")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to create webhook: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def get_coda_webhook(
    doc_id: str,
    webhook_id: str
) -> dict:
    """Get detailed information about a specific webhook.

    Args:
        doc_id: Document ID (format: doc-*)
        webhook_id: Webhook ID (format: webhook-*)

    Returns:
        Dictionary with webhook details
    """
    try:
        log.info(f"Getting webhook: {webhook_id} from doc {doc_id}")

        result = await coda_request("GET", "docs", doc_id, "webhooks", webhook_id)

        log.info(f"Retrieved webhook: {webhook_id}")

        return {
            "success": True,
            "id": result.get("id"),
            "endpoint": result.get("endpoint"),
            "eventTypes": result.get("eventTypes", []),
            "tableId": result.get("tableId"),
            "createdAt": result.get("createdAt"),
            "lastEventAt": result.get("lastEventAt"),
            "eventCount": result.get("eventCount", 0),
            "href": result.get("href")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to get webhook: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def delete_coda_webhook(
    doc_id: str,
    webhook_id: str
) -> dict:
    """Delete a webhook subscription.

    Args:
        doc_id: Document ID (format: doc-*)
        webhook_id: Webhook ID to delete (format: webhook-*)

    Returns:
        Dictionary with deletion success status
    """
    try:
        log.info(f"Deleting webhook: {webhook_id} from doc {doc_id}")

        await coda_request("DELETE", "docs", doc_id, "webhooks", webhook_id)

        log.info(f"Webhook deleted: {webhook_id}")

        return {
            "success": True,
            "id": webhook_id
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to delete webhook: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}
