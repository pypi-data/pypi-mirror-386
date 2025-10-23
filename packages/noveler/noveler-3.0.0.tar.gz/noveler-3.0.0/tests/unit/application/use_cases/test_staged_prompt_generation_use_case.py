"""Test for StagedPromptGenerationUseCase

Spec: SPEC-STAGED-002
Focus: P0 bug prevention - entity immutability
"""

import pytest

from noveler.domain.entities.staged_prompt import StagedPrompt


class TestStagedPromptEntityImmutability:
    """Test P0 bug prevention: ensure episode_number is read-only"""

    def test_episode_number_is_read_only(self):
        """episode_number property should be read-only (P0 regression test)

        Bug: Line 393 attempted to assign to staged_prompt.episode_number
        Fix: Remove assignment, keep property read-only
        """
        staged_prompt = StagedPrompt(episode_number=1, project_name="test_project")

        # Verify read access works
        assert staged_prompt.episode_number == 1

        # Verify write access is forbidden
        with pytest.raises(AttributeError, match="(can't set attribute|has no setter)"):
            staged_prompt.episode_number = 2

    def test_project_name_is_read_only(self):
        """project_name property should be read-only"""
        staged_prompt = StagedPrompt(episode_number=1, project_name="test_project")

        assert staged_prompt.project_name == "test_project"

        with pytest.raises(AttributeError):
            staged_prompt.project_name = "new_project"

    def test_episode_number_validated_at_construction(self):
        """episode_number validation should happen at __init__"""
        # Valid episode number
        staged_prompt = StagedPrompt(episode_number=1, project_name="test")
        assert staged_prompt.episode_number == 1

        # Invalid episode number (zero)
        with pytest.raises(ValueError, match="Episode number must be positive"):
            StagedPrompt(episode_number=0, project_name="test")

        # Invalid episode number (negative)
        with pytest.raises(ValueError, match="Episode number must be positive"):
            StagedPrompt(episode_number=-1, project_name="test")

    def test_project_name_validated_at_construction(self):
        """project_name validation should happen at __init__"""
        # Valid project name
        staged_prompt = StagedPrompt(episode_number=1, project_name="my_project")
        assert staged_prompt.project_name == "my_project"

        # Invalid project name (empty)
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            StagedPrompt(episode_number=1, project_name="")

        # Invalid project name (whitespace only)
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            StagedPrompt(episode_number=1, project_name="   ")


@pytest.mark.skip(reason="UseCase integration test - requires async setup")
class TestStagedPromptGenerationUseCase:
    """Integration tests for StagedPromptGenerationUseCase

    TODO: Implement after async test infrastructure is ready
    """

    async def test_prepare_generation_context_does_not_modify_entity(self):
        """_prepare_generation_context should not modify staged_prompt entity"""
        # TODO: Implement when async test infrastructure is ready
        pass
