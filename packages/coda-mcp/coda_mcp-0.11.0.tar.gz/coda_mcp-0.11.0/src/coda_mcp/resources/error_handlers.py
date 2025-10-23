"""Standard error response formatting for MCP resources."""
import json
from typing import Any


class ErrorFormatter:
    """Formats error responses for MCP resources."""

    @staticmethod
    def build_error(
        error: str,
        hint: str,
        error_detail: dict[str, Any] | None = None
    ) -> str:
        """Build standardized error response as JSON string.

        Args:
            error: Human-readable error message with context
            hint: Actionable recovery step
            error_detail: Optional additional error details

        Returns:
            JSON string with {success: false, error, hint, error_detail?}
        """
        response: dict[str, Any] = {
            "success": False,
            "error": error,
            "hint": hint
        }

        if error_detail:
            response["error_detail"] = error_detail

        return json.dumps(response, indent=2)

    @staticmethod
    def not_found(resource_type: str, resource_id: str, suggestion: str = "") -> str:
        """Format 404 Not Found error.

        Args:
            resource_type: Type of resource (e.g., "document", "page", "table")
            resource_id: ID that was not found
            suggestion: Optional suggestion for discovery (e.g., "list_coda_pages")

        Returns:
            JSON error response
        """
        error = f"{resource_type.title()} not found: {resource_id}"
        hint = f"Verify {resource_type} ID exists and you have access"

        if suggestion:
            hint += f". Use `{suggestion}` tool to discover valid IDs"

        return ErrorFormatter.build_error(error, hint, {
            "http_status": 404,
            "resource_type": resource_type,
            "resource_id": resource_id
        })

    @staticmethod
    def forbidden(resource_type: str, resource_id: str) -> str:
        """Format 403 Forbidden error.

        Args:
            resource_type: Type of resource
            resource_id: ID that access was denied for

        Returns:
            JSON error response
        """
        error = f"Permission denied for {resource_type}: {resource_id}"
        hint = f"Request access permissions from the {resource_type} owner"

        return ErrorFormatter.build_error(error, hint, {
            "http_status": 403,
            "resource_type": resource_type,
            "resource_id": resource_id
        })

    @staticmethod
    def unauthorized() -> str:
        """Format 401 Unauthorized error.

        Returns:
            JSON error response
        """
        error = "Unauthorized: Invalid or missing API key"
        hint = "Check CODA_API_KEY environment variable is set correctly"

        return ErrorFormatter.build_error(error, hint, {
            "http_status": 401
        })

    @staticmethod
    def rate_limited(retry_after: int = 60) -> str:
        """Format 429 Rate Limited error.

        Args:
            retry_after: Seconds to wait before retrying

        Returns:
            JSON error response
        """
        error = "Rate limit exceeded"
        hint = f"Wait {retry_after} seconds before retrying"

        return ErrorFormatter.build_error(error, hint, {
            "http_status": 429,
            "retry_after": retry_after
        })

    @staticmethod
    def from_exception(exception: Exception, context: str = "") -> str:
        """Format generic exception as error response.

        Args:
            exception: Exception that occurred
            context: Optional context about what was being attempted

        Returns:
            JSON error response
        """
        error_msg = str(exception)
        if context:
            error_msg = f"{context}: {error_msg}"

        hint = "Check error details and verify request parameters"

        return ErrorFormatter.build_error(error_msg, hint, {
            "exception_type": type(exception).__name__
        })
