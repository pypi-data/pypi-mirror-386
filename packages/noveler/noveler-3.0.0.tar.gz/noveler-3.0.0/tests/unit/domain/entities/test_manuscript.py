"""Test for Manuscript Entity

Spec: Anemic Domain Model elimination
Focus: Immutability and business logic encapsulation
"""

import pytest

from noveler.domain.entities.manuscript import Manuscript
from noveler.domain.value_objects.project_time import project_now


class TestManuscriptImmutability:
    """Test Manuscript entity immutability (frozen=True)"""

    def test_manuscript_is_frozen(self):
        """Manuscript should be immutable (@dataclass(frozen=True))"""
        manuscript = Manuscript.create_new(
            episode_number=1, content="Test content for manuscript", session_id="test_session_001"
        )

        # Verify read access works
        assert manuscript.episode_number == 1
        assert manuscript.content == "Test content for manuscript"
        assert manuscript.session_id == "test_session_001"

        # Verify write access is forbidden (frozen dataclass)
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            manuscript.episode_number = 2

        with pytest.raises(Exception):
            manuscript.content = "Modified content"

        with pytest.raises(Exception):
            manuscript.session_id = "new_session"

    def test_manuscript_content_cannot_be_mutated(self):
        """Content field should not be modifiable after creation"""
        content = "Original manuscript content"
        manuscript = Manuscript.create_new(episode_number=1, content=content, session_id="session_001")

        with pytest.raises(Exception):
            manuscript.content = "Attempted modification"

        # Original content should remain unchanged
        assert manuscript.content == content


class TestManuscriptBusinessLogic:
    """Test business logic encapsulation in Manuscript entity"""

    def test_is_publishable_returns_true_for_valid_manuscript(self):
        """Publishable manuscript: sufficient length + meaningful content"""
        # MIN_CONTENT_LENGTH = 100
        content = "あ" * 150  # 150 characters
        manuscript = Manuscript.create_new(episode_number=1, content=content, session_id="session_001")

        assert manuscript.is_publishable() is True

    def test_is_publishable_returns_false_for_short_manuscript(self):
        """Short manuscript (< MIN_CONTENT_LENGTH) is not publishable"""
        content = "Short"  # 5 characters
        manuscript = Manuscript.create_new(episode_number=1, content=content, session_id="session_001")

        assert manuscript.is_publishable() is False

    def test_is_publishable_returns_false_for_whitespace_only(self):
        """Whitespace-only manuscript is not publishable"""
        content = " " * 200  # 200 spaces
        manuscript = Manuscript.create_new(episode_number=1, content=content, session_id="session_001")

        assert manuscript.is_publishable() is False

    def test_is_sufficient_length_checks_min_content_length(self):
        """is_sufficient_length should check MIN_CONTENT_LENGTH constant"""
        # Just at threshold (100 characters stripped)
        manuscript = Manuscript.create_new(episode_number=1, content="あ" * 100, session_id="session_001")
        assert manuscript.is_sufficient_length() is True

        # Just below threshold (99 characters stripped)
        manuscript = Manuscript.create_new(episode_number=1, content="あ" * 99, session_id="session_001")
        assert manuscript.is_sufficient_length() is False

    def test_get_character_count_returns_accurate_count(self):
        """get_character_count should return total character count"""
        content = "日本語テスト\n改行含む"
        manuscript = Manuscript.create_new(episode_number=1, content=content, session_id="session_001")

        assert manuscript.get_character_count() == len(content)

    def test_get_stripped_character_count_excludes_whitespace(self):
        """get_stripped_character_count should exclude leading/trailing whitespace"""
        content = "   content with spaces   \n"
        manuscript = Manuscript.create_new(episode_number=1, content=content, session_id="session_001")

        assert manuscript.get_stripped_character_count() == len(content.strip())

    def test_to_metadata_dict_contains_required_fields(self):
        """to_metadata_dict should include all required metadata fields"""
        manuscript = Manuscript.create_new(episode_number=5, content="Test content", session_id="session_123")

        metadata = manuscript.to_metadata_dict()

        assert "episode_number" in metadata
        assert metadata["episode_number"] == 5
        assert "generated_at" in metadata
        assert "session_id" in metadata
        assert metadata["session_id"] == "session_123"
        assert "character_count" in metadata
        assert metadata["character_count"] == len("Test content")


class TestManuscriptFactoryMethod:
    """Test Manuscript.create_new factory method"""

    def test_create_new_sets_generated_at_to_current_time(self):
        """create_new should set generated_at to current project time"""
        before = project_now()
        manuscript = Manuscript.create_new(episode_number=1, content="Test", session_id="session_001")
        after = project_now()

        assert before <= manuscript.generated_at <= after

    def test_create_new_validates_episode_number(self):
        """create_new should validate episode_number >= 1"""
        # Valid episode number
        manuscript = Manuscript.create_new(episode_number=1, content="Test", session_id="session_001")
        assert manuscript.episode_number == 1

        # Invalid episode number (zero)
        with pytest.raises(ValueError, match="Episode number must be >= 1"):
            Manuscript.create_new(episode_number=0, content="Test", session_id="session_001")

        # Invalid episode number (negative)
        with pytest.raises(ValueError, match="Episode number must be >= 1"):
            Manuscript.create_new(episode_number=-1, content="Test", session_id="session_001")

    def test_create_new_validates_session_id(self):
        """create_new should validate session_id is not empty"""
        # Valid session ID
        manuscript = Manuscript.create_new(episode_number=1, content="Test", session_id="valid_session")
        assert manuscript.session_id == "valid_session"

        # Invalid session ID (empty)
        with pytest.raises(ValueError, match="Session ID cannot be empty"):
            Manuscript.create_new(episode_number=1, content="Test", session_id="")

        # Invalid session ID (whitespace only)
        with pytest.raises(ValueError, match="Session ID cannot be empty"):
            Manuscript.create_new(episode_number=1, content="Test", session_id="   ")

    def test_get_filename_returns_episode_number_string(self):
        """get_filename should return episode number as string"""
        manuscript = Manuscript.create_new(episode_number=42, content="Test", session_id="session_001")

        assert manuscript.get_filename() == "42"
