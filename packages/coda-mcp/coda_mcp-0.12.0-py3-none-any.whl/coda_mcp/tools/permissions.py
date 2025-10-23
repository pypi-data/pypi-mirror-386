# src/coda_mcp/tools/permissions.py
"""Permission and publishing operations."""
from __future__ import annotations

from typing import Any

from coda_mcp.coda_client import coda_request
from coda_mcp.logging import get_logger

log = get_logger("coda_mcp.tools.permissions")


async def list_coda_permissions(
    doc_id: str,
    limit: int = 25,
    page_token: str | None = None
) -> dict:
    """
    List permissions for a document.

    Args:
        doc_id: ID of the document
        limit: Maximum results to return (default 25)
        page_token: Token for pagination

    Returns:
        Dictionary with 'items' list of permissions and pagination info
    """
    try:
        log.info(f"Listing permissions for doc: {doc_id}")

        params = {"limit": limit}
        if page_token:
            params["pageToken"] = page_token

        result = await coda_request(
            "GET", "docs", doc_id, "acl", "permissions",
            params=params
        )

        permission_count = len(result.get("items", []))
        log.info(f"Found {permission_count} permissions for doc {doc_id}")

        return {
            "success": True,
            "permissions": result.get("items", []),
            "href": result.get("href"),
            "nextPageToken": result.get("nextPageToken"),
            "nextPageLink": result.get("nextPageLink"),
            "next_page_token": result.get("nextPageToken")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to list permissions: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def get_coda_permissions(
    doc_id: str
) -> dict:
    """
    Get the current authenticated user's access level for a document.

    Args:
        doc_id: ID of the document

    Returns:
        Dictionary with access level and owner status
    """
    try:
        log.info(f"Getting permissions for doc: {doc_id}")

        result = await coda_request(
            "GET", "docs", doc_id, "acl", "permissions", "metadata"
        )

        access = result.get("access", "none")
        is_owner = result.get("isOwner", False)

        log.info(f"User has {access} access to doc {doc_id}, isOwner: {is_owner}")

        return {
            "success": True,
            "access": access,
            "isOwner": is_owner,
            "is_owner": is_owner  # Both snake_case and camelCase for compatibility
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to get permissions: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def grant_coda_permission(
    doc_id: str,
    access: str,
    principal: dict[str, Any],
    suppress_email: bool = False
) -> dict:
    """
    Add a permission to a document.

    Args:
        doc_id: ID of the document
        access: Type of access (readonly, write, comment)
        principal: Metadata about the principal (e.g., {"email": "user@example.com", "type": "email"})
        suppress_email: Whether to suppress email notification

    Returns:
        Success status
    """
    try:
        log.info(f"Adding {access} permission for {principal.get('email')} to doc {doc_id}")

        permission_data = {
            "access": access,
            "principal": principal,
            "suppressEmail": suppress_email
        }

        result = await coda_request(
            "POST", "docs", doc_id, "acl", "permissions",
            json=permission_data
        )

        log.info("Permission added successfully")

        return {
            "success": True,
            "id": result.get("id"),
            "principal": result.get("principal"),
            "access": result.get("access")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to add permission: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def revoke_coda_permission(
    doc_id: str,
    permission_id: str
) -> dict:
    """
    Delete a permission from a document.

    Args:
        doc_id: ID of the document
        permission_id: ID of the permission to delete

    Returns:
        Success status
    """
    try:
        log.info(f"Deleting permission {permission_id} from doc {doc_id}")

        await coda_request(
            "DELETE", "docs", doc_id, "acl", "permissions", permission_id
        )

        log.info(f"Permission {permission_id} deleted successfully")

        return {"success": True}

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to delete permission: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def publish_coda_doc(
    doc_id: str,
    slug: str | None = None,
    discoverable: bool | None = None,
    earn_credit: bool | None = None,
    category_names: list[str] | None = None,
    mode: str | None = None
) -> dict:
    """
    Publish a document to the Coda gallery.

    Args:
        doc_id: ID of the document
        slug: URL slug for the published document
        discoverable: Whether the document is discoverable in gallery
        earn_credit: Whether to earn credit for new signups
        category_names: List of category names to apply
        mode: Interaction mode (view, play, edit)

    Returns:
        Request ID for tracking mutation status
    """
    try:
        log.info(f"Publishing doc {doc_id}")

        publish_data = {}
        if slug is not None:
            publish_data["slug"] = slug
        if discoverable is not None:
            publish_data["discoverable"] = discoverable
        if earn_credit is not None:
            publish_data["earnCredit"] = earn_credit
        if category_names is not None:
            publish_data["categoryNames"] = category_names
        if mode is not None:
            publish_data["mode"] = mode

        result = await coda_request(
            "PUT", "docs", doc_id, "publish",
            json=publish_data
        )

        log.info(f"Document published with request ID: {result.get('requestId')}")

        return {
            "success": True,
            "requestId": result.get("requestId")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to publish document: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def unpublish_coda_doc(
    doc_id: str
) -> dict:
    """
    Unpublish a document from the Coda gallery.

    Args:
        doc_id: ID of the document

    Returns:
        Success status
    """
    try:
        log.info(f"Unpublishing doc {doc_id}")

        await coda_request("DELETE", "docs", doc_id, "publish")

        log.info(f"Document {doc_id} unpublished successfully")

        return {"success": True}

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to unpublish document: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}
