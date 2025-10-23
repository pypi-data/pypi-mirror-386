"""Markdown formatting utilities for MCP resources."""
from typing import Any


class MarkdownFormatter:
    """Formats data as Markdown for MCP resource responses."""

    @staticmethod
    def format_table(
        headers: list[str],
        rows: list[list[Any]],
        alignments: list[str] | None = None
    ) -> str:
        """Format data as Markdown table.

        Args:
            headers: Column headers
            rows: List of row data (each row is a list of values)
            alignments: Optional list of alignments ('left', 'center', 'right')
                       Defaults to 'left' for all columns

        Returns:
            Markdown table string
        """
        if not headers:
            return ""

        if alignments is None:
            alignments = ["left"] * len(headers)

        # Build header row
        header_row = "| " + " | ".join(str(h) for h in headers) + " |"

        # Build separator row with alignments
        separators = []
        for align in alignments:
            if align == "center":
                separators.append(":---:")
            elif align == "right":
                separators.append("---:")
            else:  # left or default
                separators.append("---")

        separator_row = "| " + " | ".join(separators) + " |"

        # Build data rows
        data_rows = []
        for row in rows:
            # Ensure row has same number of columns as headers
            padded_row = list(row) + [""] * (len(headers) - len(row))
            row_str = "| " + " | ".join(str(val) for val in padded_row[:len(headers)]) + " |"
            data_rows.append(row_str)

        # Combine all parts
        return "\n".join([header_row, separator_row] + data_rows)

    @staticmethod
    def format_pagination_hint(
        next_page_token: str | None,
        param_name: str = "pageToken"
    ) -> str:
        """Format pagination hint for Markdown.

        Args:
            next_page_token: Token for next page (or None if no more pages)
            param_name: Parameter name to use in hint (default: pageToken)

        Returns:
            Markdown pagination hint string
        """
        if not next_page_token:
            return ""

        return f"\n\n**Next Page**: Use `{param_name}={next_page_token}` to retrieve more results."

    @staticmethod
    def format_list(
        items: list[str],
        ordered: bool = False,
        indent: int = 0
    ) -> str:
        """Format list as Markdown.

        Args:
            items: List items
            ordered: True for numbered list, False for bullet list
            indent: Indentation level (0-based)

        Returns:
            Markdown list string
        """
        if not items:
            return ""

        indent_str = "  " * indent
        lines = []

        for i, item in enumerate(items, start=1):
            if ordered:
                lines.append(f"{indent_str}{i}. {item}")
            else:
                lines.append(f"{indent_str}- {item}")

        return "\n".join(lines)

    @staticmethod
    def format_heading(text: str, level: int = 1) -> str:
        """Format heading in Markdown.

        Args:
            text: Heading text
            level: Heading level (1-6)

        Returns:
            Markdown heading string
        """
        level = max(1, min(6, level))  # Clamp to 1-6
        return f"{'#' * level} {text}"

    @staticmethod
    def format_link(text: str, url: str) -> str:
        """Format link in Markdown.

        Args:
            text: Link text
            url: Link URL (can be resource URI like coda://...)

        Returns:
            Markdown link string
        """
        return f"[{text}]({url})"

    @staticmethod
    def format_emphasis(text: str, strong: bool = False) -> str:
        """Format emphasis in Markdown.

        Args:
            text: Text to emphasize
            strong: True for bold (**text**), False for italic (*text*)

        Returns:
            Markdown emphasis string
        """
        if strong:
            return f"**{text}**"
        else:
            return f"*{text}*"

    @staticmethod
    def format_code_block(code: str, language: str = "") -> str:
        """Format code block in Markdown.

        Args:
            code: Code content
            language: Optional language identifier

        Returns:
            Markdown code block string
        """
        return f"```{language}\n{code}\n```"

    @staticmethod
    def format_horizontal_rule() -> str:
        """Format horizontal rule in Markdown.

        Returns:
            Markdown horizontal rule string
        """
        return "\n---\n"

    @staticmethod
    def format_blockquote(text: str) -> str:
        """Format blockquote in Markdown.

        Args:
            text: Quote text (can be multiline)

        Returns:
            Markdown blockquote string
        """
        lines = text.split("\n")
        return "\n".join(f"> {line}" for line in lines)

    @staticmethod
    def escape_markdown(text: str) -> str:
        """Escape special Markdown characters.

        Args:
            text: Text to escape

        Returns:
            Escaped text safe for Markdown
        """
        # Escape common Markdown special characters
        special_chars = ['\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!', '|']
        escaped = text
        for char in special_chars:
            escaped = escaped.replace(char, '\\' + char)
        return escaped
