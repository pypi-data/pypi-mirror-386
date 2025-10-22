# src/coda_mcp/tools/documents.py
"""Document-level Coda API operations."""
from __future__ import annotations

from typing import Any

from coda_mcp.coda_client import coda_request
from coda_mcp.logging import get_logger

log = get_logger("coda_mcp.tools.documents")


async def list_coda_docs(
    is_owner: bool | None = None,
    is_published: bool | None = None,
    query: str | None = None,
    source_doc: str | None = None,
    is_starred: bool | None = None,
    in_gallery: bool | None = None,
    workspace_id: str | None = None,
    folder_id: str | None = None,
    limit: int = 25,
    page_token: str | None = None
) -> dict:
    """
    List documents in Coda workspace with optional filters.

    Args:
        is_owner: Filter for docs owned by user
        is_published: Filter for published docs
        query: Search query string
        source_doc: Filter for docs copied from this doc
        is_starred: Filter for starred docs
        in_gallery: Filter for docs in gallery
        workspace_id: Filter by workspace
        folder_id: Filter by folder
        limit: Maximum results to return (default 25)
        page_token: Token for pagination

    Returns:
        Dictionary with 'items' list and pagination info
    """
    try:
        log.info("Listing Coda documents")

        params = {"limit": limit}

        if is_owner is not None:
            params["isOwner"] = str(is_owner).lower()
        if is_published is not None:
            params["isPublished"] = str(is_published).lower()
        if query:
            params["query"] = query
        if source_doc:
            params["sourceDoc"] = source_doc
        if is_starred is not None:
            params["isStarred"] = str(is_starred).lower()
        if in_gallery is not None:
            params["inGallery"] = str(in_gallery).lower()
        if workspace_id:
            params["workspaceId"] = workspace_id
        if folder_id:
            params["folderId"] = folder_id
        if page_token:
            params["pageToken"] = page_token

        result = await coda_request("GET", "docs", params=params)

        doc_count = len(result.get("items", []))
        log.info(f"Found {doc_count} documents")

        return {
            "success": True,
            "docs": result.get("items", []),
            "href": result.get("href"),
            "nextPageToken": result.get("nextPageToken"),
            "nextPageLink": result.get("nextPageLink"),
            "next_page_token": result.get("nextPageToken")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to list documents: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def get_coda_doc(doc_id: str) -> dict:
    """
    Get detailed information about a specific document.

    Args:
        doc_id: ID of the document

    Returns:
        Document metadata including name, owner, workspace, etc.
    """
    try:
        log.info(f"Getting info for document: {doc_id}")

        result = await coda_request("GET", "docs", doc_id)

        log.info(f"Retrieved doc: {result.get('name')}")

        return {
            "success": True,
            "id": result.get("id"),
            "type": result.get("type"),
            "href": result.get("href"),
            "browserLink": result.get("browserLink"),
            "name": result.get("name"),
            "owner": result.get("owner"),
            "ownerName": result.get("ownerName"),
            "createdAt": result.get("createdAt"),
            "updatedAt": result.get("updatedAt"),
            "workspace": result.get("workspace"),
            "workspaceId": result.get("workspaceId"),
            "folderId": result.get("folderId"),
            "icon": result.get("icon"),
            "docSize": result.get("docSize"),
            "sourceDoc": result.get("sourceDoc"),
            "published": result.get("published")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to get doc info: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def create_coda_document(
    title: str,
    folder_id: str | None = None,
    template_id: str | None = None,
    initial_page_content: str | None = None
) -> dict:
    """
    Create a new Coda document, optionally from a template.

    Args:
        title: Name for the new document
        folder_id: Folder to create document in
        template_id: Template document to copy from
        initial_page_content: Markdown content for initial page

    Returns:
        Dictionary with success, doc_id, browser_link, etc.
    """
    try:
        log.info(f"Creating new document: {title}")

        data: dict[str, Any] = {"title": title}

        if folder_id:
            data["folderId"] = folder_id
        if template_id:
            data["sourceDoc"] = template_id
        if initial_page_content:
            data["initialPage"] = {"content": initial_page_content}

        result = await coda_request("POST", "docs", json=data)

        log.info(f"Document created: {result.get('id')}")

        return {
            "success": True,
            "doc_id": result.get("id"),
            "id": result.get("id"),
            "browser_link": result.get("browserLink"),
            "browserLink": result.get("browserLink"),
            "workspace_id": result.get("workspaceId"),
            "workspaceId": result.get("workspaceId"),
            "request_id": result.get("requestId"),
            "requestId": result.get("requestId")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to create document: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def delete_coda_document(doc_id: str) -> dict:
    """
    Delete a document.

    Args:
        doc_id: ID of the document to delete

    Returns:
        Success confirmation
    """
    try:
        log.info(f"Deleting document: {doc_id}")

        await coda_request("DELETE", "docs", doc_id)

        log.info(f"Document deleted: {doc_id}")

        return {
            "success": True,
            "message": f"Document {doc_id} deleted successfully"
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to delete document: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def update_coda_document(doc_id: str, title: str | None = None, icon_name: str | None = None) -> dict:
    """
    Update document properties.

    Args:
        doc_id: ID of the document
        title: New title for the document
        icon_name: New icon name

    Returns:
        Updated document info
    """
    try:
        log.info(f"Updating document: {doc_id}")

        data: dict[str, Any] = {}
        if title:
            data["title"] = title
        if icon_name:
            data["iconName"] = icon_name

        if not data:
            return {"success": False, "error": "No update parameters provided"}

        result = await coda_request("PATCH", "docs", doc_id, json=data)

        log.info(f"Document updated: {doc_id}")

        return {
            "success": True,
            "id": result.get("id"),
            "name": result.get("name"),
            "updatedAt": result.get("updatedAt")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to update document: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}
