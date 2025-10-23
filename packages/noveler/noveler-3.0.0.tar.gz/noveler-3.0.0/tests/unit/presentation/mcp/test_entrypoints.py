"""tests.unit.presentation.mcp.test_entrypoints
Where: Presentation-layer entrypoint wrappers.
What: Validate delegation to handlers and error fallback behaviour.
Why: Ensures noveler.presentation.mcp.entrypoints stays a thin adapter layer.
"""

from __future__ import annotations

import pytest

from noveler.presentation.mcp import entrypoints
from noveler.presentation.mcp.adapters import handlers


@pytest.mark.asyncio
async def test_execute_fix_quality_issues_delegates_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = {"success": True, "score": 88}

    async def fake_handler(arguments: dict[str, object]) -> dict[str, object]:
        assert arguments == {"episode_number": 1}
        return expected

    monkeypatch.setattr(handlers, "fix_quality_issues", fake_handler)

    result = await entrypoints.execute_fix_quality_issues({"episode_number": 1})

    assert result is expected


@pytest.mark.asyncio
async def test_execute_fix_quality_issues_handles_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def boom(arguments: dict[str, object]) -> dict[str, object]:  # type: ignore[return-type]
        raise RuntimeError("boom")

    monkeypatch.setattr(handlers, "fix_quality_issues", boom)

    result = await entrypoints.execute_fix_quality_issues({"episode_number": 1})

    assert result == {
        "success": False,
        "error": "boom",
        "tool": "fix_quality_issues",
    }


@pytest.mark.asyncio
async def test_execute_enhanced_get_writing_tasks_delegates_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that enhanced_get_writing_tasks delegates to handler correctly."""
    expected = {"success": True, "tasks": ["task1", "task2"]}

    async def fake_handler(arguments: dict[str, object]) -> dict[str, object]:
        assert arguments == {"episode_number": 1}
        return expected

    monkeypatch.setattr(handlers, "enhanced_get_writing_tasks", fake_handler)

    result = await entrypoints.execute_enhanced_get_writing_tasks({"episode_number": 1})

    assert result is expected


@pytest.mark.asyncio
async def test_execute_enhanced_get_writing_tasks_handles_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that enhanced_get_writing_tasks handles exceptions correctly."""
    async def boom(arguments: dict[str, object]) -> dict[str, object]:  # type: ignore[return-type]
        raise RuntimeError("task error")

    monkeypatch.setattr(handlers, "enhanced_get_writing_tasks", boom)

    result = await entrypoints.execute_enhanced_get_writing_tasks({"episode_number": 1})

    assert result == {
        "success": False,
        "error": "task error",
        "tool": "enhanced_get_writing_tasks",
    }


@pytest.mark.asyncio
async def test_execute_enhanced_execute_writing_step_delegates_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that enhanced_execute_writing_step delegates to handler correctly."""
    expected = {"success": True, "step_result": "completed"}

    async def fake_handler(arguments: dict[str, object]) -> dict[str, object]:
        assert arguments == {"episode_number": 1, "step_id": 1}
        return expected

    monkeypatch.setattr(handlers, "enhanced_execute_writing_step", fake_handler)

    result = await entrypoints.execute_enhanced_execute_writing_step(
        {"episode_number": 1, "step_id": 1}
    )

    assert result is expected


@pytest.mark.asyncio
async def test_execute_enhanced_execute_writing_step_handles_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that enhanced_execute_writing_step handles exceptions correctly."""
    async def boom(arguments: dict[str, object]) -> dict[str, object]:  # type: ignore[return-type]
        raise RuntimeError("step error")

    monkeypatch.setattr(handlers, "enhanced_execute_writing_step", boom)

    result = await entrypoints.execute_enhanced_execute_writing_step(
        {"episode_number": 1, "step_id": 1}
    )

    assert result == {
        "success": False,
        "error": "step error",
        "tool": "enhanced_execute_writing_step",
    }


@pytest.mark.asyncio
async def test_execute_enhanced_resume_from_partial_failure_delegates_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that enhanced_resume_from_partial_failure delegates to handler correctly."""
    expected = {"success": True, "resumed": True}

    async def fake_handler(arguments: dict[str, object]) -> dict[str, object]:
        assert arguments == {"episode_number": 1, "recovery_point": 5}
        return expected

    monkeypatch.setattr(handlers, "enhanced_resume_from_partial_failure", fake_handler)

    result = await entrypoints.execute_enhanced_resume_from_partial_failure(
        {"episode_number": 1, "recovery_point": 5}
    )

    assert result is expected


@pytest.mark.asyncio
async def test_execute_enhanced_resume_from_partial_failure_handles_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that enhanced_resume_from_partial_failure handles exceptions correctly."""
    async def boom(arguments: dict[str, object]) -> dict[str, object]:  # type: ignore[return-type]
        raise RuntimeError("resume error")

    monkeypatch.setattr(handlers, "enhanced_resume_from_partial_failure", boom)

    result = await entrypoints.execute_enhanced_resume_from_partial_failure(
        {"episode_number": 1, "recovery_point": 5}
    )

    assert result == {
        "success": False,
        "error": "resume error",
        "tool": "enhanced_resume_from_partial_failure",
    }


@pytest.mark.asyncio
async def test_execute_get_check_tasks_delegates_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that get_check_tasks delegates to handler correctly."""
    expected = {"success": True, "tasks": ["check1", "check2"]}

    async def fake_handler(arguments: dict[str, object]) -> dict[str, object]:
        assert arguments == {"episode_number": 1}
        return expected

    monkeypatch.setattr(handlers, "get_check_tasks", fake_handler)

    result = await entrypoints.execute_get_check_tasks({"episode_number": 1})

    assert result is expected


@pytest.mark.asyncio
async def test_execute_get_check_tasks_handles_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that get_check_tasks handles exceptions correctly."""
    async def boom(arguments: dict[str, object]) -> dict[str, object]:  # type: ignore[return-type]
        raise RuntimeError("check tasks error")

    monkeypatch.setattr(handlers, "get_check_tasks", boom)

    result = await entrypoints.execute_get_check_tasks({"episode_number": 1})

    assert result == {
        "success": False,
        "error": "check tasks error",
        "tool": "get_check_tasks",
    }


@pytest.mark.asyncio
async def test_execute_check_step_command_delegates_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that execute_check_step delegates to handler correctly."""
    expected = {"success": True, "check_result": "passed"}

    async def fake_handler(arguments: dict[str, object]) -> dict[str, object]:
        assert arguments == {"episode_number": 1, "check_id": "grammar"}
        return expected

    monkeypatch.setattr(handlers, "execute_check_step", fake_handler)

    result = await entrypoints.execute_check_step_command(
        {"episode_number": 1, "check_id": "grammar"}
    )

    assert result is expected


@pytest.mark.asyncio
async def test_execute_check_step_command_handles_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that execute_check_step handles exceptions correctly."""
    async def boom(arguments: dict[str, object]) -> dict[str, object]:  # type: ignore[return-type]
        raise RuntimeError("check step error")

    monkeypatch.setattr(handlers, "execute_check_step", boom)

    result = await entrypoints.execute_check_step_command(
        {"episode_number": 1, "check_id": "grammar"}
    )

    assert result == {
        "success": False,
        "error": "check step error",
        "tool": "execute_check_step",
    }


@pytest.mark.asyncio
async def test_execute_get_check_status_delegates_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that get_check_status delegates to handler correctly."""
    expected = {"success": True, "status": "completed"}

    async def fake_handler(arguments: dict[str, object]) -> dict[str, object]:
        assert arguments == {"episode_number": 1}
        return expected

    monkeypatch.setattr(handlers, "get_check_status", fake_handler)

    result = await entrypoints.execute_get_check_status({"episode_number": 1})

    assert result is expected


@pytest.mark.asyncio
async def test_execute_get_check_status_handles_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that get_check_status handles exceptions correctly."""
    async def boom(arguments: dict[str, object]) -> dict[str, object]:  # type: ignore[return-type]
        raise RuntimeError("status error")

    monkeypatch.setattr(handlers, "get_check_status", boom)

    result = await entrypoints.execute_get_check_status({"episode_number": 1})

    assert result == {
        "success": False,
        "error": "status error",
        "tool": "get_check_status",
    }


@pytest.mark.asyncio
async def test_execute_get_check_history_delegates_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that get_check_history delegates to handler correctly."""
    expected = {"success": True, "history": [{"check_id": "grammar", "result": "passed"}]}

    async def fake_handler(arguments: dict[str, object]) -> dict[str, object]:
        assert arguments == {"episode_number": 1}
        return expected

    monkeypatch.setattr(handlers, "get_check_history", fake_handler)

    result = await entrypoints.execute_get_check_history({"episode_number": 1})

    assert result is expected


@pytest.mark.asyncio
async def test_execute_get_check_history_handles_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that get_check_history handles exceptions correctly."""
    async def boom(arguments: dict[str, object]) -> dict[str, object]:  # type: ignore[return-type]
        raise RuntimeError("history error")

    monkeypatch.setattr(handlers, "get_check_history", boom)

    result = await entrypoints.execute_get_check_history({"episode_number": 1})

    assert result == {
        "success": False,
        "error": "history error",
        "tool": "get_check_history",
    }


@pytest.mark.asyncio
async def test_execute_generate_episode_preview_delegates_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that generate_episode_preview delegates to handler correctly."""
    expected = {"success": True, "preview": "Episode preview content"}

    async def fake_handler(arguments: dict[str, object]) -> dict[str, object]:
        assert arguments == {"episode_number": 1}
        return expected

    monkeypatch.setattr(handlers, "generate_episode_preview", fake_handler)

    result = await entrypoints.execute_generate_episode_preview({"episode_number": 1})

    assert result is expected


@pytest.mark.asyncio
async def test_execute_generate_episode_preview_handles_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that generate_episode_preview handles exceptions correctly."""
    async def boom(arguments: dict[str, object]) -> dict[str, object]:  # type: ignore[return-type]
        raise RuntimeError("preview error")

    monkeypatch.setattr(handlers, "generate_episode_preview", boom)

    result = await entrypoints.execute_generate_episode_preview({"episode_number": 1})

    assert result == {
        "success": False,
        "error": "preview error",
        "tool": "generate_episode_preview",
    }

