#!/usr/bin/env python3
"""Tests for PathResolver (SPEC-YAML-021).

File: tests/unit/infrastructure/utils/test_path_resolver.py
Purpose: Validate array wildcard resolution and numeric aggregation functionality.
Context: Tests SPEC-YAML-021 implementation for validator path resolution.
"""

import pytest

from noveler.infrastructure.utils.path_resolver import (
    AggregationError,
    PathResolutionError,
    PathResolver,
    PathSegment,
)


class TestPathSegment:
    """Tests for PathSegment dataclass."""

    def test_simple_key(self) -> None:
        """Test creating a simple key segment."""
        segment = PathSegment(key="episodes")
        assert segment.key == "episodes"
        assert segment.is_wildcard is False
        assert segment.index is None

    def test_wildcard_segment(self) -> None:
        """Test creating a wildcard segment."""
        segment = PathSegment(key="items", is_wildcard=True)
        assert segment.key == "items"
        assert segment.is_wildcard is True
        assert segment.index is None

    def test_indexed_segment(self) -> None:
        """Test creating an indexed segment."""
        segment = PathSegment(key="episodes", index=0)
        assert segment.key == "episodes"
        assert segment.is_wildcard is False
        assert segment.index == 0

    def test_wildcard_and_index_conflict(self) -> None:
        """Test that wildcard and index are mutually exclusive."""
        with pytest.raises(ValueError, match="mutually exclusive"):
            PathSegment(key="items", is_wildcard=True, index=0)


class TestPathParsing:
    """Tests for path parsing."""

    def test_parse_simple_path(self) -> None:
        """Test parsing a simple dotted path."""
        segments = PathResolver.parse_path("metadata.title")
        assert len(segments) == 2
        assert segments[0] == PathSegment(key="metadata")
        assert segments[1] == PathSegment(key="title")

    def test_parse_array_wildcard(self) -> None:
        """Test parsing path with array wildcard."""
        segments = PathResolver.parse_path("episodes[*].word_count")
        assert len(segments) == 2
        assert segments[0] == PathSegment(key="episodes", is_wildcard=True)
        assert segments[1] == PathSegment(key="word_count")

    def test_parse_array_index(self) -> None:
        """Test parsing path with specific array index."""
        segments = PathResolver.parse_path("episodes[0].title")
        assert len(segments) == 2
        assert segments[0] == PathSegment(key="episodes", index=0)
        assert segments[1] == PathSegment(key="title")

    def test_parse_nested_wildcards(self) -> None:
        """Test parsing path with nested wildcards."""
        segments = PathResolver.parse_path("chapters[*].sections[*].hook")
        assert len(segments) == 3
        assert segments[0] == PathSegment(key="chapters", is_wildcard=True)
        assert segments[1] == PathSegment(key="sections", is_wildcard=True)
        assert segments[2] == PathSegment(key="hook")

    def test_parse_empty_path(self) -> None:
        """Test that empty path raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            PathResolver.parse_path("")

    def test_parse_invalid_syntax(self) -> None:
        """Test that invalid syntax raises ValueError."""
        with pytest.raises(ValueError, match="Invalid path segment"):
            PathResolver.parse_path("episodes[*")

    def test_parse_negative_index(self) -> None:
        """Test that negative indices are rejected."""
        with pytest.raises(ValueError, match="Negative indices"):
            PathResolver.parse_path("episodes[-1].title")


class TestPathResolution:
    """Tests for path resolution."""

    def test_resolve_simple_key(self) -> None:
        """Test resolving a simple nested key."""
        data = {"metadata": {"title": "Episode 1"}}
        result = PathResolver.resolve(data, "metadata.title")
        assert result == "Episode 1"

    def test_resolve_array_index(self) -> None:
        """Test resolving with specific array index."""
        data = {"episodes": [{"title": "第1話"}, {"title": "第2話"}]}
        result = PathResolver.resolve(data, "episodes[0].title")
        assert result == "第1話"

    def test_resolve_array_wildcard(self) -> None:
        """Test resolving with array wildcard."""
        data = {"episodes": [{"word_count": 4500}, {"word_count": 5200}, {"word_count": 3800}]}
        result = PathResolver.resolve(data, "episodes[*].word_count")
        assert result == [4500, 5200, 3800]

    def test_resolve_nested_wildcards(self) -> None:
        """Test resolving with nested wildcards."""
        data = {
            "chapters": [
                {"sections": [{"hook": True}, {"hook": False}]},
                {"sections": [{"hook": True}]},
            ]
        }
        result = PathResolver.resolve(data, "chapters[*].sections[*].hook")
        # Nested wildcards should be flattened
        assert result == [True, False, True]

    def test_resolve_key_not_found(self) -> None:
        """Test that missing key raises PathResolutionError on non-empty array."""
        data = {"episodes": [{"title": "第1話"}]}
        with pytest.raises(PathResolutionError, match="not found"):
            PathResolver.resolve(data, "episodes[*].invalid_field")

    def test_resolve_index_out_of_range(self) -> None:
        """Test that out-of-range index raises error."""
        data = {"episodes": [{"title": "第1話"}]}
        with pytest.raises(PathResolutionError, match="out of range"):
            PathResolver.resolve(data, "episodes[5].title")

    def test_resolve_wildcard_on_non_array(self) -> None:
        """Test that wildcard on non-array raises error."""
        data = {"metadata": {"title": "Episode"}}
        with pytest.raises(PathResolutionError, match="requires array"):
            PathResolver.resolve(data, "metadata[*].title")

    def test_resolve_empty_array_wildcard(self) -> None:
        """Test resolving wildcard on empty array."""
        data = {"episodes": []}
        result = PathResolver.resolve(data, "episodes[*].word_count")
        assert result == []


class TestAggregation:
    """Tests for numeric aggregation."""

    def test_aggregate_min(self) -> None:
        """Test minimum aggregation."""
        data = {"episodes": [{"word_count": 4500}, {"word_count": 5200}, {"word_count": 3800}]}
        result = PathResolver.aggregate(data, "episodes[*].word_count", "min")
        assert result == 3800

    def test_aggregate_max(self) -> None:
        """Test maximum aggregation."""
        data = {"episodes": [{"word_count": 4500}, {"word_count": 5200}, {"word_count": 3800}]}
        result = PathResolver.aggregate(data, "episodes[*].word_count", "max")
        assert result == 5200

    def test_aggregate_avg(self) -> None:
        """Test average aggregation."""
        data = {"episodes": [{"word_count": 4500}, {"word_count": 5200}, {"word_count": 3800}]}
        result = PathResolver.aggregate(data, "episodes[*].word_count", "avg")
        assert result == 4500.0

    def test_aggregate_avg_rounding(self) -> None:
        """Test that average is rounded to 2 decimal places."""
        data = {"items": [{"value": 1}, {"value": 2}, {"value": 3}]}
        result = PathResolver.aggregate(data, "items[*].value", "avg")
        assert result == 2.0

    def test_aggregate_empty_array(self) -> None:
        """Test aggregation on empty array returns None."""
        data = {"episodes": []}
        result = PathResolver.aggregate(data, "episodes[*].word_count", "min")
        assert result is None

    def test_aggregate_non_numeric_elements(self) -> None:
        """Test that non-numeric elements raise AggregationError."""
        data = {"items": [{"value": 1}, {"value": "not_a_number"}, {"value": 3}]}
        with pytest.raises(AggregationError, match="non-numeric"):
            PathResolver.aggregate(data, "items[*].value", "avg")

    def test_aggregate_single_value(self) -> None:
        """Test aggregation on single value (no wildcard)."""
        data = {"metadata": {"score": 85}}
        result = PathResolver.aggregate(data, "metadata.score", "min")
        assert result == 85

    def test_aggregate_nested_wildcards(self) -> None:
        """Test aggregation with nested wildcards."""
        data = {
            "chapters": [
                {"sections": [{"score": 80}, {"score": 90}]},
                {"sections": [{"score": 85}]},
            ]
        }
        result = PathResolver.aggregate(data, "chapters[*].sections[*].score", "avg")
        # (80 + 90 + 85) / 3 = 85.0
        assert result == 85.0

    def test_aggregate_invalid_function(self) -> None:
        """Test that invalid aggregation function raises ValueError."""
        data = {"items": [{"value": 1}]}
        with pytest.raises(ValueError, match="Unknown aggregation function"):
            PathResolver.aggregate(data, "items[*].value", "sum")  # type: ignore[arg-type]


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""

    def test_complex_nested_structure(self) -> None:
        """Test complex nested structure from SPEC-YAML-021 example."""
        data = {
            "episodes": [
                {
                    "title": "第1話",
                    "word_count": 4500,
                    "sections": [{"hook": True}, {"hook": False}],
                },
                {
                    "title": "第2話",
                    "word_count": 5200,
                    "sections": [{"hook": True}],
                },
                {
                    "title": "第3話",
                    "word_count": 3800,
                    "sections": [{"hook": False}],
                },
            ]
        }

        # Single value
        title = PathResolver.resolve(data, "episodes[0].title")
        assert title == "第1話"

        # Array wildcard
        word_counts = PathResolver.resolve(data, "episodes[*].word_count")
        assert word_counts == [4500, 5200, 3800]

        # Nested wildcard
        hooks = PathResolver.resolve(data, "episodes[*].sections[*].hook")
        assert hooks == [True, False, True, False]

        # Aggregation
        min_wc = PathResolver.aggregate(data, "episodes[*].word_count", "min")
        max_wc = PathResolver.aggregate(data, "episodes[*].word_count", "max")
        avg_wc = PathResolver.aggregate(data, "episodes[*].word_count", "avg")

        assert min_wc == 3800
        assert max_wc == 5200
        assert avg_wc == 4500.0


@pytest.mark.spec("SPEC-YAML-021")
class TestSPECYAML021Compliance:
    """Specification compliance tests for SPEC-YAML-021."""

    def test_spec_example_dotted_path(self) -> None:
        """Test SPEC example: metadata.title → data["metadata"]["title"]"""
        data = {"metadata": {"title": "Test Title"}}
        result = PathResolver.resolve(data, "metadata.title")
        assert result == "Test Title"

    def test_spec_example_array_index(self) -> None:
        """Test SPEC example: episodes[0].title → data["episodes"][0]["title"]"""
        data = {"episodes": [{"title": "Episode 1"}]}
        result = PathResolver.resolve(data, "episodes[0].title")
        assert result == "Episode 1"

    def test_spec_example_array_wildcard(self) -> None:
        """Test SPEC example: episodes[*].word_count → all word_count values"""
        data = {"episodes": [{"word_count": 100}, {"word_count": 200}]}
        result = PathResolver.resolve(data, "episodes[*].word_count")
        assert result == [100, 200]

    def test_spec_example_nested_wildcard(self) -> None:
        """Test SPEC example: chapters[*].sections[*].hook → flattened"""
        data = {
            "chapters": [
                {"sections": [{"hook": True}, {"hook": False}]},
                {"sections": [{"hook": True}]},
            ]
        }
        result = PathResolver.resolve(data, "chapters[*].sections[*].hook")
        assert result == [True, False, True]

    def test_spec_aggregation_min(self) -> None:
        """Test SPEC aggregation: PathResolver.aggregate(path, 'min')"""
        data = {"values": [{"x": 10}, {"x": 20}, {"x": 5}]}
        result = PathResolver.aggregate(data, "values[*].x", "min")
        assert result == 5

    def test_spec_aggregation_max(self) -> None:
        """Test SPEC aggregation: PathResolver.aggregate(path, 'max')"""
        data = {"values": [{"x": 10}, {"x": 20}, {"x": 5}]}
        result = PathResolver.aggregate(data, "values[*].x", "max")
        assert result == 20

    def test_spec_aggregation_avg(self) -> None:
        """Test SPEC aggregation: PathResolver.aggregate(path, 'avg')"""
        data = {"values": [{"x": 10}, {"x": 20}, {"x": 30}]}
        result = PathResolver.aggregate(data, "values[*].x", "avg")
        assert result == 20.0

    def test_spec_error_nonexistent_path(self) -> None:
        """Test SPEC error handling: nonexistent path returns PathResolutionError on non-empty array"""
        data = {"episodes": [{"title": "第1話"}]}
        with pytest.raises(PathResolutionError):
            PathResolver.resolve(data, "episodes[*].nonexistent")

    def test_spec_error_wildcard_on_non_array(self) -> None:
        """Test SPEC error handling: wildcard on non-array raises error"""
        data = {"metadata": {"title": "Test"}}
        with pytest.raises(PathResolutionError, match="requires array"):
            PathResolver.resolve(data, "metadata[*].title")

    def test_spec_error_empty_aggregation(self) -> None:
        """Test SPEC error handling: empty array aggregation returns None"""
        data = {"episodes": []}
        result = PathResolver.aggregate(data, "episodes[*].word_count", "avg")
        assert result is None
