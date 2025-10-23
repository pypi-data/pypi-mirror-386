"""Integration test for ManuscriptRepository.save(manuscript)

Spec: Repository layer should support rich domain entities directly
Focus: Type-safe save method with Manuscript entity
"""

from pathlib import Path

import pytest

from noveler.domain.entities.manuscript import Manuscript
from noveler.infrastructure.repositories.markdown_manuscript_repository import MarkdownManuscriptRepository


class TestManuscriptRepositorySaveMethod:
    """Integration test for Repository.save(manuscript: Manuscript)"""

    @pytest.fixture
    def manuscript_dir(self, tmp_path):
        """Temporary manuscript directory"""
        return tmp_path / "manuscripts"

    @pytest.fixture
    def repository(self, manuscript_dir):
        """Manuscript repository instance"""
        return MarkdownManuscriptRepository(manuscript_dir)

    def test_save_method_saves_manuscript_entity(self, repository, manuscript_dir):
        """save(manuscript) should persist Manuscript entity with metadata"""
        # Create manuscript entity
        manuscript = Manuscript.create_new(
            episode_number=1, content="Test manuscript content with sufficient length" * 5, session_id="test_session_001"
        )

        # Save using new save() method
        success = repository.save(manuscript)

        assert success is True

        # Verify file was created
        manuscript_file = manuscript_dir / "1.md"
        assert manuscript_file.exists()

        # Verify content
        saved_content = manuscript_file.read_text(encoding="utf-8")
        assert "Test manuscript content" in saved_content

        # Verify metadata in frontmatter
        assert "episode_number: 1" in saved_content
        assert "session_id: test_session_001" in saved_content
        assert "character_count:" in saved_content

    def test_save_method_preserves_metadata(self, repository, manuscript_dir):
        """save(manuscript) should preserve all metadata from to_metadata_dict()"""
        manuscript = Manuscript.create_new(
            episode_number=5, content="Content" * 30, session_id="session_12345"
        )

        repository.save(manuscript)

        # Load and verify metadata
        metadata = repository.get_manuscript_metadata(5)

        assert metadata is not None
        assert metadata["episode_number"] == 5
        assert metadata["session_id"] == "session_12345"
        assert "generated_at" in metadata
        assert metadata["character_count"] == len("Content" * 30)

    def test_save_method_overwrites_existing_manuscript(self, repository, manuscript_dir):
        """save(manuscript) should overwrite existing manuscript"""
        # First save
        manuscript1 = Manuscript.create_new(episode_number=1, content="Original content" * 10, session_id="session_001")
        repository.save(manuscript1)

        # Second save (same episode)
        manuscript2 = Manuscript.create_new(episode_number=1, content="Updated content" * 10, session_id="session_002")
        repository.save(manuscript2)

        # Verify latest content
        loaded_content = repository.get_manuscript(1)
        assert "Updated content" in loaded_content
        assert "Original content" not in loaded_content

        # Verify metadata updated
        metadata = repository.get_manuscript_metadata(1)
        assert metadata["session_id"] == "session_002"

    def test_save_method_vs_legacy_save_manuscript(self, repository, manuscript_dir):
        """save(manuscript) and save_manuscript() should both work"""
        # New method: save(manuscript)
        manuscript = Manuscript.create_new(episode_number=1, content="New method content" * 10, session_id="new_session")
        success_new = repository.save(manuscript)

        # Legacy method: save_manuscript(episode_number, content)
        success_legacy = repository.save_manuscript(2, "Legacy method content" * 10)

        assert success_new is True
        assert success_legacy is True

        # Both should create files
        assert (manuscript_dir / "1.md").exists()
        assert (manuscript_dir / "2.md").exists()

        # New method should have metadata, legacy may not
        metadata1 = repository.get_manuscript_metadata(1)
        assert metadata1 is not None
        assert "session_id" in metadata1

    def test_save_method_handles_special_characters_in_content(self, repository, manuscript_dir):
        """save(manuscript) should handle Japanese and special characters"""
        content = "日本語テスト\n改行含む\t タブ文字\n「括弧」『二重括弧』" * 5
        manuscript = Manuscript.create_new(episode_number=10, content=content, session_id="jp_session")

        success = repository.save(manuscript)
        assert success is True

        # Verify content preservation
        loaded = repository.get_manuscript(10)
        assert "日本語テスト" in loaded
        assert "「括弧」" in loaded
        assert "『二重括弧』" in loaded

    def test_save_method_creates_directory_if_not_exists(self, tmp_path):
        """save(manuscript) should create manuscript_dir if it doesn't exist"""
        non_existent_dir = tmp_path / "new" / "nested" / "dir"
        assert not non_existent_dir.exists()

        repository = MarkdownManuscriptRepository(non_existent_dir)
        manuscript = Manuscript.create_new(episode_number=1, content="Content" * 20, session_id="session_001")

        success = repository.save(manuscript)

        assert success is True
        assert non_existent_dir.exists()
        assert (non_existent_dir / "1.md").exists()
