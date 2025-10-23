# File: src/noveler/domain/services/orchestration/step_orchestrator.py
# Purpose: Step progression logic and prerequisite checking
# Context: Extracted from ProgressiveCheckManager step orchestration methods

from typing import Any


class StepOrchestrator:
    """Step progression control (Domain layer - no I/O).

    Responsibilities:
        - Check task prerequisites
        - Find next executable step
        - Get all executable tasks from task list

    Note: This is a stateless service that operates on task configurations
    and completed step lists provided as parameters.

    Extracted from:
        - ProgressiveCheckManager._check_prerequisites (lines 1458-1463)
        - ProgressiveCheckManager._find_next_step (lines 2160-2169)
        - ProgressiveCheckManager._get_executable_tasks (lines 1410-1418)
    """

    def __init__(self, tasks_config: dict[str, Any]) -> None:
        """Initialize orchestrator with tasks configuration.

        Args:
            tasks_config: check_tasks.yaml structure
                Expected structure:
                {
                    "metadata": {"version": "1.0.0", "total_steps": 12},
                    "phases": [...],
                    "tasks": [
                        {
                            "id": 1,
                            "name": "誤字脱字チェック",
                            "phase": "basic_quality",
                            "prerequisites": []
                        },
                        ...
                    ]
                }
        """
        self._tasks_config = tasks_config

    @property
    def tasks(self) -> list[dict[str, Any]]:
        """Get tasks list from configuration."""
        return self._tasks_config.get("tasks", [])

    @staticmethod
    def check_prerequisites(prerequisites: list[int], completed_steps: list[int]) -> bool:
        """Check if all prerequisites are completed.

        Args:
            prerequisites: List of prerequisite step IDs (e.g., [1, 2])
            completed_steps: List of completed step IDs (e.g., [1, 2, 3])

        Returns:
            True if all prerequisites are in completed_steps, False otherwise

        Side Effects:
            None (pure function)

        Examples:
            >>> StepOrchestrator.check_prerequisites([1, 2], [1, 2, 3])
            True
            >>> StepOrchestrator.check_prerequisites([1, 2], [1])
            False
            >>> StepOrchestrator.check_prerequisites([], [])
            True  # No prerequisites = always satisfied
        """
        return all(prereq in completed_steps for prereq in prerequisites)

    def find_next_step(self, completed_steps: list[int]) -> int | None:
        """Find the next executable step ID.

        Strategy: Return first task (in order) that is:
        - Not yet completed
        - Has all prerequisites satisfied

        Args:
            completed_steps: List of completed step IDs

        Returns:
            Next step ID (int) or None if no executable steps remain

        Side Effects:
            None (pure function)

        Examples:
            Given tasks: [
                {"id": 1, "prerequisites": []},
                {"id": 2, "prerequisites": [1]},
                {"id": 3, "prerequisites": [1, 2]},
            ]

            >>> orchestrator.find_next_step([])
            1  # First task with no prerequisites

            >>> orchestrator.find_next_step([1])
            2  # Second task (prerequisite 1 satisfied)

            >>> orchestrator.find_next_step([1, 2, 3])
            None  # All tasks completed
        """
        for task in self.tasks:
            task_id = task["id"]
            prerequisites = task.get("prerequisites", [])

            # Skip completed tasks
            if task_id in completed_steps:
                continue

            # Check if prerequisites are satisfied
            if self.check_prerequisites(prerequisites, completed_steps):
                return int(task_id)

        return None

    def get_executable_tasks(self, completed_steps: list[int]) -> list[dict[str, Any]]:
        """Get all currently executable tasks.

        Returns all tasks that:
        - Are not yet completed
        - Have all prerequisites satisfied

        Args:
            completed_steps: List of completed step IDs

        Returns:
            List of executable task dicts (may be empty)

        Side Effects:
            None (pure function)

        Examples:
            Given tasks: [
                {"id": 1, "name": "Task A", "prerequisites": []},
                {"id": 2, "name": "Task B", "prerequisites": []},
                {"id": 3, "name": "Task C", "prerequisites": [1, 2]},
            ]

            >>> orchestrator.get_executable_tasks([])
            [{"id": 1, ...}, {"id": 2, ...}]  # Tasks A and B (no prerequisites)

            >>> orchestrator.get_executable_tasks([1])
            [{"id": 2, ...}]  # Only Task B (Task C still needs Task 2)

            >>> orchestrator.get_executable_tasks([1, 2])
            [{"id": 3, ...}]  # Task C (both prerequisites satisfied)
        """
        executable = []
        for task in self.tasks:
            task_id = task["id"]
            prerequisites = task.get("prerequisites", [])

            # Skip completed tasks
            if task_id in completed_steps:
                continue

            # Check if prerequisites are satisfied
            if self.check_prerequisites(prerequisites, completed_steps):
                executable.append(task)

        return executable

    def get_task_by_id(self, task_id: int) -> dict[str, Any] | None:
        """Get task dict by ID.

        Args:
            task_id: Task ID to find

        Returns:
            Task dict or None if not found

        Side Effects:
            None (pure function)

        Examples:
            >>> orchestrator.get_task_by_id(1)
            {"id": 1, "name": "誤字脱字チェック", ...}

            >>> orchestrator.get_task_by_id(999)
            None  # Not found
        """
        for task in self.tasks:
            if task["id"] == task_id:
                return task
        return None
