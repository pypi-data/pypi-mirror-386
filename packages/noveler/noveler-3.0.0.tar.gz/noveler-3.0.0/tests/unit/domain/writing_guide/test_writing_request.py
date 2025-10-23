# File: tests/unit/domain/writing_guide/test_writing_request.py
# Purpose: Unit tests for WritingRequest Value Object
# Context: Tests domain invariants, business logic, and factory methods

import pytest
from noveler.domain.writing_guide.models.writing_request import WritingRequest, DetailLevel


class TestWritingRequestConstruction:
    """Tests for WritingRequest construction and validation."""

    def test_valid_request_construction(self) -> None:
        """Verify valid request can be constructed."""
        request = WritingRequest(
            genre="fantasy",
            word_count="2000-3000",
            viewpoint="一人称",
            viewpoint_character="主人公",
            difficulty="standard",
            priority="high",
            detail_level=DetailLevel.STEPWISE,
        )
        assert request.genre == "fantasy"
        assert request.word_count == "2000-3000"
        assert request.detail_level == DetailLevel.STEPWISE

    def test_empty_genre_raises_error(self) -> None:
        """Verify empty genre violates domain invariant."""
        with pytest.raises(ValueError, match="Genre must not be empty"):
            WritingRequest(
                genre="",
                word_count="2000-3000",
                viewpoint="一人称",
                viewpoint_character="主人公",
                difficulty="standard",
                priority="high",
                detail_level=DetailLevel.STANDARD,
            )

    def test_whitespace_genre_raises_error(self) -> None:
        """Verify whitespace-only genre violates domain invariant."""
        with pytest.raises(ValueError, match="Genre must not be empty"):
            WritingRequest(
                genre="   ",
                word_count="2000-3000",
                viewpoint="一人称",
                viewpoint_character="主人公",
                difficulty="standard",
                priority="high",
                detail_level=DetailLevel.STANDARD,
            )

    def test_invalid_word_count_format_raises_error(self) -> None:
        """Verify invalid word_count format is rejected."""
        with pytest.raises(ValueError, match="Invalid word_count format"):
            WritingRequest(
                genre="fantasy",
                word_count="invalid_format",
                viewpoint="一人称",
                viewpoint_character="主人公",
                difficulty="standard",
                priority="high",
                detail_level=DetailLevel.STANDARD,
            )

    def test_valid_word_count_formats(self) -> None:
        """Verify various valid word_count formats are accepted."""
        valid_formats = ["2000-3000", "100-999", "10000-20000"]
        for word_count in valid_formats:
            request = WritingRequest(
                genre="fantasy",
                word_count=word_count,
                viewpoint="一人称",
                viewpoint_character="主人公",
                difficulty="standard",
                priority="high",
                detail_level=DetailLevel.STANDARD,
            )
            assert request.word_count == word_count


class TestWritingRequestBusinessLogic:
    """Tests for WritingRequest business logic methods."""

    def test_requires_stepwise_guidance_returns_true_for_stepwise_level(self) -> None:
        """Verify stepwise detail level triggers stepwise guidance."""
        request = WritingRequest(
            genre="fantasy",
            word_count="2000-3000",
            viewpoint="一人称",
            viewpoint_character="主人公",
            difficulty="standard",
            priority="high",
            detail_level=DetailLevel.STEPWISE,
        )
        assert request.requires_stepwise_guidance() is True

    def test_requires_stepwise_guidance_returns_false_for_standard_level(self) -> None:
        """Verify standard detail level does not trigger stepwise guidance."""
        request = WritingRequest(
            genre="fantasy",
            word_count="2000-3000",
            viewpoint="一人称",
            viewpoint_character="主人公",
            difficulty="standard",
            priority="high",
            detail_level=DetailLevel.STANDARD,
        )
        assert request.requires_stepwise_guidance() is False

    def test_is_high_priority_returns_true_for_high(self) -> None:
        """Verify high priority is correctly identified."""
        request = WritingRequest(
            genre="fantasy",
            word_count="2000-3000",
            viewpoint="一人称",
            viewpoint_character="主人公",
            difficulty="standard",
            priority="high",
            detail_level=DetailLevel.STANDARD,
        )
        assert request.is_high_priority() is True

    def test_is_high_priority_returns_false_for_medium(self) -> None:
        """Verify medium priority is not high priority."""
        request = WritingRequest(
            genre="fantasy",
            word_count="2000-3000",
            viewpoint="一人称",
            viewpoint_character="主人公",
            difficulty="standard",
            priority="medium",
            detail_level=DetailLevel.STANDARD,
        )
        assert request.is_high_priority() is False

    def test_has_custom_requirements_returns_true_when_present(self) -> None:
        """Verify custom requirements are detected."""
        request = WritingRequest(
            genre="fantasy",
            word_count="2000-3000",
            viewpoint="一人称",
            viewpoint_character="主人公",
            difficulty="standard",
            priority="high",
            detail_level=DetailLevel.STANDARD,
            custom_requirements=["Requirement 1", "Requirement 2"],
        )
        assert request.has_custom_requirements() is True

    def test_has_custom_requirements_returns_false_when_none(self) -> None:
        """Verify absence of custom requirements is detected."""
        request = WritingRequest(
            genre="fantasy",
            word_count="2000-3000",
            viewpoint="一人称",
            viewpoint_character="主人公",
            difficulty="standard",
            priority="high",
            detail_level=DetailLevel.STANDARD,
            custom_requirements=None,
        )
        assert request.has_custom_requirements() is False

    def test_has_custom_requirements_returns_false_for_empty_list(self) -> None:
        """Verify empty custom requirements list is treated as absent."""
        request = WritingRequest(
            genre="fantasy",
            word_count="2000-3000",
            viewpoint="一人称",
            viewpoint_character="主人公",
            difficulty="standard",
            priority="high",
            detail_level=DetailLevel.STANDARD,
            custom_requirements=[],
        )
        assert request.has_custom_requirements() is False


class TestWritingRequestFactoryMethods:
    """Tests for WritingRequest factory methods."""

    def test_create_default_returns_valid_request(self) -> None:
        """Verify factory method creates valid default request."""
        request = WritingRequest.create_default(genre="science_fiction")
        assert request.genre == "science_fiction"
        assert request.word_count == "4000-6000"
        assert request.viewpoint == "三人称単元視点"
        assert request.viewpoint_character == "主人公"
        assert request.difficulty == "beginner"
        assert request.priority == "critical"
        assert request.detail_level == DetailLevel.STANDARD

    def test_create_default_with_genre_override(self) -> None:
        """Verify factory method respects genre override."""
        request = WritingRequest.create_default(genre="mystery")
        assert request.genre == "mystery"
        # Defaults still apply to non-overridden fields
        assert request.word_count == "4000-6000"
        assert request.difficulty == "beginner"
        assert request.priority == "critical"
        assert request.detail_level == DetailLevel.STANDARD


class TestWritingRequestImmutability:
    """Tests for WritingRequest immutability (frozen dataclass)."""

    def test_genre_is_immutable(self) -> None:
        """Verify genre field cannot be modified after construction."""
        request = WritingRequest(
            genre="fantasy",
            word_count="2000-3000",
            viewpoint="一人称",
            viewpoint_character="主人公",
            difficulty="standard",
            priority="high",
            detail_level=DetailLevel.STANDARD,
        )
        with pytest.raises(AttributeError):
            request.genre = "mystery"  # type: ignore[misc]

    def test_detail_level_is_immutable(self) -> None:
        """Verify detail_level field cannot be modified after construction."""
        request = WritingRequest(
            genre="fantasy",
            word_count="2000-3000",
            viewpoint="一人称",
            viewpoint_character="主人公",
            difficulty="standard",
            priority="high",
            detail_level=DetailLevel.STANDARD,
        )
        with pytest.raises(AttributeError):
            request.detail_level = DetailLevel.STEPWISE  # type: ignore[misc]


class TestWritingRequestEquality:
    """Tests for WritingRequest value equality (frozen dataclass)."""

    def test_equal_requests_are_equal(self) -> None:
        """Verify requests with identical values are equal."""
        request1 = WritingRequest(
            genre="fantasy",
            word_count="2000-3000",
            viewpoint="一人称",
            viewpoint_character="主人公",
            difficulty="standard",
            priority="high",
            detail_level=DetailLevel.STANDARD,
        )
        request2 = WritingRequest(
            genre="fantasy",
            word_count="2000-3000",
            viewpoint="一人称",
            viewpoint_character="主人公",
            difficulty="standard",
            priority="high",
            detail_level=DetailLevel.STANDARD,
        )
        assert request1 == request2

    def test_different_genre_not_equal(self) -> None:
        """Verify requests with different genres are not equal."""
        request1 = WritingRequest(
            genre="fantasy",
            word_count="2000-3000",
            viewpoint="一人称",
            viewpoint_character="主人公",
            difficulty="standard",
            priority="high",
            detail_level=DetailLevel.STANDARD,
        )
        request2 = WritingRequest(
            genre="mystery",
            word_count="2000-3000",
            viewpoint="一人称",
            viewpoint_character="主人公",
            difficulty="standard",
            priority="high",
            detail_level=DetailLevel.STANDARD,
        )
        assert request1 != request2

    def test_hashable_for_set_operations(self) -> None:
        """Verify frozen request can be used in sets and dicts."""
        request = WritingRequest(
            genre="fantasy",
            word_count="2000-3000",
            viewpoint="一人称",
            viewpoint_character="主人公",
            difficulty="standard",
            priority="high",
            detail_level=DetailLevel.STANDARD,
        )
        request_set = {request}
        assert request in request_set
