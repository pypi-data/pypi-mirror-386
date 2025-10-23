# File: tests/unit/domain/services/orchestration/test_step_orchestrator.py
# Purpose: Unit tests for StepOrchestrator domain service
# Context: Tests business logic for step progression and prerequisites

import pytest
from noveler.domain.services.orchestration import StepOrchestrator


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_tasks_config():
    """Sample tasks configuration for testing."""
    return {
        "metadata": {"version": "1.0.0", "total_steps": 5},
        "phases": ["basic", "advanced"],
        "tasks": [
            {"id": 1, "name": "Task A", "phase": "basic", "prerequisites": []},
            {"id": 2, "name": "Task B", "phase": "basic", "prerequisites": [1]},
            {"id": 3, "name": "Task C", "phase": "basic", "prerequisites": [1]},
            {"id": 4, "name": "Task D", "phase": "advanced", "prerequisites": [2, 3]},
            {"id": 5, "name": "Task E", "phase": "advanced", "prerequisites": [4]},
        ],
    }


@pytest.fixture
def orchestrator(sample_tasks_config):
    """StepOrchestrator instance with sample config."""
    return StepOrchestrator(sample_tasks_config)


# ============================================================================
# Unit Tests - check_prerequisites
# ============================================================================


class TestCheckPrerequisites:
    """Tests for check_prerequisites static method."""

    def test_no_prerequisites(self):
        """check_prerequisites() should return True for empty prerequisites."""
        assert StepOrchestrator.check_prerequisites([], []) is True
        assert StepOrchestrator.check_prerequisites([], [1, 2, 3]) is True

    def test_all_prerequisites_satisfied(self):
        """check_prerequisites() should return True if all prerequisites completed."""
        assert StepOrchestrator.check_prerequisites([1, 2], [1, 2, 3]) is True
        assert StepOrchestrator.check_prerequisites([1], [1, 2]) is True

    def test_some_prerequisites_missing(self):
        """check_prerequisites() should return False if any prerequisite missing."""
        assert StepOrchestrator.check_prerequisites([1, 2], [1]) is False
        assert StepOrchestrator.check_prerequisites([1, 2, 3], [1, 2]) is False

    def test_no_prerequisites_completed(self):
        """check_prerequisites() should return False if no prerequisites completed."""
        assert StepOrchestrator.check_prerequisites([1, 2], []) is False

    def test_exact_match(self):
        """check_prerequisites() should return True for exact match."""
        assert StepOrchestrator.check_prerequisites([1, 2], [1, 2]) is True


# ============================================================================
# Unit Tests - find_next_step
# ============================================================================


class TestFindNextStep:
    """Tests for find_next_step method."""

    def test_first_step_no_prerequisites(self, orchestrator):
        """find_next_step() should return first task when nothing completed."""
        result = orchestrator.find_next_step([])
        assert result == 1

    def test_second_step_after_first_completed(self, orchestrator):
        """find_next_step() should return task 2 or 3 after task 1 completed."""
        result = orchestrator.find_next_step([1])
        # Both tasks 2 and 3 have prerequisite [1], returns first found (task 2)
        assert result == 2

    def test_skip_completed_tasks(self, orchestrator):
        """find_next_step() should skip already completed tasks."""
        result = orchestrator.find_next_step([1, 2])
        # Task 2 completed, next is task 3 (prerequisite [1] satisfied)
        assert result == 3

    def test_wait_for_multiple_prerequisites(self, orchestrator):
        """find_next_step() should wait for all prerequisites."""
        result = orchestrator.find_next_step([1, 2])
        # Task 4 requires [2, 3], only 2 completed, so returns task 3
        assert result == 3

    def test_advanced_step_after_all_basics(self, orchestrator):
        """find_next_step() should return advanced task after basics completed."""
        result = orchestrator.find_next_step([1, 2, 3])
        # Task 4 requires [2, 3], both completed
        assert result == 4

    def test_final_step(self, orchestrator):
        """find_next_step() should return final task."""
        result = orchestrator.find_next_step([1, 2, 3, 4])
        # Task 5 requires [4]
        assert result == 5

    def test_all_steps_completed(self, orchestrator):
        """find_next_step() should return None when all tasks completed."""
        result = orchestrator.find_next_step([1, 2, 3, 4, 5])
        assert result is None

    def test_empty_tasks_config(self):
        """find_next_step() should return None for empty tasks config."""
        empty_orchestrator = StepOrchestrator({"metadata": {}, "tasks": []})
        result = empty_orchestrator.find_next_step([])
        assert result is None


# ============================================================================
# Unit Tests - get_executable_tasks
# ============================================================================


class TestGetExecutableTasks:
    """Tests for get_executable_tasks method."""

    def test_nothing_completed(self, orchestrator):
        """get_executable_tasks() should return only first task with no prerequisites."""
        result = orchestrator.get_executable_tasks([])
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_multiple_parallel_tasks(self, orchestrator):
        """get_executable_tasks() should return multiple tasks with satisfied prerequisites."""
        result = orchestrator.get_executable_tasks([1])
        # Both tasks 2 and 3 have prerequisite [1]
        assert len(result) == 2
        assert {task["id"] for task in result} == {2, 3}

    def test_skip_completed_tasks(self, orchestrator):
        """get_executable_tasks() should skip completed tasks."""
        result = orchestrator.get_executable_tasks([1, 2])
        # Task 2 completed, only task 3 remains with prerequisite [1]
        assert len(result) == 1
        assert result[0]["id"] == 3

    def test_wait_for_all_prerequisites(self, orchestrator):
        """get_executable_tasks() should not return tasks with unsatisfied prerequisites."""
        result = orchestrator.get_executable_tasks([1, 2])
        # Task 4 requires [2, 3], only 2 completed
        # Only task 3 is executable
        assert len(result) == 1
        assert result[0]["id"] == 3

    def test_all_completed(self, orchestrator):
        """get_executable_tasks() should return empty list when all completed."""
        result = orchestrator.get_executable_tasks([1, 2, 3, 4, 5])
        assert result == []

    def test_empty_tasks_config(self):
        """get_executable_tasks() should return empty list for empty config."""
        empty_orchestrator = StepOrchestrator({"metadata": {}, "tasks": []})
        result = empty_orchestrator.get_executable_tasks([])
        assert result == []


# ============================================================================
# Unit Tests - get_task_by_id
# ============================================================================


class TestGetTaskById:
    """Tests for get_task_by_id method."""

    def test_find_existing_task(self, orchestrator):
        """get_task_by_id() should return task dict for existing ID."""
        result = orchestrator.get_task_by_id(1)
        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "Task A"

    def test_find_middle_task(self, orchestrator):
        """get_task_by_id() should find task in middle of list."""
        result = orchestrator.get_task_by_id(3)
        assert result is not None
        assert result["id"] == 3
        assert result["name"] == "Task C"

    def test_nonexistent_task(self, orchestrator):
        """get_task_by_id() should return None for nonexistent ID."""
        result = orchestrator.get_task_by_id(999)
        assert result is None

    def test_empty_tasks_config(self):
        """get_task_by_id() should return None for empty config."""
        empty_orchestrator = StepOrchestrator({"metadata": {}, "tasks": []})
        result = empty_orchestrator.get_task_by_id(1)
        assert result is None


# ============================================================================
# Integration Tests
# ============================================================================


class TestStepOrchestratorIntegration:
    """Integration-style tests for complete workflows."""

    def test_sequential_workflow(self, orchestrator):
        """Test sequential completion workflow."""
        completed = []

        # Step 1: Start with nothing completed
        next_step = orchestrator.find_next_step(completed)
        assert next_step == 1

        # Complete task 1
        completed.append(1)

        # Step 2: Should find task 2 or 3 (both available, returns first)
        next_step = orchestrator.find_next_step(completed)
        assert next_step == 2

        # Complete task 2
        completed.append(2)

        # Step 3: Should find task 3
        next_step = orchestrator.find_next_step(completed)
        assert next_step == 3

        # Complete task 3
        completed.append(3)

        # Step 4: Should find task 4 (both prerequisites [2, 3] satisfied)
        next_step = orchestrator.find_next_step(completed)
        assert next_step == 4

        # Complete task 4
        completed.append(4)

        # Step 5: Should find task 5
        next_step = orchestrator.find_next_step(completed)
        assert next_step == 5

        # Complete task 5
        completed.append(5)

        # Final: No more tasks
        next_step = orchestrator.find_next_step(completed)
        assert next_step is None

    def test_parallel_execution_tracking(self, orchestrator):
        """Test tracking multiple executable tasks."""
        # After task 1, both 2 and 3 are executable
        executable = orchestrator.get_executable_tasks([1])
        assert len(executable) == 2
        assert {task["id"] for task in executable} == {2, 3}

        # Can choose to execute either task 2 or 3 first
        # Let's say we complete task 3 first
        executable = orchestrator.get_executable_tasks([1, 3])
        assert len(executable) == 1
        assert executable[0]["id"] == 2

        # Complete task 2
        executable = orchestrator.get_executable_tasks([1, 2, 3])
        assert len(executable) == 1
        assert executable[0]["id"] == 4  # Both prerequisites satisfied

    def test_complex_prerequisite_chain(self):
        """Test complex prerequisite dependencies."""
        complex_config = {
            "tasks": [
                {"id": 1, "prerequisites": []},
                {"id": 2, "prerequisites": []},
                {"id": 3, "prerequisites": [1, 2]},
                {"id": 4, "prerequisites": [3]},
                {"id": 5, "prerequisites": [1]},
            ]
        }
        orchestrator = StepOrchestrator(complex_config)

        # Nothing completed: tasks 1 and 2 available
        executable = orchestrator.get_executable_tasks([])
        assert {task["id"] for task in executable} == {1, 2}

        # Only task 1 completed: tasks 2 and 5 available
        executable = orchestrator.get_executable_tasks([1])
        assert {task["id"] for task in executable} == {2, 5}

        # Tasks 1 and 2 completed: tasks 3 and 5 available
        executable = orchestrator.get_executable_tasks([1, 2])
        assert {task["id"] for task in executable} == {3, 5}

        # Tasks 1, 2, 3 completed: tasks 4 and 5 available
        executable = orchestrator.get_executable_tasks([1, 2, 3])
        assert {task["id"] for task in executable} == {4, 5}
