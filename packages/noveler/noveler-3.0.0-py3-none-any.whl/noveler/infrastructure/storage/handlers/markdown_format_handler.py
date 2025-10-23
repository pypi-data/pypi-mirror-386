# File: src/noveler/infrastructure/storage/handlers/markdown_format_handler.py
# Purpose: Markdown with YAML frontmatter serialization/deserialization handler
# Context: Infrastructure implementation of IFileFormatHandler for Markdown format

import re
from datetime import datetime, timezone
from typing import Any

import yaml

from noveler.domain.interfaces.i_file_format_handler import IFileFormatHandler


class MarkdownFormatHandler(IFileFormatHandler):
    """Markdown with YAML frontmatter handler implementation.

    Responsibilities:
    - Serialize text content with YAML frontmatter
    - Deserialize frontmatter + markdown content
    - Extract metadata from YAML frontmatter

    Design Decisions:
    - Format: "---\\nYAML frontmatter\\n---\\nMarkdown content"
    - Metadata in frontmatter, content as plain text
    - Preserve line endings
    - Auto-add "created" and "format" metadata if missing

    Error Handling:
    - YAMLError in frontmatter → ValueError
    - Invalid frontmatter format → treat as plain text (no error)
    """

    def serialize(self, content: Any, metadata: dict | None = None) -> str:
        """Convert text content to Markdown with YAML frontmatter.

        Args:
            content: Markdown text content (string)
            metadata: Optional metadata for YAML frontmatter

        Returns:
            Markdown string with YAML frontmatter

        Raises:
            ValueError: If content cannot be converted to string
            TypeError: If content is not string-like

        Side Effects:
            None (pure function, but auto-adds timestamp if "created" not in metadata)

        Preconditions:
            - content should be string or string-convertible

        Postconditions:
            - Returns valid Markdown with "---" delimited frontmatter
            - Metadata includes "created" (ISO8601) and "format": "markdown"
        """
        try:
            # Ensure content is string
            content_str = str(content)

            # Initialize metadata with defaults
            if metadata is None:
                metadata = {}

            # Auto-add metadata if missing
            if "created" not in metadata:
                metadata["created"] = datetime.now(timezone.utc).isoformat()
            if "format" not in metadata:
                metadata["format"] = "markdown"

            # Create frontmatter + content
            return self._create_frontmatter_content(content_str, metadata)

        except (TypeError, ValueError) as e:
            msg = f"Failed to serialize content to Markdown: {e}"
            raise ValueError(msg) from e

    def deserialize(self, data: str | bytes) -> tuple[Any, dict | None]:
        """Convert Markdown with frontmatter to content and metadata.

        Args:
            data: Markdown string or bytes with optional YAML frontmatter

        Returns:
            Tuple of (content, metadata)
            - content: Markdown text (frontmatter removed)
            - metadata: Parsed frontmatter dict or empty dict

        Raises:
            ValueError: If frontmatter YAML is invalid

        Side Effects:
            None (pure function)

        Preconditions:
            - data must be valid UTF-8 string/bytes

        Postconditions:
            - Returns tuple with content stripped of frontmatter
            - Metadata is valid dict or empty dict (never None)
        """
        try:
            # Convert bytes to string if needed
            if isinstance(data, bytes):
                data = data.decode("utf-8")

            # Extract content and metadata
            content = self._extract_content_from_frontmatter(data)
            metadata = self._extract_metadata_from_frontmatter(data)

            return content, metadata

        except (UnicodeDecodeError, yaml.YAMLError) as e:
            msg = f"Failed to deserialize Markdown data: {e}"
            raise ValueError(msg) from e

    def get_supported_extensions(self) -> list[str]:
        """Return supported file extensions for Markdown format.

        Returns:
            List containing [".md", ".markdown"]

        Side Effects:
            None (pure function)
        """
        return [".md", ".markdown"]

    def _create_frontmatter_content(self, content: str, metadata: dict) -> str:
        """Create YAML frontmatter + Markdown content.

        Args:
            content: Markdown text
            metadata: Frontmatter metadata dict

        Returns:
            Frontmatter-formatted content

        Side Effects:
            None (pure function)

        Preconditions:
            - metadata must be dict

        Postconditions:
            - Returns "---\\n...yaml...\\n---\\n\\ncontent"
            - If metadata is empty, returns content unchanged
        """
        if not metadata:
            return content

        try:
            # YAML dump with safe formatting
            yaml_content = yaml.dump(
                metadata, default_flow_style=False, allow_unicode=True, sort_keys=False
            )

            return f"""---
{yaml_content.rstrip()}
---

{content}"""
        except yaml.YAMLError:
            # YAML generation failed, return content without frontmatter
            return content

    def _extract_content_from_frontmatter(self, full_content: str) -> str:
        """Extract Markdown content from frontmatter.

        Args:
            full_content: Full Markdown with possible frontmatter

        Returns:
            Markdown content only (frontmatter removed)

        Side Effects:
            None (pure function)

        Preconditions:
            - full_content must be string

        Postconditions:
            - Returns content stripped of frontmatter
            - If no frontmatter, returns original content
        """
        if not full_content.startswith("---"):
            return full_content

        # Frontmatter pattern matching
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, full_content, re.DOTALL)

        if match:
            return match.group(2).strip()
        return full_content

    def _extract_metadata_from_frontmatter(self, full_content: str) -> dict:
        """Extract metadata from YAML frontmatter.

        Args:
            full_content: Full Markdown with possible frontmatter

        Returns:
            Metadata dict (empty if no frontmatter or parse error)

        Side Effects:
            None (pure function)

        Preconditions:
            - full_content must be string

        Postconditions:
            - Returns valid dict (never None)
            - Returns empty dict if no frontmatter or parse error
        """
        if not full_content.startswith("---"):
            return {}

        pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.match(pattern, full_content, re.DOTALL)

        if match:
            try:
                yaml_content = match.group(1)
                return yaml.safe_load(yaml_content) or {}
            except yaml.YAMLError:
                return {}
        else:
            return {}
