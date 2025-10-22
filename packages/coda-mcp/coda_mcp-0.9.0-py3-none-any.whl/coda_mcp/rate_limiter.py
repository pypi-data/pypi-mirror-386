# src/coda_mcp/rate_limiter.py
"""Rate limiting for Coda API requests using sliding window algorithm."""
from __future__ import annotations

import asyncio
import time

from coda_mcp.logging import get_logger

log = get_logger("coda_mcp.rate_limiter")


class SlidingWindowRateLimiter:
    """
    Implements a sliding window rate limiter for API requests.
    Ensures requests don't exceed specified limits within time windows.
    """

    def __init__(self, limit: int, period: float):
        """
        Initialize the rate limiter.

        Args:
            limit: Maximum number of requests allowed
            period: Time window in seconds
        """
        self.limit = limit
        self.period = period
        self.requests: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Acquire a rate limit slot, waiting if necessary.

        This will block if the rate limit has been exceeded, waiting until
        a slot becomes available in the sliding window.
        """
        async with self._lock:
            now = time.time()

            # Remove expired timestamps from sliding window
            self.requests = [t for t in self.requests if now - t < self.period]

            # If at capacity, wait for the oldest request to expire
            if len(self.requests) >= self.limit:
                sleep_time = self.requests[0] + self.period - now
                if sleep_time > 0:
                    log.debug(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
                    # Recheck after sleeping
                    now = time.time()
                    self.requests = [t for t in self.requests if now - t < self.period]

            # Record this request
            self.requests.append(time.time())

    def get_remaining(self) -> int:
        """Get number of requests remaining in current window."""
        now = time.time()
        self.requests = [t for t in self.requests if now - t < self.period]
        return max(0, self.limit - len(self.requests))


class CodaRateLimiter:
    """
    Manages rate limiting for Coda API requests across different endpoint types.

    Uses sliding window rate limiters for:
    - Global limit: 1000 requests/minute across all endpoints
    - Read operations: 100 requests/6 seconds
    - Write operations: 10 requests/6 seconds
    - Content write (buttons): 5 requests/10 seconds
    - List docs: 4 requests/6 seconds
    - Analytics: 100 requests/6 seconds
    """

    def __init__(self):
        """Initialize rate limiters based on Coda API limits."""
        # Global rate limit: 1000 req/min
        self.global_limiter = SlidingWindowRateLimiter(limit=1000, period=60)

        # Per-operation rate limiters (from application.json)
        self.limiters: dict[str, SlidingWindowRateLimiter] = {
            "read": SlidingWindowRateLimiter(limit=100, period=6),
            "write": SlidingWindowRateLimiter(limit=10, period=6),
            "content_write": SlidingWindowRateLimiter(limit=5, period=10),
            "list_docs": SlidingWindowRateLimiter(limit=4, period=6),
            "read_analytics": SlidingWindowRateLimiter(limit=100, period=6),
        }

        log.info("Rate limiters initialized")

    def _classify_request(self, method: str, path: str) -> str:
        """
        Classify request into rate limit category.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            path: API path (e.g., "docs/abc/tables/xyz/rows")

        Returns:
            Rate limit category key
        """
        # List docs endpoint
        if path == "docs" and method == "GET":
            return "list_docs"

        # Analytics endpoints
        if "analytics" in path:
            return "read_analytics"

        # Button push operations
        if "buttons" in path and method == "POST":
            return "content_write"

        # Write operations
        if method in ("POST", "PUT", "PATCH", "DELETE"):
            return "write"

        # Default to read
        return "read"

    async def acquire(self, method: str, path: str) -> None:
        """
        Acquire rate limit for a request.

        Args:
            method: HTTP method
            path: API path
        """
        # Always apply global limit first
        await self.global_limiter.acquire()

        # Then apply specific limit
        category = self._classify_request(method, path)
        if category in self.limiters:
            await self.limiters[category].acquire()
            log.debug(f"Rate limit acquired for {method} {path} (category: {category})")


# Global rate limiter instance
_rate_limiter: CodaRateLimiter | None = None


def get_rate_limiter() -> CodaRateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = CodaRateLimiter()
    return _rate_limiter
