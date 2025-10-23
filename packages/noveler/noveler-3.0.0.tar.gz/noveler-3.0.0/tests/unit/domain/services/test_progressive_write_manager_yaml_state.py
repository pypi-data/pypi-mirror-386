# File: tests/unit/domain/services/test_progressive_write_manager_yaml_state.py
# Purpose: Test YAML state file loading and save instructions generation for 18-step writing system
# Context: Verifies _try_load_yaml_state() and _generate_save_instructions() methods in ProgressiveWriteManager

from pathlib import Path

import pytest

from noveler.domain.services.progressive_write_manager import ProgressiveWriteManager


@pytest.fixture
def write_manager_stub(tmp_path):
    """Create a minimal ProgressiveWriteManager for testing.

    Purpose: Provide isolated test environment with necessary attributes.

    Args:
        tmp_path: pytest fixture providing temporary directory

    Returns:
        ProgressiveWriteManager instance with minimal state for testing
    """
    manager = ProgressiveWriteManager.__new__(ProgressiveWriteManager)
    manager.project_root = tmp_path
    manager.episode_number = 1
    manager.logger = None  # Suppress logging in tests
    manager.current_state = {
        "episode_number": 1,
        "completed_steps": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        "episode_info": {
            "created_at": "2025-10-13T00:00:00",
            "status": "in_progress"
        }
    }
    return manager


@pytest.fixture
def yaml_state_file(tmp_path):
    """Create a sample YAML state file at the expected location.

    Purpose: Provide test fixture for YAML state file loading tests.

    Args:
        tmp_path: pytest fixture providing temporary directory

    Returns:
        Path to created YAML state file

    Side Effects:
        Creates directory structure and YAML file in tmp_path
    """
    state_dir = tmp_path / "50_管理資料" / "執筆記録"
    state_dir.mkdir(parents=True, exist_ok=True)

    yaml_content = """episode_info:
  episode_number: 1
  status: in_progress
  created_at: "2025-10-13T00:00:00"
  updated_at: "2025-10-13T01:00:00"

workflow_progress:
  current_step: 11
  completed_steps: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
  next_step: 12
  failed_steps: []

step_results:
  # Step execution results
"""

    state_file = state_dir / "episode_001_state.yaml"
    state_file.write_text(yaml_content, encoding="utf-8")

    return state_file


class TestTryLoadYamlState:
    """Test suite for _try_load_yaml_state() method.

    Purpose: Verify YAML state file loading from 50_管理資料/執筆記録/ directory.
    Context: This method provides priority loading over legacy JSON format.
    """

    def test_loads_yaml_state_successfully(self, write_manager_stub, yaml_state_file):
        """Verify successful YAML state file loading and conversion to internal format."""
        manager = write_manager_stub

        state = manager._try_load_yaml_state()

        assert state is not None
        assert state["episode_number"] == 1
        assert state["current_step"] == 11
        assert state["completed_steps"] == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        assert state["overall_status"] == "in_progress"
        assert state["source"] == "yaml_18_step"

    def test_returns_none_when_file_not_found(self, write_manager_stub):
        """Verify graceful handling when YAML file doesn't exist."""
        manager = write_manager_stub

        state = manager._try_load_yaml_state()

        assert state is None

    def test_returns_none_when_yaml_parsing_fails(self, write_manager_stub, tmp_path):
        """Verify graceful handling of invalid YAML syntax."""
        manager = write_manager_stub

        # Create invalid YAML file to test error handling
        state_dir = tmp_path / "50_管理資料" / "執筆記録"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "episode_001_state.yaml"
        state_file.write_text("invalid: yaml: content: [", encoding="utf-8")

        state = manager._try_load_yaml_state()

        assert state is None

    def test_converts_yaml_structure_correctly(self, write_manager_stub, tmp_path):
        """Verify correct conversion from YAML structure to internal state format."""
        manager = write_manager_stub

        # Create YAML with specific structure for conversion testing
        state_dir = tmp_path / "50_管理資料" / "執筆記録"
        state_dir.mkdir(parents=True, exist_ok=True)

        yaml_content = """episode_info:
  episode_number: 1
  status: draft_completed
  created_at: "2025-10-13T00:00:00"
  updated_at: "2025-10-13T02:00:00"

workflow_progress:
  current_step: 12
  completed_steps: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  next_step: 13
  failed_steps: []
"""

        state_file = state_dir / "episode_001_state.yaml"
        state_file.write_text(yaml_content, encoding="utf-8")

        state = manager._try_load_yaml_state()

        assert state["current_step"] == 12
        assert state["completed_steps"] == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        assert state["overall_status"] == "draft_completed"
        assert state["last_updated"] == "2025-10-13T02:00:00"


class TestGenerateSaveInstructions:
    """Test suite for _generate_save_instructions() method.

    Purpose: Verify prompt instructions generation for LLM to save manuscript and state.
    Context: Instructions are embedded in prompt, LLM executes mcp__noveler__write tool.
    """

    def test_generates_instructions_with_manuscript_path(self, write_manager_stub):
        """Verify instruction contains correct manuscript file path."""
        manager = write_manager_stub

        instructions = manager._generate_save_instructions(step_id=12, step_name="初稿執筆")

        assert "40_原稿/第001話.md" in instructions
        assert "mcp__noveler__write" in instructions

    def test_generates_instructions_with_state_path(self, write_manager_stub):
        """Verify instruction contains correct state file path."""
        manager = write_manager_stub

        instructions = manager._generate_save_instructions(step_id=12, step_name="初稿執筆")

        assert "50_管理資料/執筆記録/episode_001_state.yaml" in instructions

    def test_generates_updated_yaml_content(self, write_manager_stub):
        """Verify instruction contains pre-generated updated YAML content."""
        manager = write_manager_stub

        instructions = manager._generate_save_instructions(step_id=12, step_name="初稿執筆")

        # Verify YAML content includes completed step 12
        assert "completed_steps: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]" in instructions
        assert "current_step: 12" in instructions
        assert "next_step: 13" in instructions

    def test_contains_copy_paste_instruction(self, write_manager_stub):
        """Verify instruction emphasizes copy-paste to prevent manual editing errors."""
        manager = write_manager_stub

        instructions = manager._generate_save_instructions(step_id=12, step_name="初稿執筆")

        assert "そのままコピー" in instructions
        assert "編集は不要" in instructions


class TestGenerateUpdatedYaml:
    """Test suite for _generate_updated_yaml() method.

    Purpose: Verify programmatic YAML generation for state updates.
    Context: Pre-generates YAML to eliminate LLM manual editing errors (DEC-018).
    """

    def test_generates_valid_yaml_structure(self, write_manager_stub):
        """Verify generated YAML has valid structure with required sections."""
        manager = write_manager_stub
        new_completed = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

        yaml_content = manager._generate_updated_yaml(step_id=12, new_completed=new_completed)

        assert "episode_info:" in yaml_content
        assert "workflow_progress:" in yaml_content
        assert "step_results:" in yaml_content

    def test_updates_completed_steps_correctly(self, write_manager_stub):
        """Verify completed_steps list is updated with new step_id."""
        manager = write_manager_stub
        new_completed = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

        yaml_content = manager._generate_updated_yaml(step_id=12, new_completed=new_completed)

        assert "completed_steps: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]" in yaml_content

    def test_updates_current_step(self, write_manager_stub):
        """Verify current_step is set to completed step_id."""
        manager = write_manager_stub
        new_completed = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

        yaml_content = manager._generate_updated_yaml(step_id=12, new_completed=new_completed)

        assert "current_step: 12" in yaml_content

    def test_calculates_next_step_correctly(self, write_manager_stub):
        """Verify next_step is calculated as step_id + 1."""
        manager = write_manager_stub
        new_completed = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

        yaml_content = manager._generate_updated_yaml(step_id=12, new_completed=new_completed)

        assert "next_step: 13" in yaml_content

    def test_sets_next_step_null_for_final_step(self, write_manager_stub):
        """Verify next_step is null when step_id is 17 (final step in 18-step system)."""
        manager = write_manager_stub
        new_completed = list(range(18))

        yaml_content = manager._generate_updated_yaml(step_id=17, new_completed=new_completed)

        assert "next_step: null" in yaml_content

    def test_updates_status_to_draft_completed_for_step_12(self, write_manager_stub):
        """Verify status changes to 'draft_completed' when completing STEP 12 (初稿執筆)."""
        manager = write_manager_stub
        new_completed = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

        yaml_content = manager._generate_updated_yaml(step_id=12, new_completed=new_completed)

        assert "status: draft_completed" in yaml_content

    def test_preserves_status_for_other_steps(self, write_manager_stub):
        """Verify status is preserved for steps other than 12."""
        manager = write_manager_stub
        manager.current_state["episode_info"]["status"] = "in_progress"
        new_completed = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

        yaml_content = manager._generate_updated_yaml(step_id=11, new_completed=new_completed)

        assert "status: in_progress" in yaml_content

    def test_includes_episode_number(self, write_manager_stub):
        """Verify episode_number is included in YAML."""
        manager = write_manager_stub
        new_completed = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

        yaml_content = manager._generate_updated_yaml(step_id=12, new_completed=new_completed)

        assert "episode_number: 1" in yaml_content

    def test_preserves_created_at_from_current_state(self, write_manager_stub):
        """Verify created_at timestamp is preserved from current_state."""
        manager = write_manager_stub
        manager.current_state["episode_info"]["created_at"] = "2025-10-13T00:00:00"
        new_completed = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

        yaml_content = manager._generate_updated_yaml(step_id=12, new_completed=new_completed)

        assert 'created_at: "2025-10-13T00:00:00"' in yaml_content
