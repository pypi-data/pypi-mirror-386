# src/coda_mcp/tools/pages.py
"""Page-level Coda API operations."""
from __future__ import annotations

from coda_mcp.coda_client import coda_request
from coda_mcp.logging import get_logger

log = get_logger("coda_mcp.tools.pages")


async def list_coda_pages(
    doc_id: str,
    limit: int = 25,
    page_token: str | None = None
) -> dict:
    """
    List all pages in a document.

    Args:
        doc_id: ID of the document
        limit: Maximum results to return (default 25)
        page_token: Token for pagination

    Returns:
        Dictionary with 'pages' list and pagination info
    """
    try:
        log.info(f"Listing pages in document: {doc_id}")

        params = {"limit": limit}
        if page_token:
            params["pageToken"] = page_token

        result = await coda_request("GET", "docs", doc_id, "pages", params=params)

        page_count = len(result.get("items", []))
        log.info(f"Found {page_count} pages in doc {doc_id}")

        return {
            "success": True,
            "pages": result.get("items", []),
            "href": result.get("href"),
            "nextPageToken": result.get("nextPageToken"),
            "nextPageLink": result.get("nextPageLink"),
            "next_page_token": result.get("nextPageToken")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to list pages: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def get_coda_page(
    doc_id: str,
    page_id_or_name: str
) -> dict:
    """
    Get detailed information about a page.

    Args:
        doc_id: ID of the document
        page_id_or_name: ID or name of the page

    Returns:
        Page metadata including content type, parent, etc.
    """
    try:
        log.info(f"Getting page {page_id_or_name} from doc {doc_id}")

        result = await coda_request("GET", "docs", doc_id, "pages", page_id_or_name)

        log.info(f"Retrieved page: {result.get('name')}")

        return {
            "success": True,
            "id": result.get("id"),
            "type": result.get("type"),
            "href": result.get("href"),
            "browserLink": result.get("browserLink"),
            "name": result.get("name"),
            "subtitle": result.get("subtitle"),
            "icon": result.get("icon"),
            "image": result.get("image"),
            "contentType": result.get("contentType"),
            "isHidden": result.get("isHidden"),
            "parent": result.get("parent"),
            "children": result.get("children"),
            "createdAt": result.get("createdAt"),
            "updatedAt": result.get("updatedAt")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to get page: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def create_coda_page(
    doc_id: str,
    name: str,
    subtitle: str | None = None,
    icon_name: str | None = None,
    parent_page_id_or_name: str | None = None,
    page_content: str | None = None
) -> dict:
    """
    Create a new page in a document (asynchronous operation).

    Args:
        doc_id: ID of the document
        name: Name of the new page
        subtitle: Optional subtitle for the page
        icon_name: Optional icon name
        parent_page_id_or_name: Optional parent page (for subpages)
        page_content: Optional initial content for the page

    Returns:
        Request ID and page ID

    Note:
        This is an asynchronous operation. The page may not be immediately
        available for querying or updating after this call returns.

        To ensure the page is ready:
        1. Wait 1-2 seconds before accessing the page, OR
        2. Use the returned requestId with get_coda_mutation_status() to poll
           for completion status

        Without waiting, subsequent operations may receive 404 errors.
    """
    try:
        log.info(f"Creating page '{name}' in doc {doc_id}")

        page_data = {
            "name": name,
            "contentType": "canvas"
        }

        if subtitle:
            page_data["subtitle"] = subtitle
        if icon_name:
            page_data["iconName"] = icon_name
        if parent_page_id_or_name:
            page_data["parentPageIdOrName"] = parent_page_id_or_name
        if page_content:
            page_data["pageContent"] = {"type": "canvas", "canvasContent": page_content}

        result = await coda_request("POST", "docs", doc_id, "pages", json=page_data)

        log.info(f"Page created with ID: {result.get('id')}")

        return {
            "success": True,
            "id": result.get("id"),
            "requestId": result.get("requestId"),
            "browserLink": result.get("browserLink")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to create page: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def wait_for_page_availability(
    doc_id: str,
    page_id: str,
    max_wait_seconds: int = 10,
    poll_interval: float = 0.5
) -> bool:
    """
    Poll until a newly created page becomes available.

    Args:
        doc_id: ID of the document
        page_id: ID of the page to wait for
        max_wait_seconds: Maximum time to wait (default: 10 seconds)
        poll_interval: Time between polls in seconds (default: 0.5 seconds)

    Returns:
        True if page becomes available, False if timeout

    Note:
        This is a utility function for handling the asynchronous nature of
        create_coda_page(). After creating a page, call this function to
        ensure the page is ready before attempting to access or modify it.

    Example:
        result = await create_coda_page(doc_id, "My Page")
        page_id = result.get("id")
        if await wait_for_page_availability(doc_id, page_id):
            # Now safe to update or query the page
            await update_coda_page_content(doc_id, page_id, "# Content")
    """
    import asyncio
    import time

    try:
        log.info(f"Waiting for page {page_id} to become available...")
        start_time = time.time()
        elapsed = 0

        while elapsed < max_wait_seconds:
            # Try to get the page
            result = await get_coda_page(doc_id, page_id)

            # If successful, page is available
            if result.get("success"):
                log.info(f"Page {page_id} available after {elapsed:.2f}s")
                return True

            # Wait before next attempt
            await asyncio.sleep(poll_interval)
            elapsed = time.time() - start_time

        log.warning(f"Page {page_id} not available after {max_wait_seconds}s")
        return False

    except Exception as e:
        log.error(f"Error waiting for page availability: {e}", exc_info=True)
        return False


async def update_coda_page(
    doc_id: str,
    page_id_or_name: str,
    name: str | None = None,
    subtitle: str | None = None,
    icon_name: str | None = None,
    is_hidden: bool | None = None
) -> dict:
    """
    Update page properties.

    Args:
        doc_id: ID of the document
        page_id_or_name: ID or name of the page
        name: New name for the page
        subtitle: New subtitle
        icon_name: New icon name
        is_hidden: Whether page should be hidden

    Returns:
        Request ID for tracking mutation status
    """
    try:
        log.info(f"Updating page {page_id_or_name} in doc {doc_id}")

        update_data = {}
        if name is not None:
            update_data["name"] = name
        if subtitle is not None:
            update_data["subtitle"] = subtitle
        if icon_name is not None:
            update_data["iconName"] = icon_name
        if is_hidden is not None:
            update_data["isHidden"] = is_hidden

        if not update_data:
            return {"success": False, "error": "No update parameters provided"}

        result = await coda_request(
            "PUT", "docs", doc_id, "pages", page_id_or_name,
            json=update_data
        )

        log.info(f"Page updated with request ID: {result.get('requestId')}")

        return {
            "success": True,
            "requestId": result.get("requestId")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to update page: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def delete_coda_page(
    doc_id: str,
    page_id_or_name: str
) -> dict:
    """
    Delete a page from a document.

    Args:
        doc_id: ID of the document
        page_id_or_name: ID or name of the page to delete

    Returns:
        Success status
    """
    try:
        log.info(f"Deleting page {page_id_or_name} from doc {doc_id}")

        await coda_request("DELETE", "docs", doc_id, "pages", page_id_or_name)

        log.info(f"Page {page_id_or_name} deleted successfully")

        return {"success": True}

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to delete page: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def update_coda_page_content(
    doc_id: str,
    page_id_or_name: str,
    content: str,
    content_format: str = "markdown",
    insert_mode: str = "replace"
) -> dict:
    """
    Update the canvas content of an existing page.

    Args:
        doc_id: ID of the document
        page_id_or_name: ID or name of the page
        content: Content to write (HTML or Markdown)
        content_format: Format of content ("html" or "markdown", default: "markdown")
        insert_mode: How to insert content ("replace" or "append", default: "replace")

    Returns:
        Request ID for tracking mutation status

    Note:
        This operation updates page canvas content, not metadata.
        Use update_coda_page() for metadata changes (name, subtitle, icon, hidden).
        Content format conversion may lose some Coda-specific features.
    """
    try:
        log.info(f"Updating content for page {page_id_or_name} in doc {doc_id}")

        if content_format not in ["html", "markdown"]:
            return {"success": False, "error": "content_format must be 'html' or 'markdown'"}

        if insert_mode not in ["replace", "append"]:
            return {"success": False, "error": "insert_mode must be 'replace' or 'append'"}

        update_data = {
            "contentUpdate": {
                "insertionMode": insert_mode,
                "canvasContent": {
                    "format": content_format,
                    "content": content
                }
            }
        }

        result = await coda_request(
            "PUT", "docs", doc_id, "pages", page_id_or_name,
            json=update_data
        )

        log.info(f"Page content updated with request ID: {result.get('requestId')}")

        return {
            "success": True,
            "requestId": result.get("requestId")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to update page content: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def get_coda_page_content(
    doc_id: str,
    page_id_or_name: str,
    output_format: str = "markdown"
) -> dict:
    """
    Retrieve the canvas content of a page.

    Args:
        doc_id: ID of the document
        page_id_or_name: ID or name of the page
        output_format: Desired output format ("html" or "markdown", default: "markdown")

    Returns:
        Page content in the requested format

    Note:
        This retrieves the actual canvas content, not just metadata.
        Use get_coda_page() for metadata only.
        Export is asynchronous - may require polling for completion.
    """
    try:
        log.info(f"Getting content for page {page_id_or_name} from doc {doc_id}")

        if output_format not in ["html", "markdown"]:
            return {"success": False, "error": "output_format must be 'html' or 'markdown'"}

        # Initiate export
        export_request = await coda_request(
            "POST", "docs", doc_id, "pages", page_id_or_name, "export",
            json={"outputFormat": output_format}
        )

        request_id = export_request.get("id")
        download_link = export_request.get("downloadLink")
        status = export_request.get("status")

        log.info(f"Page export initiated with request ID: {request_id}, status: {status}")

        return {
            "success": True,
            "requestId": request_id,
            "downloadLink": download_link,
            "status": status,
            "outputFormat": output_format
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to get page content: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def export_coda_page(
    doc_id: str,
    page_id_or_name: str,
    output_format: str = "markdown"
) -> dict:
    """
    Export a page to HTML or Markdown format (asynchronous operation).

    Args:
        doc_id: ID of the document
        page_id_or_name: ID or name of the page
        output_format: Export format ("html" or "markdown", default: "markdown")

    Returns:
        Export request details including request ID and download link (when ready)

    Note:
        This is an asynchronous operation. The response includes a requestId
        that can be used with get_coda_mutation_status() to check completion status.
        Once complete, the downloadLink will be available to fetch the content.
    """
    try:
        log.info(f"Exporting page {page_id_or_name} from doc {doc_id} to {output_format}")

        if output_format not in ["html", "markdown"]:
            return {"success": False, "error": "output_format must be 'html' or 'markdown'"}

        result = await coda_request(
            "POST", "docs", doc_id, "pages", page_id_or_name, "export",
            json={"outputFormat": output_format}
        )

        request_id = result.get("id")
        download_link = result.get("downloadLink")
        status = result.get("status")

        log.info(f"Page export requested: ID={request_id}, status={status}")

        return {
            "success": True,
            "requestId": request_id,
            "downloadLink": download_link,
            "status": status,
            "outputFormat": output_format,
            "href": result.get("href")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to export page: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}
