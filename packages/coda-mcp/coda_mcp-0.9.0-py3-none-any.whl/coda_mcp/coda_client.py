# src/coda_mcp/coda_client.py
"""Shared Coda API client with rate limiting support."""
from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx

from coda_mcp.logging import get_logger
from coda_mcp.rate_limiter import get_rate_limiter

log = get_logger("coda_mcp.coda_client")

CODA_API_BASE = "https://coda.io/apis/v1"

# Global client instance
_http_client: httpx.AsyncClient | None = None


def get_coda_api_key() -> str:
    """Get Coda API key from environment."""
    api_key = os.getenv("CODA_API_KEY")
    if not api_key:
        raise ValueError("CODA_API_KEY environment variable not set")
    return api_key


async def get_http_client() -> httpx.AsyncClient:
    """Get or create shared async HTTP client."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        log.debug("HTTP client initialized")
    return _http_client


async def close_http_client() -> None:
    """Close the shared HTTP client."""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
        log.debug("HTTP client closed")


def build_url(*path_segments: str) -> str:
    """
    Build Coda API URL from path segments.

    Args:
        path_segments: URL path components (e.g., 'docs', doc_id, 'tables')

    Returns:
        Complete API URL
    """
    filtered = [seg.strip('/') for seg in path_segments if seg and seg.strip('/')]
    path = '/'.join(filtered)
    return f"{CODA_API_BASE}/{path}"


async def coda_request(
    method: str,
    *path_segments: str,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    max_retries: int = 3
) -> dict[str, Any]:
    """
    Make authenticated request to Coda API with rate limiting and retry logic.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path_segments: URL path components
        params: Query parameters
        json: JSON request body
        max_retries: Maximum number of retries for 429 errors (default 3)

    Returns:
        Response data as dictionary

    Raises:
        ValueError: If API key not configured
        httpx.HTTPStatusError: If request fails after retries
    """
    api_key = get_coda_api_key()
    url = build_url(*path_segments)
    client = await get_http_client()
    rate_limiter = get_rate_limiter()

    # Extract path for rate limiting (remove base URL)
    path = '/'.join(path_segments)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    attempt = 0
    while attempt <= max_retries:
        try:
            # Apply rate limiting before making request
            await rate_limiter.acquire(method, path)

            log.debug(f"{method} {url} (attempt {attempt + 1}/{max_retries + 1})")

            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json
            )

            # Log rate limit headers for monitoring
            remaining = response.headers.get('X-RateLimit-Remaining')
            reset = response.headers.get('X-RateLimit-Reset')
            if remaining:
                log.debug(f"Rate limit remaining: {remaining}, reset: {reset}")

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            # Handle rate limit exceeded (429)
            if e.response.status_code == 429 and attempt < max_retries:
                retry_after = int(e.response.headers.get('Retry-After', '1'))
                log.warning(f"Rate limit exceeded (429), retrying after {retry_after}s")
                await asyncio.sleep(retry_after)
                attempt += 1
                continue
            # Re-raise other errors or if out of retries
            raise

        except Exception as e:
            log.error(f"Request failed: {e}")
            raise

    # Should not reach here, but just in case
    raise httpx.HTTPStatusError(
        f"Max retries ({max_retries}) exceeded",
        request=None,
        response=None
    )
