# File: tests/unit/infrastructure/repositories/test_session_manifest_repository.py
# Purpose: Comprehensive tests for SessionManifestRepository
# Context: Contract tests + unit tests + edge cases for manifest persistence

import pytest
import json
from pathlib import Path
from noveler.infrastructure.repositories.session_manifest_repository import SessionManifestRepository


# ============================================================================
# Contract Tests - ISessionManifestRepository Protocol Compliance
# ============================================================================


class TestSessionManifestRepositoryContract:
    """Contract tests for ISessionManifestRepository protocol compliance."""

    def test_read_manifest_returns_dict(self, tmp_path: Path) -> None:
        """Contract: read_manifest() must return dict."""
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text('{"session_id": "test"}', encoding="utf-8")

        repo = SessionManifestRepository()
        result = repo.read_manifest(manifest_file)

        assert isinstance(result, dict), "read_manifest must return dict"

    def test_write_manifest_accepts_dict(self, tmp_path: Path) -> None:
        """Contract: write_manifest() must accept dict without raising."""
        manifest_file = tmp_path / "manifest.json"
        repo = SessionManifestRepository()

        data = {"session_id": "test", "episode_number": 1}
        repo.write_manifest(manifest_file, data)  # Should not raise

    def test_read_manifest_raises_on_missing_file(self, tmp_path: Path) -> None:
        """Contract: read_manifest() must raise FileNotFoundError if file missing."""
        repo = SessionManifestRepository()
        nonexistent = tmp_path / "missing.json"

        with pytest.raises(FileNotFoundError):
            repo.read_manifest(nonexistent)


# ============================================================================
# Unit Tests - SessionManifestRepository Implementation
# ============================================================================


class TestSessionManifestRepositoryUnit:
    """Unit tests for SessionManifestRepository implementation."""

    def test_write_creates_parent_directories(self, tmp_path: Path) -> None:
        """write_manifest() should create parent directories automatically."""
        nested_dir = tmp_path / "deeply" / "nested" / "path"
        manifest_file = nested_dir / "manifest.json"

        repo = SessionManifestRepository()
        repo.write_manifest(manifest_file, {"session_id": "test"})

        assert manifest_file.exists()
        assert nested_dir.exists()

    def test_write_then_read_roundtrip(self, tmp_path: Path) -> None:
        """Writing then reading should preserve data exactly."""
        manifest_file = tmp_path / "manifest.json"
        original_data = {
            "session_id": "episode_001",
            "session_start_ts": "2025-10-04T12:30:00+09:00",
            "session_start_compact": "202510041230",
            "episode_number": 1,
            "metadata": {"author": "test_user"},
        }

        repo = SessionManifestRepository()
        repo.write_manifest(manifest_file, original_data)
        loaded_data = repo.read_manifest(manifest_file)

        assert loaded_data == original_data

    def test_write_preserves_utf8_characters(self, tmp_path: Path) -> None:
        """write_manifest() should preserve Japanese characters."""
        manifest_file = tmp_path / "manifest.json"
        japanese_data = {
            "session_id": "エピソード001",
            "project_name": "小説プロジェクト",
            "metadata": {"author": "山田太郎"},
        }

        repo = SessionManifestRepository()
        repo.write_manifest(manifest_file, japanese_data)
        loaded_data = repo.read_manifest(manifest_file)

        assert loaded_data["session_id"] == "エピソード001"
        assert loaded_data["project_name"] == "小説プロジェクト"
        assert loaded_data["metadata"]["author"] == "山田太郎"

    def test_write_formats_json_with_indent(self, tmp_path: Path) -> None:
        """write_manifest() should format JSON with indent=2 for readability."""
        manifest_file = tmp_path / "manifest.json"
        data = {"session_id": "test", "nested": {"key": "value"}}

        repo = SessionManifestRepository()
        repo.write_manifest(manifest_file, data)

        # Read raw content to check formatting
        raw_content = manifest_file.read_text(encoding="utf-8")

        # Should have newlines (not minified)
        assert "\n" in raw_content
        # Should have indentation
        assert "  " in raw_content  # 2-space indent

    def test_read_raises_on_invalid_json(self, tmp_path: Path) -> None:
        """read_manifest() should raise JSONDecodeError on invalid JSON."""
        manifest_file = tmp_path / "invalid.json"
        manifest_file.write_text("{invalid json}", encoding="utf-8")

        repo = SessionManifestRepository()

        with pytest.raises(json.JSONDecodeError):
            repo.read_manifest(manifest_file)

    def test_read_raises_on_non_dict_root(self, tmp_path: Path) -> None:
        """read_manifest() should raise ValueError if JSON root is not dict."""
        manifest_file = tmp_path / "array.json"
        manifest_file.write_text('["not", "a", "dict"]', encoding="utf-8")

        repo = SessionManifestRepository()

        with pytest.raises(ValueError, match="Manifest root must be dict"):
            repo.read_manifest(manifest_file)

    def test_write_overwrites_existing_file(self, tmp_path: Path) -> None:
        """write_manifest() should overwrite existing file."""
        manifest_file = tmp_path / "manifest.json"

        repo = SessionManifestRepository()

        # Write first version
        repo.write_manifest(manifest_file, {"version": 1})
        first_read = repo.read_manifest(manifest_file)
        assert first_read["version"] == 1

        # Overwrite with second version
        repo.write_manifest(manifest_file, {"version": 2})
        second_read = repo.read_manifest(manifest_file)
        assert second_read["version"] == 2
        assert "version" in second_read  # Should only have new data

    def test_read_loads_complex_nested_structure(self, tmp_path: Path) -> None:
        """read_manifest() should handle complex nested structures."""
        manifest_file = tmp_path / "complex.json"
        complex_data = {
            "session_id": "test",
            "metadata": {
                "tags": ["fantasy", "adventure"],
                "counts": {"chapters": 10, "words": 50000},
                "nested": {"deeply": {"nested": {"value": "found"}}},
            },
        }

        repo = SessionManifestRepository()
        repo.write_manifest(manifest_file, complex_data)
        loaded = repo.read_manifest(manifest_file)

        assert loaded["metadata"]["tags"] == ["fantasy", "adventure"]
        assert loaded["metadata"]["counts"]["words"] == 50000
        assert loaded["metadata"]["nested"]["deeply"]["nested"]["value"] == "found"

    def test_write_raises_on_non_serializable_object(self, tmp_path: Path) -> None:
        """write_manifest() should raise TypeError on non-JSON-serializable data."""
        manifest_file = tmp_path / "manifest.json"

        class CustomObject:
            pass

        data = {"session_id": "test", "custom": CustomObject()}

        repo = SessionManifestRepository()

        with pytest.raises(TypeError):
            repo.write_manifest(manifest_file, data)


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestSessionManifestRepositoryEdgeCases:
    """Edge case tests for SessionManifestRepository."""

    def test_empty_dict(self, tmp_path: Path) -> None:
        """write_manifest() should handle empty dict gracefully."""
        manifest_file = tmp_path / "empty.json"

        repo = SessionManifestRepository()
        repo.write_manifest(manifest_file, {})
        loaded = repo.read_manifest(manifest_file)

        assert loaded == {}

    def test_very_large_manifest(self, tmp_path: Path) -> None:
        """write_manifest() should handle large manifests (stress test)."""
        manifest_file = tmp_path / "large.json"

        # Create large manifest with 1000 entries
        large_data = {
            "session_id": "test",
            "steps": {f"step_{i}": {"completed": i % 2 == 0} for i in range(1000)},
        }

        repo = SessionManifestRepository()
        repo.write_manifest(manifest_file, large_data)
        loaded = repo.read_manifest(manifest_file)

        assert len(loaded["steps"]) == 1000
        assert loaded["steps"]["step_999"]["completed"] is False  # 999 is odd

    def test_special_characters_in_values(self, tmp_path: Path) -> None:
        """write_manifest() should handle special characters correctly."""
        manifest_file = tmp_path / "special.json"
        special_data = {
            "quotes": 'He said "hello"',
            "backslashes": "C:\\Users\\path",
            "newlines": "line1\nline2",
            "unicode": "🔥📚✨",
            "emoji_japanese": "こんにちは😊",
        }

        repo = SessionManifestRepository()
        repo.write_manifest(manifest_file, special_data)
        loaded = repo.read_manifest(manifest_file)

        assert loaded["quotes"] == 'He said "hello"'
        assert loaded["backslashes"] == "C:\\Users\\path"
        assert loaded["newlines"] == "line1\nline2"
        assert loaded["unicode"] == "🔥📚✨"
        assert loaded["emoji_japanese"] == "こんにちは😊"

    def test_read_file_without_utf8_bom(self, tmp_path: Path) -> None:
        """read_manifest() should handle UTF-8 files without BOM."""
        manifest_file = tmp_path / "no_bom.json"

        # Write without BOM (default Python behavior)
        with manifest_file.open("w", encoding="utf-8") as f:
            json.dump({"test": "日本語"}, f, ensure_ascii=False)

        repo = SessionManifestRepository()
        loaded = repo.read_manifest(manifest_file)

        assert loaded["test"] == "日本語"

    def test_concurrent_writes_last_write_wins(self, tmp_path: Path) -> None:
        """Multiple writes should follow last-write-wins semantics."""
        manifest_file = tmp_path / "concurrent.json"

        repo = SessionManifestRepository()

        # Simulate concurrent writes
        repo.write_manifest(manifest_file, {"write": 1})
        repo.write_manifest(manifest_file, {"write": 2})
        repo.write_manifest(manifest_file, {"write": 3})

        loaded = repo.read_manifest(manifest_file)
        assert loaded["write"] == 3  # Last write wins
