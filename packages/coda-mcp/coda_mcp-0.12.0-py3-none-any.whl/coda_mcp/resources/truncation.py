"""Content truncation utilities for MCP resources."""


class ContentTruncator:
    """Handles content truncation for large resource responses."""

    # Default limits
    DEFAULT_MAX_BYTES = 51200  # 50KB
    DEFAULT_MAX_ROWS = 10

    @staticmethod
    def truncate_text(
        content: str,
        max_bytes: int = DEFAULT_MAX_BYTES,
        tool_hint: str = "",
        resource_name: str = ""
    ) -> tuple[str, bool]:
        """Truncate text content to maximum byte size.

        Args:
            content: Text content to truncate
            max_bytes: Maximum size in bytes (default: 50KB)
            tool_hint: Tool name to suggest for full content (e.g., "get_coda_page")
            resource_name: Name of resource being truncated (for note)

        Returns:
            Tuple of (truncated_content, was_truncated)
        """
        content_bytes = content.encode('utf-8')

        if len(content_bytes) <= max_bytes:
            return content, False

        # Truncate at byte boundary
        truncated_bytes = content_bytes[:max_bytes]

        # Decode, ignoring incomplete characters at end
        truncated = truncated_bytes.decode('utf-8', errors='ignore')

        # Try to truncate at last complete line for cleaner output
        last_newline = truncated.rfind('\n')
        if last_newline > max_bytes * 0.9:  # Only if we don't lose too much
            truncated = truncated[:last_newline]

        # Add truncation note
        note = ContentTruncator._build_truncation_note(
            original_bytes=len(content_bytes),
            max_bytes=max_bytes,
            tool_hint=tool_hint,
            resource_name=resource_name
        )

        return truncated + "\n\n" + note, True

    @staticmethod
    def truncate_rows(
        rows: list,
        max_rows: int = DEFAULT_MAX_ROWS,
        total_count: int | None = None,
        tool_hint: str = "list_coda_rows"
    ) -> tuple[list, bool]:
        """Truncate list of rows to maximum count.

        Args:
            rows: List of row data
            max_rows: Maximum number of rows to return (default: 10)
            total_count: Total number of rows available (for note)
            tool_hint: Tool name to suggest for full data

        Returns:
            Tuple of (truncated_rows, was_truncated)
        """
        if len(rows) <= max_rows:
            return rows, False

        return rows[:max_rows], True

    @staticmethod
    def _build_truncation_note(
        original_bytes: int,
        max_bytes: int,
        tool_hint: str,
        resource_name: str
    ) -> str:
        """Build truncation note for Markdown.

        Args:
            original_bytes: Original content size in bytes
            max_bytes: Maximum allowed bytes
            tool_hint: Tool to suggest for full content
            resource_name: Name of truncated resource

        Returns:
            Markdown truncation note
        """
        original_kb = original_bytes / 1024
        max_kb = max_bytes / 1024

        note_parts = [
            "---",
            f"*Content truncated at {max_kb:.0f}KB (full content is {original_kb:.0f}KB)."
        ]

        if tool_hint:
            note_parts.append(f" Use tool `{tool_hint}` for complete content.*")
        else:
            note_parts.append("*")

        return "\n".join(note_parts)

    @staticmethod
    def build_preview_note(
        shown_count: int,
        total_count: int,
        tool_hint: str = "list_coda_rows",
        resource_type: str = "rows"
    ) -> str:
        """Build preview note for limited row display.

        Args:
            shown_count: Number of rows shown
            total_count: Total number of rows available
            tool_hint: Tool to suggest for full data
            resource_type: Type of items (e.g., "rows", "documents")

        Returns:
            Markdown preview note
        """
        if shown_count >= total_count:
            return ""

        note = f"\n\n**Note**: Showing {shown_count} of {total_count} total {resource_type}."

        if tool_hint:
            note += f" For more:\n- Query with filters: Use `{tool_hint}` tool"

        return note
