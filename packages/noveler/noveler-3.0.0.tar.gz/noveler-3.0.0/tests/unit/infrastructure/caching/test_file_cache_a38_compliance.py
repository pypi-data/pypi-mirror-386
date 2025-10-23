#!/usr/bin/env python3
# File: tests/unit/infrastructure/caching/test_file_cache_a38_compliance.py
# Purpose: Unit tests for A38 config compliance in FileCache
# Context: B20 Phase 4 - Verify A38 pattern loading

"""Unit tests for FileCache A38 configuration compliance.

Verifies that FileGlobCacheService correctly loads manuscript
patterns from A38 configuration (no hardcoding).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from noveler.infrastructure.caching.file_cache_service import (
    A38_CONFIG_RELATIVE_PATH,
    DEFAULT_A38_MANUSCRIPT_PATTERN,
    FileGlobCacheService,
    _find_a38_config_path,
)


class TestA38ConfigLoading:
    """Test A38 configuration file loading."""

    def test_get_manuscript_pattern_from_a38_reads_config(self, tmp_path):
        """_get_manuscript_pattern_from_a38() should read config file."""
        # Create mock A38 config
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "a38_path_settings.yaml"
        config_file.write_text(
            """
naming_patterns:
  manuscript: "EP{episode:03d}_draft.md"
""",
            encoding="utf-8",
        )

        mock_logger = MagicMock()
        service = FileGlobCacheService(logger=mock_logger)

        # Patch the config path to our test config
        with patch(
            "noveler.infrastructure.caching.file_cache_service._find_a38_config_path",
            return_value=config_file,
        ):
            pattern = service._get_manuscript_pattern_from_a38()

        assert pattern == "EP{episode:03d}_draft.md"

    def test_fallback_on_missing_config(self):
        """Should use default pattern when config file not found."""
        mock_logger = MagicMock()
        service = FileGlobCacheService(logger=mock_logger)

        # Mock non-existent config path
        with patch(
            "noveler.infrastructure.caching.file_cache_service._find_a38_config_path",
            return_value=None,
        ):
            pattern = service._get_manuscript_pattern_from_a38()

        # Should return default pattern
        assert pattern == DEFAULT_A38_MANUSCRIPT_PATTERN
        mock_logger.warning.assert_called()

    def test_fallback_on_yaml_error(self, tmp_path):
        """Should use default pattern when YAML parsing fails."""
        mock_logger = MagicMock()
        service = FileGlobCacheService(logger=mock_logger)

        # Mock config file that exists but has invalid YAML
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        invalid_config = config_dir / "a38_path_settings.yaml"
        invalid_config.write_text("::invalid_yaml", encoding="utf-8")

        with patch(
            "noveler.infrastructure.caching.file_cache_service._find_a38_config_path",
            return_value=invalid_config,
        ):
            pattern = service._get_manuscript_pattern_from_a38()

        assert pattern == DEFAULT_A38_MANUSCRIPT_PATTERN
        mock_logger.warning.assert_called()


class TestFindA38ConfigPath:
    """Test helper that resolves A38 config location."""

    def test_returns_repo_config_path(self):
        """Helper should resolve repository config by default."""
        config_path = _find_a38_config_path()

        project_root = Path(__file__).resolve().parents[4]
        expected = (project_root / A38_CONFIG_RELATIVE_PATH).resolve()

        assert config_path is not None
        assert config_path.exists()
        assert config_path.resolve() == expected


class TestEpisodeFilePatternApplication:
    """Test episode file pattern application."""

    def test_get_episode_file_uses_a38_pattern(self, tmp_path):
        """get_episode_file_cached() should use A38 pattern."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        # Create file matching A38 pattern
        test_file = manuscript_dir / "第001話_テスト.md"
        test_file.write_text("test content", encoding="utf-8")

        mock_logger = MagicMock()
        service = FileGlobCacheService(logger=mock_logger)

        # Mock A38 config to return standard pattern
        with patch.object(
            service,
            "_get_manuscript_pattern_from_a38",
            return_value=DEFAULT_A38_MANUSCRIPT_PATTERN,
        ):
            result = service.get_episode_file_cached(manuscript_dir, episode_number=1)

        assert result is not None
        assert result.name == "第001話_テスト.md"

    def test_fallback_to_non_zero_padded_pattern(self, tmp_path):
        """Should fallback to non-zero-padded pattern if zero-padded not found."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        # Create file with non-zero-padded name
        test_file = manuscript_dir / "第1話_テスト.md"
        test_file.write_text("test content", encoding="utf-8")

        mock_logger = MagicMock()
        service = FileGlobCacheService(logger=mock_logger)

        with patch.object(
            service,
            "_get_manuscript_pattern_from_a38",
            return_value=DEFAULT_A38_MANUSCRIPT_PATTERN,
        ):
            result = service.get_episode_file_cached(manuscript_dir, episode_number=1)

        # Should find non-zero-padded version as fallback
        assert result is not None
        assert result.name == "第1話_テスト.md"


@pytest.mark.contract
class TestNoHardcodingContract:
    """B20 Contract: No hardcoded patterns."""

    def test_no_hardcoded_manuscript_pattern(self):
        """FileCache must not contain hardcoded '第*話_*.md' pattern."""
        import inspect

        from noveler.infrastructure.caching.file_cache_service import (
            FileGlobCacheService,
        )

        # Get source code of get_episode_file_cached
        source = inspect.getsource(FileGlobCacheService.get_episode_file_cached)

        # B20 Contract: Must call _get_manuscript_pattern_from_a38()
        assert "_get_manuscript_pattern_from_a38" in source, (
            "get_episode_file_cached must call _get_manuscript_pattern_from_a38()"
        )

        # B20 Contract: Must not hardcode the pattern
        assert '"第*話_*.md"' not in source, (
            "Hardcoded pattern found - must use A38 config"
        )
