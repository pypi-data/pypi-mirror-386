# src/coda_mcp/server.py
from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from coda_mcp import __version__
from coda_mcp.logging import get_logger
from coda_mcp.tools import (
    account,
    analytics,
    automations,
    categories,
    controls,
    documents,
    formulas,
    pages,
    permissions,
    rows,
    tables,
    webhooks,
)

log = get_logger("coda_mcp.server")
_mcp = FastMCP("Coda MCP Server")

CODA_API_BASE = "https://coda.io/apis/v1"

def get_coda_api_key() -> str:
    """Get Coda API key from environment."""
    api_key = os.getenv("CODA_API_KEY")
    if not api_key:
        raise ValueError("CODA_API_KEY environment variable not set")
    return api_key

@_mcp.tool()
async def ping(message: str = "pong") -> dict:
    """Echo tool for connectivity testing."""
    log.debug(f"Ping called with: {message}")
    return {"success": True, "echo": message}

@_mcp.tool()
async def calculate(operation: str, a: float, b: float) -> dict:
    """Perform arithmetic operations.

    Args:
        operation: One of: add, subtract, multiply, divide
        a: First operand
        b: Second operand

    Returns:
        Result of the calculation or error message
    """
    log.info(f"Calculate: {operation}({a}, {b})")

    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else None,
    }

    if operation not in operations:
        log.warning(f"Unknown operation: {operation}")
        return {"success": False, "error": f"Unknown operation: {operation}"}

    result = operations[operation](a, b)

    if result is None:
        log.warning("Division by zero attempted")
        return {"success": False, "error": "Division by zero"}

    log.debug(f"Calculate result: {result}")
    return {"success": True, "result": result}

@_mcp.tool()
async def list_coda_folders(workspace_id: str = "") -> dict:
    """List folders in a Coda workspace.

    Args:
        workspace_id: Optional workspace ID to filter folders

    Returns:
        List of folders with their IDs and names
    """
    try:
        log.info(f"Listing Coda folders for workspace: {workspace_id or 'all'}")

        api_key = get_coda_api_key()

        url = f"{CODA_API_BASE}/folders"
        if workspace_id:
            url += f"?workspaceId={workspace_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                timeout=30.0
            )

            response.raise_for_status()
            result = response.json()

        folders = result.get("items", [])
        log.info(f"Found {len(folders)} folders")

        return {
            "success": True,
            "folders": [
                {
                    "id": f.get("id"),
                    "name": f.get("name"),
                    "workspace_id": f.get("workspaceId"),
                    "browser_link": f.get("browserLink")
                }
                for f in folders
            ]
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except httpx.HTTPStatusError as e:
        log.error(f"HTTP error listing folders: {e.response.status_code} - {e.response.text}")
        return {"success": False, "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
    except Exception as e:
        log.error(f"Failed to list folders: {e}", exc_info=True)
        return {"success": False, "error": f"Failed to list folders: {type(e).__name__}: {str(e)}"}

# Document Operations
@_mcp.tool()
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
    """List documents with optional filtering.

    Args:
        is_owner: Filter for docs owned by the user
        is_published: Filter for published docs
        query: Search query to filter results
        source_doc: Filter for docs copied from a source doc
        is_starred: Filter for starred docs
        in_gallery: Filter for gallery docs
        workspace_id: Filter by workspace ID
        folder_id: Filter by folder ID
        limit: Maximum results to return (default 25)
        page_token: Token for pagination

    Returns:
        Dictionary with 'items' list and pagination info
    """
    return await documents.list_coda_docs(
        is_owner=is_owner,
        is_published=is_published,
        query=query,
        source_doc=source_doc,
        is_starred=is_starred,
        in_gallery=in_gallery,
        workspace_id=workspace_id,
        folder_id=folder_id,
        limit=limit,
        page_token=page_token
    )

@_mcp.tool()
async def get_coda_doc(doc_id: str) -> dict:
    """Get metadata about a specific document.

    Args:
        doc_id: ID of the document

    Returns:
        Document metadata including title, owner, dates, etc.
    """
    return await documents.get_coda_doc(doc_id)

@_mcp.tool()
async def delete_coda_document(doc_id: str) -> dict:
    """Delete a document permanently.

    Args:
        doc_id: ID of the document to delete

    Returns:
        Success status
    """
    return await documents.delete_coda_document(doc_id)

@_mcp.tool()
async def update_coda_document(
    doc_id: str,
    title: str | None = None,
    icon_name: str | None = None
) -> dict:
    """Update document properties.

    Args:
        doc_id: ID of the document
        title: New title for the document
        icon_name: New icon name

    Returns:
        Request ID for tracking mutation status
    """
    return await documents.update_coda_document(doc_id, title, icon_name)

@_mcp.tool()
async def create_coda_document(
    title: str,
    folder_id: str | None = None,
    template_id: str | None = None,
    initial_page_content: str | None = None
) -> dict:
    """Create a new Coda document.

    Args:
        title: Name for the new document
        folder_id: Folder to create document in (optional)
        template_id: Template document to copy from (optional)
        initial_page_content: Markdown content for initial page (optional)

    Returns:
        Document creation result with doc_id and browser_link
    """
    return await documents.create_coda_document(
        title=title,
        folder_id=folder_id,
        template_id=template_id,
        initial_page_content=initial_page_content
    )

# Table Operations
@_mcp.tool()
async def list_coda_tables(
    doc_id: str,
    limit: int = 25,
    page_token: str | None = None,
    sort_by: str | None = None,
    table_types: list[str] | None = None
) -> dict:
    """List tables in a document.

    Args:
        doc_id: ID of the document
        limit: Maximum results to return (default 25)
        page_token: Token for pagination
        sort_by: Sort order (name, createdAt, updatedAt)
        table_types: Sequence or comma-separated string of table types (table, view)

    Returns:
        Dictionary with 'items' list and pagination info
    """
    normalized_table_types: list[str] | None = None
    if table_types:
        if isinstance(table_types, str):
            # Allow comma-separated string for legacy callers
            normalized_table_types = [t.strip() for t in table_types.split(",") if t.strip()]
        else:
            normalized_table_types = [str(t).strip() for t in table_types if str(t).strip()]
    return await tables.list_coda_tables(
        doc_id,
        limit,
        page_token,
        sort_by,
        normalized_table_types if normalized_table_types else None
    )

@_mcp.tool()
async def get_coda_table(
    doc_id: str,
    table_id_or_name: str,
    use_updated_table_layouts: bool | None = None,
    use_column_names: bool | None = None
) -> dict:
    """Get metadata about a specific table.

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        use_updated_table_layouts: Use updated layout format for response payload
        use_column_names: Deprecated alias for use_updated_table_layouts

    Returns:
        Table metadata including columns, layout info, etc.
    """
    resolved_layout_flag = use_updated_table_layouts
    if resolved_layout_flag is None and use_column_names is not None:
        resolved_layout_flag = use_column_names
    return await tables.get_coda_table(
        doc_id,
        table_id_or_name,
        use_updated_table_layouts=resolved_layout_flag
    )

@_mcp.tool()
async def list_coda_columns(
    doc_id: str,
    table_id_or_name: str,
    limit: int = 25,
    page_token: str | None = None
) -> dict:
    """List columns in a table.

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        limit: Maximum results to return (default 25)
        page_token: Token for pagination

    Returns:
        Dictionary with 'items' list and pagination info
    """
    return await tables.list_coda_columns(doc_id, table_id_or_name, limit, page_token)

@_mcp.tool()
async def get_coda_column(
    doc_id: str,
    table_id_or_name: str,
    column_id_or_name: str
) -> dict:
    """Get metadata about a specific column.

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        column_id_or_name: ID or name of the column

    Returns:
        Column metadata including type, format, formula, etc.
    """
    return await tables.get_coda_column(doc_id, table_id_or_name, column_id_or_name)

@_mcp.tool()
async def create_coda_table(
    doc_id: str,
    name: str,
    columns: list[dict[str, Any]],
    rows: list[dict[str, Any]] | None = None,
    display_column: str | None = None
) -> dict:
    """Create a new table with defined schema.

    Args:
        doc_id: ID of the document to create the table in
        name: Name for the new table
        columns: Column definitions: [{name, type, format?, default_value?, options?}]
        rows: Optional seed data: [{column_name: value, ...}]
        display_column: Name of column to use as display column

    Returns:
        Table creation result with table_id and browser_link
    """
    return await tables.create_coda_table(
        doc_id=doc_id,
        name=name,
        columns=columns,
        rows=rows,
        display_column=display_column
    )

# Row Operations
@_mcp.tool()
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
    """List rows in a table with optional filtering and sorting.

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        query: Query to filter rows
        sort_by: Sort order (createdAt, natural, updatedAt)
        use_column_names: Use column names instead of IDs
        value_format: Value format (simple, simpleWithArrays, rich)
        visible_only: Only return visible rows
        limit: Maximum results to return (default 25)
        page_token: Token for pagination
        sync_token: Token for incremental sync

    Returns:
        Dictionary with 'items' list and pagination info
    """
    return await rows.list_coda_rows(
        doc_id, table_id_or_name, query, sort_by, use_column_names,
        value_format, visible_only, limit, page_token, sync_token
    )

@_mcp.tool()
async def get_coda_row(
    doc_id: str,
    table_id_or_name: str,
    row_id_or_name: str,
    use_column_names: bool = False,
    value_format: str = "simple"
) -> dict:
    """Get a specific row from a table.

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        row_id_or_name: ID or name of the row
        use_column_names: Use column names instead of IDs
        value_format: Value format (simple, simpleWithArrays, rich)

    Returns:
        Row data with all column values
    """
    return await rows.get_coda_row(doc_id, table_id_or_name, row_id_or_name, use_column_names, value_format)

@_mcp.tool()
async def create_coda_row(
    doc_id: str,
    table_id_or_name: str,
    row_data: dict[str, Any],
    key_columns: list | None = None,
    disable_parsing: bool = True
) -> dict:
    """Create a new row in a table (with optional upsert).

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        row_data: Dictionary of column names/IDs to values
        key_columns: List of columns for upsert matching
        disable_parsing: Disable automatic parsing of values

    Returns:
        Request ID and added row IDs
    """
    return await rows.create_coda_row(doc_id, table_id_or_name, row_data, key_columns, disable_parsing)

@_mcp.tool()
async def update_coda_row(
    doc_id: str,
    table_id_or_name: str,
    row_id_or_name: str,
    row_data: dict[str, Any],
    disable_parsing: bool = True
) -> dict:
    """Update an existing row in a table.

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        row_id_or_name: ID or name of the row
        row_data: Dictionary of column names/IDs to new values
        disable_parsing: Disable automatic parsing of values

    Returns:
        Request ID for tracking mutation status
    """
    return await rows.update_coda_row(doc_id, table_id_or_name, row_id_or_name, row_data, disable_parsing)

@_mcp.tool()
async def delete_coda_row(
    doc_id: str,
    table_id_or_name: str,
    row_id_or_name: str
) -> dict:
    """Delete a row from a table.

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        row_id_or_name: ID or name of the row to delete

    Returns:
        Request ID for tracking mutation status
    """
    return await rows.delete_coda_row(doc_id, table_id_or_name, row_id_or_name)

@_mcp.tool()
async def bulk_delete_coda_rows(
    doc_id: str,
    table_id_or_name: str,
    row_ids: list
) -> dict:
    """Delete multiple rows from a table in a single request.

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        row_ids: List of row IDs to delete

    Returns:
        Request ID and count of rows deleted
    """
    return await rows.bulk_delete_coda_rows(doc_id, table_id_or_name, row_ids)

# Page Operations
@_mcp.tool()
async def list_coda_pages(
    doc_id: str,
    limit: int = 25,
    page_token: str | None = None
) -> dict:
    """List pages in a document.

    Args:
        doc_id: ID of the document
        limit: Maximum results to return (default 25)
        page_token: Token for pagination

    Returns:
        Dictionary with 'items' list and pagination info
    """
    return await pages.list_coda_pages(doc_id, limit, page_token)

@_mcp.tool()
async def get_coda_page(
    doc_id: str,
    page_id_or_name: str
) -> dict:
    """Get metadata about a specific page.

    Args:
        doc_id: ID of the document
        page_id_or_name: ID or name of the page

    Returns:
        Page metadata including content type, parent, children, etc.
    """
    return await pages.get_coda_page(doc_id, page_id_or_name)

@_mcp.tool()
async def create_coda_page(
    doc_id: str,
    name: str,
    subtitle: str | None = None,
    icon_name: str | None = None,
    parent_page_id_or_name: str | None = None,
    page_content: str | None = None
) -> dict:
    """Create a new page in a document.

    Args:
        doc_id: ID of the document
        name: Name of the new page
        subtitle: Optional subtitle for the page
        icon_name: Optional icon name
        parent_page_id_or_name: Optional parent page (for subpages)
        page_content: Optional initial content for the page

    Returns:
        Request ID and page ID
    """
    return await pages.create_coda_page(doc_id, name, subtitle, icon_name, parent_page_id_or_name, page_content)

@_mcp.tool()
async def update_coda_page(
    doc_id: str,
    page_id_or_name: str,
    name: str | None = None,
    subtitle: str | None = None,
    icon_name: str | None = None,
    is_hidden: bool | None = None
) -> dict:
    """Update page properties.

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
    return await pages.update_coda_page(doc_id, page_id_or_name, name, subtitle, icon_name, is_hidden)

@_mcp.tool()
async def delete_coda_page(
    doc_id: str,
    page_id_or_name: str
) -> dict:
    """Delete a page from a document.

    Args:
        doc_id: ID of the document
        page_id_or_name: ID or name of the page to delete

    Returns:
        Success status
    """
    return await pages.delete_coda_page(doc_id, page_id_or_name)

@_mcp.tool()
async def update_coda_page_content(
    doc_id: str,
    page_id_or_name: str,
    content: str,
    content_format: str = "markdown",
    insert_mode: str = "replace"
) -> dict:
    """Update the canvas content of an existing page.

    Args:
        doc_id: ID of the document
        page_id_or_name: ID or name of the page
        content: Content to write (HTML or Markdown)
        content_format: Format of content ("html" or "markdown", default: "markdown")
        insert_mode: How to insert content ("replace" or "append", default: "replace")

    Returns:
        Request ID for tracking mutation status

    Note:
        This updates page canvas content. For metadata (name, subtitle, icon),
        use update_coda_page() instead.
    """
    return await pages.update_coda_page_content(doc_id, page_id_or_name, content, content_format, insert_mode)

@_mcp.tool()
async def get_coda_page_content(
    doc_id: str,
    page_id_or_name: str,
    output_format: str = "markdown"
) -> dict:
    """Retrieve the canvas content of a page.

    Args:
        doc_id: ID of the document
        page_id_or_name: ID or name of the page
        output_format: Desired output format ("html" or "markdown", default: "markdown")

    Returns:
        Export request with status and download link

    Note:
        This retrieves actual canvas content, not just metadata.
        The operation is asynchronous - poll the requestId for completion.
    """
    return await pages.get_coda_page_content(doc_id, page_id_or_name, output_format)

@_mcp.tool()
async def export_coda_page(
    doc_id: str,
    page_id_or_name: str,
    output_format: str = "markdown"
) -> dict:
    """Export a page to HTML or Markdown format.

    Args:
        doc_id: ID of the document
        page_id_or_name: ID or name of the page
        output_format: Export format ("html" or "markdown", default: "markdown")

    Returns:
        Export request details with requestId and downloadLink

    Note:
        This is asynchronous. Use get_coda_mutation_status() to check completion.
        Once complete, fetch content from the downloadLink.
    """
    return await pages.export_coda_page(doc_id, page_id_or_name, output_format)

# Formula Operations
@_mcp.tool()
async def list_coda_formulas(
    doc_id: str,
    limit: int = 25,
    page_token: str | None = None
) -> dict:
    """List all formulas in a document.

    Args:
        doc_id: ID of the document
        limit: Maximum results to return (default 25, max 100)
        page_token: Token for pagination

    Returns:
        Dictionary with 'formulas' list and pagination info
    """
    return await formulas.list_coda_formulas(doc_id, limit, page_token)

@_mcp.tool()
async def get_coda_formula(
    doc_id: str,
    formula_id_or_name: str
) -> dict:
    """Get detailed information about a specific formula.

    Args:
        doc_id: ID of the document
        formula_id_or_name: ID (format: formula-*) or name of the formula

    Returns:
        Formula object with id, name, formula expression, parent, etc.
    """
    return await formulas.get_coda_formula(doc_id, formula_id_or_name)

# Control Operations
@_mcp.tool()
async def list_coda_controls(
    doc_id: str,
    limit: int = 25,
    page_token: str | None = None,
    sort_by: str = "name"
) -> dict:
    """List all controls in a document.

    Args:
        doc_id: ID of the document
        limit: Maximum results to return (default 25, max 100)
        page_token: Token for pagination
        sort_by: Sort order - "name" or "createdAt"

    Returns:
        Dictionary with 'controls' list and pagination info
    """
    return await controls.list_coda_controls(doc_id, limit, page_token, sort_by)

@_mcp.tool()
async def get_coda_control(
    doc_id: str,
    control_id_or_name: str
) -> dict:
    """Get detailed information about a specific control.

    Args:
        doc_id: ID of the document
        control_id_or_name: ID (format: ctrl-*) or name of the control

    Returns:
        Control object with id, name, type, value, etc.
    """
    return await controls.get_coda_control(doc_id, control_id_or_name)

@_mcp.tool()
async def list_coda_control_types() -> dict:
    """Get list of available control types supported by Coda API.

    Returns:
        Dictionary with 'control_types' array
    """
    return await controls.list_coda_control_types()

@_mcp.tool()
async def create_coda_control(
    doc_id: str,
    name: str,
    control_type: str,
    initial_value: Any = None,
    options: list | None = None
) -> dict:
    """Create a new control in a Coda document.

    Args:
        doc_id: ID of the document
        name: Name of the control
        control_type: Type of control (button, slider, select, etc.)
        initial_value: Initial value for the control
        options: Options for select/multiselect controls

    Returns:
        Dictionary with success status and created control details
    """
    return await controls.create_coda_control(doc_id, name, control_type, initial_value, options)

@_mcp.tool()
async def update_coda_control(
    doc_id: str,
    control_id_or_name: str,
    value: Any
) -> dict:
    """Update the value of an existing control.

    Args:
        doc_id: ID of the document
        control_id_or_name: ID (format: ctrl-*) or name of the control
        value: New value for the control

    Returns:
        Dictionary with success status and requestId for tracking
    """
    return await controls.update_coda_control(doc_id, control_id_or_name, value)

# Automation Operations
@_mcp.tool()
async def push_coda_button(
    doc_id: str,
    table_id_or_name: str,
    row_id_or_name: str,
    column_id_or_name: str
) -> dict:
    """Push a button in a table row.

    Args:
        doc_id: ID of the document
        table_id_or_name: ID or name of the table
        row_id_or_name: ID or name of the row
        column_id_or_name: ID or name of the button column

    Returns:
        Request ID, row ID, and column ID
    """
    return await automations.push_coda_button(doc_id, table_id_or_name, row_id_or_name, column_id_or_name)

@_mcp.tool()
async def trigger_coda_automation(
    doc_id: str,
    rule_id: str,
    payload: dict[str, Any]
) -> dict:
    """Trigger a webhook-invoked automation rule.

    Args:
        doc_id: ID of the document
        rule_id: ID of the automation rule
        payload: Data to send with the automation trigger

    Returns:
        Request ID for the automation trigger
    """
    return await automations.trigger_coda_automation(doc_id, rule_id, payload)

@_mcp.tool()
async def list_coda_automations(
    doc_id: str,
    limit: int = 100,
    page_token: str | None = None
) -> dict:
    """List automation rules configured in a document.

    Args:
        doc_id: ID of the document
        limit: Maximum number of automations to return (default 100)
        page_token: Token for pagination

    Returns:
        Dictionary with automations list and pagination info
    """
    return await automations.list_coda_automations(
        doc_id=doc_id,
        limit=limit,
        page_token=page_token
    )

@_mcp.tool()
async def get_mutation_status(
    request_id: str
) -> dict:
    """Check the status of an asynchronous mutation.

    Args:
        request_id: ID of the mutation request

    Returns:
        Completion status and optional warning message
    """
    return await automations.get_mutation_status(request_id)

# Permission Operations
@_mcp.tool()
async def list_coda_permissions(
    doc_id: str,
    limit: int = 25,
    page_token: str | None = None
) -> dict:
    """List permissions for a document.

    Args:
        doc_id: ID of the document
        limit: Maximum results to return (default 25)
        page_token: Token for pagination

    Returns:
        Dictionary with 'items' list of permissions and pagination info
    """
    return await permissions.list_coda_permissions(doc_id, limit, page_token)

@_mcp.tool()
async def get_coda_permissions(
    doc_id: str
) -> dict:
    """Get current user's access level for a document.

    Args:
        doc_id: ID of the document

    Returns:
        Dictionary with access level and owner status
    """
    return await permissions.get_coda_permissions(doc_id)

@_mcp.tool()
async def grant_coda_permission(
    doc_id: str,
    access: str,
    principal: dict[str, Any],
    suppress_email: bool = False
) -> dict:
    """Add a permission to a document.

    Args:
        doc_id: ID of the document
        access: Type of access (readonly, write, comment)
        principal: Metadata about the principal (e.g., {"email": "user@example.com", "type": "email"})
        suppress_email: Whether to suppress email notification

    Returns:
        Success status and permission details
    """
    return await permissions.grant_coda_permission(doc_id, access, principal, suppress_email)

@_mcp.tool()
async def revoke_coda_permission(
    doc_id: str,
    permission_id: str
) -> dict:
    """Delete a permission from a document.

    Args:
        doc_id: ID of the document
        permission_id: ID of the permission to delete

    Returns:
        Success status
    """
    return await permissions.revoke_coda_permission(doc_id, permission_id)

@_mcp.tool()
async def publish_coda_doc(
    doc_id: str,
    slug: str | None = None,
    discoverable: bool | None = None,
    earn_credit: bool | None = None,
    category_names: list | None = None,
    mode: str | None = None
) -> dict:
    """Publish a document to the Coda gallery.

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
    return await permissions.publish_coda_doc(doc_id, slug, discoverable, earn_credit, category_names, mode)

@_mcp.tool()
async def unpublish_coda_doc(
    doc_id: str
) -> dict:
    """Unpublish a document from the Coda gallery.

    Args:
        doc_id: ID of the document

    Returns:
        Success status
    """
    return await permissions.unpublish_coda_doc(doc_id)

# Category Operations (v0.7.0)
@_mcp.tool()
async def list_coda_categories() -> dict:
    """List all available Coda Gallery categories.

    Returns:
        Dictionary with 'categories' list of available categories
    """
    return await categories.list_coda_categories()

@_mcp.tool()
async def get_coda_category(category_slug: str) -> dict:
    """Get detailed information about a specific Coda Gallery category.

    Args:
        category_slug: Slug identifier for the category (e.g., "project-management")

    Returns:
        Category details including name, description, and document count
    """
    return await categories.get_coda_category(category_slug)

# Account Operations (v0.7.0)
@_mcp.tool()
async def get_coda_whoami() -> dict:
    """Get information about the current authenticated user.

    Returns:
        User identity including name, email, workspace, and type
    """
    return await account.get_coda_whoami()

@_mcp.tool()
async def get_coda_account() -> dict:
    """Get account and workspace information including limits and usage.

    Returns:
        Workspace details with member counts, document limits, and API rate limits
    """
    return await account.get_coda_account()

@_mcp.tool()
async def list_coda_api_tokens() -> dict:
    """List all API tokens associated with the account.

    Returns:
        Dictionary with 'tokens' list of API tokens and their metadata
    """
    return await account.list_coda_api_tokens()

# Analytics Operations (v0.7.0)
@_mcp.tool()
async def get_coda_doc_analytics(
    doc_id: str,
    start_date: str | None = None,
    end_date: str | None = None
) -> dict:
    """Get analytics for a specific document.

    Args:
        doc_id: ID of the document
        start_date: Start date for analytics period (ISO 8601: YYYY-MM-DD, defaults to 30 days ago)
        end_date: End date for analytics period (ISO 8601: YYYY-MM-DD, defaults to today)

    Returns:
        Document analytics including sessions, views, edits, and unique users
    """
    return await analytics.get_coda_doc_analytics(doc_id, start_date, end_date)

@_mcp.tool()
async def list_coda_doc_analytics_summary(
    start_date: str | None = None,
    end_date: str | None = None
) -> dict:
    """Get analytics summary across all documents in the workspace.

    Args:
        start_date: Start date for analytics period (ISO 8601: YYYY-MM-DD, defaults to 30 days ago)
        end_date: End date for analytics period (ISO 8601: YYYY-MM-DD, defaults to today)

    Returns:
        Organization-wide analytics including total documents, sessions, views, edits, and users
    """
    return await analytics.list_coda_doc_analytics_summary(start_date, end_date)

# ============================================================================
# Webhook Operations (v0.7.0)
# ============================================================================

@_mcp.tool()
async def list_coda_webhooks(
    doc_id: str,
    limit: int = 100,
    page_token: str | None = None
) -> dict:
    """List all webhook subscriptions for a document.

    Args:
        doc_id: Document ID (format: doc-*)
        limit: Maximum number of results per page (default: 100)
        page_token: Token for pagination to fetch next page

    Returns:
        Dictionary with webhook list, pagination info, and API link
    """
    return await webhooks.list_coda_webhooks(doc_id, limit, page_token)

@_mcp.tool()
async def create_coda_webhook(
    doc_id: str,
    endpoint: str,
    event_types: list[str],
    table_id: str | None = None
) -> dict:
    """Create a new webhook subscription to receive real-time event notifications.

    Args:
        doc_id: Document ID (format: doc-*)
        endpoint: HTTPS URL to receive webhook events (must use HTTPS)
        event_types: List of event types to subscribe to (rowAdded, rowUpdated, rowDeleted)
        table_id: Optional table ID to watch specific table (format: grid-*)

    Returns:
        Created webhook details including ID, endpoint, event types, and timestamps
    """
    return await webhooks.create_coda_webhook(doc_id, endpoint, event_types, table_id)

@_mcp.tool()
async def get_coda_webhook(
    doc_id: str,
    webhook_id: str
) -> dict:
    """Get detailed information about a specific webhook subscription.

    Args:
        doc_id: Document ID (format: doc-*)
        webhook_id: Webhook ID (format: webhook-*)

    Returns:
        Webhook details including endpoint, event types, statistics (event count, last event time)
    """
    return await webhooks.get_coda_webhook(doc_id, webhook_id)

@_mcp.tool()
async def delete_coda_webhook(
    doc_id: str,
    webhook_id: str
) -> dict:
    """Delete a webhook subscription (idempotent operation).

    Args:
        doc_id: Document ID (format: doc-*)
        webhook_id: Webhook ID to delete (format: webhook-*)

    Returns:
        Deletion confirmation with webhook ID
    """
    return await webhooks.delete_coda_webhook(doc_id, webhook_id)

def main() -> None:
    log.info(f"starting Coda MCP Server v{__version__} (stdio)")
    _mcp.run(transport="stdio")

# ------------------------------
# Resources & Prompts (scaffold)
# ------------------------------

# Version information resource
@_mcp.resource(
    "coda://version",
    name="coda-version",
    title="Coda MCP Server Version",
    description="Current server version information",
    mime_type="application/json",
)
def resource_version() -> dict:
    """Expose version information as a resource."""
    return {
        "version": __version__,
        "name": "coda-mcp",
        "server": "Coda MCP Server",
        "package": "coda-mcp"
    }

# Simple welcome resource with pointers to docs. This is static and safe.
@_mcp.resource(
    "coda://welcome",
    name="coda-welcome",
    title="Coda MCP: Welcome",
    description="Overview and useful links",
    mime_type="text/markdown",
)
def resource_welcome() -> str:
    return (
        f"# Coda MCP Server v{__version__}\n\n"
        "- Tools: see docs/products/coda-mcp/reference/api/tools/index.md\n"
        "- Getting Started: docs/products/coda-mcp/tutorials/getting-started.md\n"
        "- Platform Docs: docs/platform/overview.md\n"
    )

# Template resource to fetch Coda doc metadata by ID. Requires CODA_API_KEY.
@_mcp.resource(
    "coda://doc/{doc_id}",
    name="coda-doc-meta",
    title="Coda Document Metadata",
    description="Fetch Coda document metadata as JSON",
    mime_type="application/json",
)
async def resource_doc_meta(doc_id: str) -> dict:
    try:
        return await documents.get_coda_doc(doc_id)
    except Exception as e:
        # Keep stdout content valid JSON; return structured error
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}

# Basic prompt to guide summarization of a table
@_mcp.prompt(
    name="summarize_coda_table",
    title="Summarize a Coda Table",
    description="Ask the model to summarize a Coda table and suggest insights",
)
def prompt_summarize_coda_table(doc_id: str, table_id_or_name: str) -> list[dict]:
    return [
        {
            "role": "user",
            "content": (
                f"Summarize the Coda table '{table_id_or_name}' in document '{doc_id}'. "
                "Provide key metrics, trends, and 2-3 suggested next actions."
            ),
        }
    ]

# v0.2: Table preview resource
@_mcp.resource(
    "coda://doc/{doc_id}/table/{table_id_or_name}",
    name="coda-table-preview",
    title="Coda Table Preview",
    description="Preview a table's schema and first rows",
    mime_type="application/json",
)
async def resource_table_preview(doc_id: str, table_id_or_name: str) -> dict:
    try:
        # Fetch columns schema via get_table
        table_meta = await tables.get_coda_table(doc_id, table_id_or_name, use_column_names=True)
        columns = []
        cols = table_meta.get("table", {}).get("columns", []) if isinstance(table_meta, dict) else []
        for c in cols:
            columns.append({
                "id": c.get("id"),
                "name": c.get("name"),
                "type": c.get("type"),
            })

        # Fetch first N rows
        row_limit = 5
        rows_resp = await rows.list_coda_rows(
            doc_id,
            table_id_or_name,
            query=None,
            sort_by=None,
            use_column_names=True,
            value_format="simple",
            visible_only=True,
            limit=row_limit,
            page_token=None,
            sync_token=None,
        )
        items = []
        for r in (rows_resp.get("items") or []):
            items.append(r)

        return {
            "success": True,
            "doc_id": doc_id,
            "table": table_id_or_name,
            "columns": columns,
            "rows": items,
            "limit": row_limit,
        }
    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


if __name__ == "__main__":
    main()

# v0.2: Confirm-write prompt
@_mcp.prompt(
    name="confirm_coda_insert",
    title="Confirm Coda Insert",
    description="Ask the user to confirm inserting rows into a Coda table",
)
def prompt_confirm_coda_insert(doc_id: str, table_id_or_name: str, preview_rows: list[dict]) -> list[dict]:
    preview = preview_rows[:5]
    return [
        {
            "role": "user",
            "content": (
                "You are about to insert the following rows into the Coda table "
                f"'{table_id_or_name}' in document '{doc_id}'.\n\nPreview (first {len(preview)}):\n{preview}\n\n"
                "If this looks correct, reply with CONFIRM. If not, reply with CANCEL and explain changes."
            ),
        }
    ]
