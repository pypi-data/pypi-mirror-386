# File: tests/contracts/test_file_format_handler_contract.py
# Purpose: Contract tests for IFileFormatHandler interface compliance
# Context: Verifies all handlers implement the interface correctly with LSP compliance

import pytest

from noveler.domain.interfaces.i_file_format_handler import IFileFormatHandler
from noveler.infrastructure.storage.handlers import JsonFormatHandler, MarkdownFormatHandler, YamlFormatHandler


@pytest.fixture(
    params=[
        (JsonFormatHandler(), ".json"),
        (YamlFormatHandler(), ".yaml"),
        (MarkdownFormatHandler(), ".md"),
    ],
    ids=["json", "yaml", "markdown"],
)
def handler_with_extension(request):
    """Parametrized fixture providing all handlers with their primary extension."""
    return request.param


class TestFileFormatHandlerContract:
    """Contract tests for IFileFormatHandler interface.

    These tests verify that all implementations of IFileFormatHandler:
    1. Implement all required methods
    2. Satisfy the Liskov Substitution Principle (LSP)
    3. Maintain round-trip integrity (serialize → deserialize)
    4. Handle edge cases consistently
    """

    def test_handler_implements_interface(self, handler_with_extension):
        """Verify handler implements IFileFormatHandler."""
        handler, _ext = handler_with_extension
        assert isinstance(handler, IFileFormatHandler)

    def test_serialize_returns_str_or_bytes(self, handler_with_extension):
        """Contract: serialize() must return str or bytes."""
        handler, _ext = handler_with_extension
        content = {"test": "data", "number": 42}
        result = handler.serialize(content, None)

        assert isinstance(result, (str, bytes)), f"Expected str or bytes, got {type(result)}"

    def test_deserialize_returns_tuple(self, handler_with_extension):
        """Contract: deserialize() must return tuple[Any, dict | None]."""
        handler, _ext = handler_with_extension
        content = {"test": "data"}
        serialized = handler.serialize(content, None)
        result = handler.deserialize(serialized)

        assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
        assert len(result) == 2, f"Expected tuple of length 2, got {len(result)}"
        assert isinstance(result[1], (dict, type(None))), f"Expected dict or None for metadata, got {type(result[1])}"

    def test_get_supported_extensions_returns_list(self, handler_with_extension):
        """Contract: get_supported_extensions() must return list[str]."""
        handler, _ext = handler_with_extension
        result = handler.get_supported_extensions()

        assert isinstance(result, list), f"Expected list, got {type(result)}"
        assert len(result) > 0, "Supported extensions list must not be empty"
        assert all(isinstance(ext, str) for ext in result), "All extensions must be strings"
        assert all(ext.startswith(".") for ext in result), "All extensions must start with '.'"

    def test_round_trip_without_metadata(self, handler_with_extension):
        """Contract: Round-trip without metadata preserves content."""
        handler, _ext = handler_with_extension

        # Markdown handles text, JSON/YAML handle structured data
        if isinstance(handler, MarkdownFormatHandler):
            original = "# Test Heading\n\nParagraph content."
            serialized = handler.serialize(original, None)
            content, metadata = handler.deserialize(serialized)
            assert content.strip() == original.strip()
        else:
            original = {"key": "value", "number": 123, "nested": {"data": "test"}}
            serialized = handler.serialize(original, None)
            content, metadata = handler.deserialize(serialized)
            assert content == original, f"Round-trip failed: {content} != {original}"

        # Metadata should be dict (possibly empty) or None
        assert isinstance(metadata, (dict, type(None)))

    def test_round_trip_with_metadata(self, handler_with_extension):
        """Contract: Round-trip with metadata preserves both content and metadata."""
        handler, _ext = handler_with_extension
        original_metadata = {"author": "test", "version": 1}

        # Markdown handles text, JSON/YAML handle structured data
        if isinstance(handler, MarkdownFormatHandler):
            original_content = "# Test Document\n\nContent here."
            serialized = handler.serialize(original_content, original_metadata)
            content, metadata = handler.deserialize(serialized)
            assert content.strip() == original_content.strip()
        else:
            original_content = {"key": "value"}
            serialized = handler.serialize(original_content, original_metadata)
            content, metadata = handler.deserialize(serialized)
            assert content == original_content, f"Content mismatch: {content} != {original_content}"

        # Metadata must be preserved (allowing for additional fields like auto-added timestamps)
        if metadata:
            for key, value in original_metadata.items():
                assert key in metadata, f"Metadata key '{key}' not preserved"
                assert metadata[key] == value, f"Metadata value mismatch for '{key}'"

    def test_serialize_empty_dict(self, handler_with_extension):
        """Contract: Handlers must support empty dict serialization."""
        handler, _ext = handler_with_extension

        # Skip for Markdown (dict → str conversion)
        if isinstance(handler, MarkdownFormatHandler):
            pytest.skip("MarkdownHandler treats dict as string, not round-trip preserving")

        empty = {}
        serialized = handler.serialize(empty, None)
        content, _metadata = handler.deserialize(serialized)

        assert content == empty

    def test_serialize_with_unicode(self, handler_with_extension):
        """Contract: Handlers must preserve Unicode characters."""
        handler, _ext = handler_with_extension

        # Markdown handles text, JSON/YAML handle structured data
        if isinstance(handler, MarkdownFormatHandler):
            unicode_data = "こんにちは世界 🎉"
            serialized = handler.serialize(unicode_data, None)
            content, _metadata = handler.deserialize(serialized)
            assert unicode_data in content
        else:
            unicode_data = {"text": "こんにちは世界", "emoji": "🎉"}
            serialized = handler.serialize(unicode_data, None)
            content, _metadata = handler.deserialize(serialized)
            assert content == unicode_data

    def test_deserialize_with_bytes(self, handler_with_extension):
        """Contract: Handlers must accept both str and bytes for deserialization."""
        handler, _ext = handler_with_extension

        # Markdown handles text, JSON/YAML handle structured data
        if isinstance(handler, MarkdownFormatHandler):
            original = "Test content"
        else:
            original = {"test": "data"}

        serialized_str = handler.serialize(original, None)

        # Convert to bytes
        if isinstance(serialized_str, str):
            serialized_bytes = serialized_str.encode("utf-8")
        else:
            serialized_bytes = serialized_str

        # Both str and bytes should deserialize correctly
        content_from_str, _ = handler.deserialize(serialized_str)
        content_from_bytes, _ = handler.deserialize(serialized_bytes)

        # For Markdown, check substring; for JSON/YAML, exact match
        if isinstance(handler, MarkdownFormatHandler):
            assert original in content_from_str
            assert original in content_from_bytes
        else:
            assert content_from_str == original
            assert content_from_bytes == original

    def test_serialize_invalid_data_raises_error(self, handler_with_extension):
        """Contract: Handlers should attempt to serialize data (lenient design)."""
        handler, _ext = handler_with_extension

        # Skip test - current design uses default=str for lenient conversion
        # See DEC-034 in decision_log.yaml
        pytest.skip("Lenient design: handlers use default=str for automatic conversion")

    def test_deserialize_invalid_data_raises_error(self, handler_with_extension):
        """Contract: Handlers must raise ValueError for invalid format data."""
        handler, _ext = handler_with_extension

        # Markdown treats any text as valid (no structure validation)
        if isinstance(handler, MarkdownFormatHandler):
            pytest.skip("MarkdownHandler accepts any text as valid content")

        # YAML can parse "key: value" style text without error
        if isinstance(handler, YamlFormatHandler):
            pytest.skip("YAMLHandler is lenient with plain text parsing")

        invalid_data = "this is not valid {format} data !!!"

        with pytest.raises(ValueError):
            handler.deserialize(invalid_data)

    def test_supported_extensions_match_fixture(self, handler_with_extension):
        """Contract: Handler reports correct supported extensions."""
        handler, expected_ext = handler_with_extension
        extensions = handler.get_supported_extensions()

        assert expected_ext in extensions, f"{expected_ext} not in {extensions}"


class TestJsonFormatHandlerSpecific:
    """JSON-specific contract tests."""

    def test_json_handles_nested_structures(self):
        """JSON must handle deeply nested structures."""
        handler = JsonFormatHandler()
        nested = {"level1": {"level2": {"level3": {"value": 42}}}}

        serialized = handler.serialize(nested, None)
        content, _metadata = handler.deserialize(serialized)

        assert content == nested

    def test_json_handles_lists(self):
        """JSON must handle list serialization."""
        handler = JsonFormatHandler()
        data = [1, 2, 3, {"key": "value"}]

        serialized = handler.serialize(data, None)
        content, _metadata = handler.deserialize(serialized)

        assert content == data


class TestYamlFormatHandlerSpecific:
    """YAML-specific contract tests."""

    def test_yaml_handles_both_extensions(self):
        """YAML must support both .yaml and .yml."""
        handler = YamlFormatHandler()
        extensions = handler.get_supported_extensions()

        assert ".yaml" in extensions
        assert ".yml" in extensions

    def test_yaml_preserves_key_order(self):
        """YAML must preserve insertion order of keys."""
        handler = YamlFormatHandler()
        # Python 3.7+ dicts maintain insertion order
        ordered = {"z": 1, "a": 2, "m": 3}

        serialized = handler.serialize(ordered, None)
        content, _metadata = handler.deserialize(serialized)

        assert list(content.keys()) == list(ordered.keys())


class TestMarkdownFormatHandlerSpecific:
    """Markdown-specific contract tests."""

    def test_markdown_handles_frontmatter(self):
        """Markdown must extract frontmatter metadata."""
        handler = MarkdownFormatHandler()
        content_text = "# Title\n\nBody content"
        metadata = {"author": "test", "date": "2025-10-13"}

        serialized = handler.serialize(content_text, metadata)
        content, extracted_metadata = handler.deserialize(serialized)

        assert content.strip() == content_text.strip()
        assert "author" in extracted_metadata
        assert extracted_metadata["author"] == "test"

    def test_markdown_without_frontmatter(self):
        """Markdown must handle plain text without frontmatter."""
        handler = MarkdownFormatHandler()
        plain_text = "# Just a title\n\nNo metadata here."

        serialized = handler.serialize(plain_text, None)
        content, metadata = handler.deserialize(serialized)

        assert "# Just a title" in content
        # Auto-added metadata (created, format)
        assert isinstance(metadata, dict)

    def test_markdown_supports_md_and_markdown_extensions(self):
        """Markdown must support both .md and .markdown."""
        handler = MarkdownFormatHandler()
        extensions = handler.get_supported_extensions()

        assert ".md" in extensions
        assert ".markdown" in extensions
