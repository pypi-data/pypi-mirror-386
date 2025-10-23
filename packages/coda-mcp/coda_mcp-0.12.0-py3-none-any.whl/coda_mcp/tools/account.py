# src/coda_mcp/tools/account.py
"""Account-level Coda API operations for identity and token management (v0.7.0)."""
from __future__ import annotations

from coda_mcp.coda_client import coda_request
from coda_mcp.logging import get_logger

log = get_logger("coda_mcp.tools.account")


async def get_coda_whoami() -> dict:
    """
    Get information about the current authenticated user.

    Returns:
        Dictionary with user identity (name, email, type, workspace)
    """
    try:
        log.info("Getting current user identity")

        result = await coda_request("GET", "whoami")

        log.info(f"Retrieved user: {result.get('name')} ({result.get('email')})")

        return {
            "success": True,
            "name": result.get("name"),
            "email": result.get("email"),
            "type": result.get("type"),
            "href": result.get("href"),
            "workspace": result.get("workspace"),
            "pictureUrl": result.get("pictureUrl")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to get user identity: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def get_coda_account() -> dict:
    """
    Get account and workspace information including limits and usage.

    Returns:
        Dictionary with workspace details (id, name, limits, usage)
    """
    try:
        log.info("Getting account information")

        result = await coda_request("GET", "account")

        workspace = result.get("workspace", {})
        log.info(f"Retrieved account for workspace: {workspace.get('name')}")

        return {
            "success": True,
            "workspace": {
                "id": workspace.get("id"),
                "name": workspace.get("name"),
                "organizationId": workspace.get("organizationId"),
                "memberCount": workspace.get("memberCount", 0),
                "docLimit": workspace.get("docLimit", 0),
                "docCount": workspace.get("docCount", 0),
                "apiRateLimit": workspace.get("apiRateLimit", 10),
                "createdAt": workspace.get("createdAt")
            }
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to get account info: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def list_coda_api_tokens() -> dict:
    """
    List all API tokens associated with the account.

    Returns:
        Dictionary with 'tokens' list containing id, name, createdAt, lastUsed
    """
    try:
        log.info("Listing API tokens")

        result = await coda_request("GET", "apiTokens")

        token_count = len(result.get("items", []))
        log.info(f"Found {token_count} API tokens")

        return {
            "success": True,
            "tokens": result.get("items", []),
            "href": result.get("href")
        }

    except ValueError as e:
        log.error(f"Configuration error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        log.error(f"Failed to list API tokens: {e}", exc_info=True)
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}
