"""DDD compliance tests for EpisodeNumber Value Object validation.

Tests episode number validation across Application layer use cases.
Ensures domain rules (1 ≤ episode_number ≤ 9999) are enforced.
"""

import pytest

from noveler.application.use_cases.quality_check_command_use_case import (
    QualityCheckCommandRequest,
    QualityCheckCommandUseCase,
    QualityCheckTarget,
)
from noveler.domain.value_objects.episode_number import EpisodeNumber


class MockEpisodeRepository:
    """Mock episode repository for testing."""

    def get_episode_info(self, project_name: str, episode_number: int):
        """Return mock episode info."""
        return {
            "number": episode_number,
            "title": f"Episode {episode_number}",
            "content": "Test content",
            "project_name": project_name,
        }

    def get_all_episodes(self, project_name: str):
        """Return mock episodes list."""
        return [
            {"number": 1, "title": "Episode 1", "content": "Test content 1"},
            {"number": 2, "title": "Episode 2", "content": "Test content 2"},
        ]

    def get_episodes_in_range(self, project_name: str, start_episode: int, end_episode: int):
        """Return mock episode range."""
        return [
            {"number": i, "title": f"Episode {i}", "content": f"Test content {i}"}
            for i in range(start_episode, end_episode + 1)
        ]

    def get_latest_episode(self, project_name: str):
        """Return mock latest episode."""
        return {"number": 5, "title": "Episode 5", "content": "Test content 5"}


class MockQualityCheckRepository:
    """Mock quality check repository for testing."""

    def check_quality(self, project_name: str, episode_number: int, content: str):
        """Return mock quality check result."""
        from noveler.domain.value_objects.completion_status import QualityCheckResult
        from noveler.domain.value_objects.quality_score import QualityScore

        return QualityCheckResult(
            score=QualityScore(80),
            passed=True,
            issues=[],
        )

    def get_quality_threshold(self):
        """Return mock quality threshold."""
        from noveler.domain.value_objects.quality_score import QualityScore

        return QualityScore(70)


class MockQualityRecordRepository:
    """Mock quality record repository for testing."""

    def save_check_result(self, record: dict):
        """Mock save operation."""
        pass


class TestEpisodeNumberValidation:
    """Test suite for EpisodeNumber Value Object validation in Application layer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.episode_repo = MockEpisodeRepository()
        self.quality_check_repo = MockQualityCheckRepository()
        self.quality_record_repo = MockQualityRecordRepository()

        self.use_case = QualityCheckCommandUseCase(
            quality_check_repository=self.quality_check_repo,
            quality_record_repository=self.quality_record_repo,
            episode_repository=self.episode_repo,
        )

    def test_valid_episode_number_single_check(self):
        """Valid episode number should pass validation."""
        request = QualityCheckCommandRequest(
            project_name="test_project",
            target=QualityCheckTarget.SINGLE,
            episode_number=1,
        )

        response = self.use_case.execute(request)

        assert response.success is True
        assert response.error_message is None

    def test_episode_number_below_minimum_single_check(self):
        """Episode number below 1 should fail validation."""
        request = QualityCheckCommandRequest(
            project_name="test_project",
            target=QualityCheckTarget.SINGLE,
            episode_number=0,
        )

        response = self.use_case.execute(request)

        assert response.success is False
        assert "1以上である必要があります" in response.error_message

    def test_episode_number_negative_single_check(self):
        """Negative episode number should fail validation."""
        request = QualityCheckCommandRequest(
            project_name="test_project",
            target=QualityCheckTarget.SINGLE,
            episode_number=-1,
        )

        response = self.use_case.execute(request)

        assert response.success is False
        assert "1以上である必要があります" in response.error_message

    def test_episode_number_above_maximum_single_check(self):
        """Episode number above 9999 should fail validation."""
        request = QualityCheckCommandRequest(
            project_name="test_project",
            target=QualityCheckTarget.SINGLE,
            episode_number=10000,
        )

        response = self.use_case.execute(request)

        assert response.success is False
        assert "9999以下である必要があります" in response.error_message

    def test_episode_number_at_boundary_values(self):
        """Episode numbers at boundaries (1, 9999) should pass validation."""
        # Test minimum boundary
        request_min = QualityCheckCommandRequest(
            project_name="test_project",
            target=QualityCheckTarget.SINGLE,
            episode_number=1,
        )

        response_min = self.use_case.execute(request_min)
        assert response_min.success is True

        # Test maximum boundary
        request_max = QualityCheckCommandRequest(
            project_name="test_project",
            target=QualityCheckTarget.SINGLE,
            episode_number=9999,
        )

        response_max = self.use_case.execute(request_max)
        assert response_max.success is True

    def test_valid_episode_range_check(self):
        """Valid episode range should pass validation."""
        request = QualityCheckCommandRequest(
            project_name="test_project",
            target=QualityCheckTarget.RANGE,
            start_episode=1,
            end_episode=5,
        )

        response = self.use_case.execute(request)

        assert response.success is True
        assert response.error_message is None

    def test_invalid_start_episode_range_check(self):
        """Invalid start episode in range should fail validation."""
        request = QualityCheckCommandRequest(
            project_name="test_project",
            target=QualityCheckTarget.RANGE,
            start_episode=0,
            end_episode=5,
        )

        response = self.use_case.execute(request)

        assert response.success is False
        assert "1以上である必要があります" in response.error_message

    def test_invalid_end_episode_range_check(self):
        """Invalid end episode in range should fail validation."""
        request = QualityCheckCommandRequest(
            project_name="test_project",
            target=QualityCheckTarget.RANGE,
            start_episode=1,
            end_episode=10000,
        )

        response = self.use_case.execute(request)

        assert response.success is False
        assert "9999以下である必要があります" in response.error_message


class TestEpisodeNumberValueObjectDirectValidation:
    """Test EpisodeNumber Value Object validation directly."""

    def test_valid_episode_number_creation(self):
        """Valid episode numbers should create Value Object successfully."""
        episode_number = EpisodeNumber(1)
        assert episode_number.value == 1

        episode_number = EpisodeNumber(9999)
        assert episode_number.value == 9999

    def test_invalid_episode_number_below_minimum(self):
        """Episode number below 1 should raise ValueError."""
        with pytest.raises(ValueError, match="1以上である必要があります"):
            EpisodeNumber(0)

        with pytest.raises(ValueError, match="1以上である必要があります"):
            EpisodeNumber(-1)

    def test_invalid_episode_number_above_maximum(self):
        """Episode number above 9999 should raise ValueError."""
        with pytest.raises(ValueError, match="9999以下である必要があります"):
            EpisodeNumber(10000)

    def test_non_integer_episode_number(self):
        """Non-integer episode number should raise ValueError."""
        with pytest.raises(ValueError, match="整数である必要があります"):
            EpisodeNumber("1")  # type: ignore

        with pytest.raises(ValueError, match="整数である必要があります"):
            EpisodeNumber(1.5)  # type: ignore

    def test_episode_number_immutability(self):
        """EpisodeNumber should be immutable."""
        episode_number = EpisodeNumber(1)

        with pytest.raises(Exception):  # dataclass(frozen=True) raises FrozenInstanceError
            episode_number.value = 2  # type: ignore

    def test_episode_number_next_method(self):
        """next() method should return next episode number."""
        episode_number = EpisodeNumber(1)
        next_episode = episode_number.next()

        assert next_episode.value == 2
        assert episode_number.value == 1  # Original unchanged

    def test_episode_number_previous_method(self):
        """previous() method should return previous episode number."""
        episode_number = EpisodeNumber(2)
        previous_episode = episode_number.previous()

        assert previous_episode.value == 1
        assert episode_number.value == 2  # Original unchanged

    def test_episode_number_next_at_maximum_boundary(self):
        """next() at maximum boundary should raise ValueError."""
        episode_number = EpisodeNumber(9999)

        with pytest.raises(ValueError, match="9999以下である必要があります"):
            episode_number.next()

    def test_episode_number_previous_at_minimum_boundary(self):
        """previous() at minimum boundary should raise ValueError."""
        episode_number = EpisodeNumber(1)

        with pytest.raises(ValueError, match="前のエピソードはありません"):
            episode_number.previous()
