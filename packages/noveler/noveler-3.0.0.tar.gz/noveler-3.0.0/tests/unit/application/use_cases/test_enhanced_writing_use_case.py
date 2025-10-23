"""Tests.tests.unit.application.use_cases.test_enhanced_writing_use_case
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from noveler.domain.errors import ApplicationError, PartialFailureError
from noveler.application.use_cases.enhanced_writing_use_case import EnhancedWritingUseCase


class DummyManager:
    def __init__(self, *a, **k):
        pass

    def get_writing_tasks(self):
        return {"episode_number": 1, "current_step": 0, "executable_tasks": []}

    def get_task_status(self):
        return {"overall_status": "not_started"}

    async def execute_writing_step_async(self, step_id: int, dry_run: bool):  # noqa: ANN001
        return {"success": True}


@pytest.mark.asyncio
async def test_async_execute_step_success():
    with patch(
        "noveler.application.use_cases.enhanced_writing_use_case.create_progressive_write_manager",
        return_value=DummyManager(),
    ), patch(
        "noveler.application.use_cases.enhanced_writing_use_case.create_progressive_write_llm_executor",
        return_value=Mock(),
    ), patch(
        "noveler.application.use_cases.enhanced_writing_use_case.get_comprehensive_error_handler",
        return_value=Mock(),
    ):
        uc = EnhancedWritingUseCase(project_root=str(Path.cwd()), episode_number=1)
        res = await uc.execute_writing_step_with_recovery_async(step_id=1, dry_run=False)
        assert res["success"] is True


@pytest.mark.asyncio
async def test_async_execute_step_partial_failure_recovered():
    mgr = DummyManager()

    async def _raise_partial(*_a, **_k):
        raise PartialFailureError("pf", failed_steps=[1], completed_steps=[], recovery_point=1)

    mgr.execute_writing_step_async = AsyncMock(side_effect=_raise_partial)

    with patch(
        "noveler.application.use_cases.enhanced_writing_use_case.create_progressive_write_manager",
        return_value=mgr,
    ), patch(
        "noveler.application.use_cases.enhanced_writing_use_case.create_progressive_write_llm_executor",
        return_value=Mock(),
    ), patch(
        "noveler.application.use_cases.enhanced_writing_use_case.get_comprehensive_error_handler",
        return_value=Mock(
            handle_error=Mock(
                return_value={
                    "recovery": {"successful": True},
                    "error": {"type": "PartialFailure"},
                    "next_steps": [],
                }
            )
        ),
    ):
        uc = EnhancedWritingUseCase(project_root=str(Path.cwd()), episode_number=1)
        res = await uc.execute_writing_step_with_recovery_async(step_id=1, dry_run=False)
        assert res["success"] is True
        assert res.get("recovery_applied") is True


@pytest.mark.asyncio
async def test_async_execute_step_system_error_structured():
    mgr = DummyManager()

    async def _raise_generic(*_a, **_k):
        raise RuntimeError("bad")

    mgr.execute_writing_step_async = AsyncMock(side_effect=_raise_generic)

    with patch(
        "noveler.application.use_cases.enhanced_writing_use_case.create_progressive_write_manager",
        return_value=mgr,
    ), patch(
        "noveler.application.use_cases.enhanced_writing_use_case.create_progressive_write_llm_executor",
        return_value=Mock(),
    ), patch(
        "noveler.application.use_cases.enhanced_writing_use_case.get_comprehensive_error_handler",
        return_value=Mock(handle_error=Mock(return_value={"error": {"type": "Unexpected", "message": "bad"}, "next_steps": []})),
    ):
        uc = EnhancedWritingUseCase(project_root=str(Path.cwd()), episode_number=1)
        res = await uc.execute_writing_step_with_recovery_async(step_id=2, dry_run=False)
        assert res["success"] is False
        assert res.get("system_error") is True
        assert res.get("support_required") is True


@pytest.mark.asyncio
async def test_async_resume_from_partial_failure_breaks_on_failure():
    # write_manager とエラーHandlerのモック
    mgr = DummyManager()
    with patch(
        "noveler.application.use_cases.enhanced_writing_use_case.create_progressive_write_manager",
        return_value=mgr,
    ), patch(
        "noveler.application.use_cases.enhanced_writing_use_case.create_progressive_write_llm_executor",
        return_value=Mock(),
    ), patch(
        "noveler.application.use_cases.enhanced_writing_use_case.get_comprehensive_error_handler",
        return_value=Mock(),
    ):
        uc = EnhancedWritingUseCase(project_root=str(Path.cwd()), episode_number=1)
        # 1回目で失敗させて早期break（結果1件）
        uc.execute_writing_step_with_recovery_async = AsyncMock(return_value={"success": False})  # type: ignore[method-assign]
        res = await uc.resume_from_partial_failure_async(recovery_point=5)
        assert res["success"] is True
        assert res["resumed_steps"] == 1


@pytest.mark.unit
def test_get_tasks_invalid_episode_number_returns_structured_error():
    with patch(
        "noveler.application.use_cases.enhanced_writing_use_case.create_progressive_write_manager",
        return_value=DummyManager(),
    ), patch(
        "noveler.application.use_cases.enhanced_writing_use_case.create_progressive_write_llm_executor",
        return_value=Mock(),
    ), patch(
        "noveler.application.use_cases.enhanced_writing_use_case.get_comprehensive_error_handler",
        return_value=Mock(handle_error=Mock(return_value={"error": {"type": "InputValidationError"}, "next_steps": []})),
    ):
        uc = EnhancedWritingUseCase(project_root=str(Path.cwd()), episode_number=0)
        result = uc.get_writing_tasks_with_error_handling()
        assert result["success"] is False
        assert "error" in result
        assert result.get("fallback_mode") is True


@pytest.mark.unit
def test_get_tasks_unexpected_exception_raises_application_error():
    bad_mgr = DummyManager()
    bad_mgr.get_writing_tasks = Mock(side_effect=RuntimeError("boom"))

    with patch(
        "noveler.application.use_cases.enhanced_writing_use_case.create_progressive_write_manager",
        return_value=bad_mgr,
    ), patch(
        "noveler.application.use_cases.enhanced_writing_use_case.create_progressive_write_llm_executor",
        return_value=Mock(),
    ), patch(
        "noveler.application.use_cases.enhanced_writing_use_case.get_comprehensive_error_handler",
        return_value=Mock(handle_error=Mock(return_value={"error": {"type": "Unexpected", "message": "boom"}, "next_steps": []})),
    ):
        uc = EnhancedWritingUseCase(project_root=str(Path.cwd()), episode_number=1)
        with pytest.raises(ApplicationError):
            _ = uc.get_writing_tasks_with_error_handling()


@pytest.mark.unit
def test_execute_step_invalid_id_user_action_required():
    with patch(
        "noveler.application.use_cases.enhanced_writing_use_case.create_progressive_write_manager",
        return_value=DummyManager(),
    ), patch(
        "noveler.application.use_cases.enhanced_writing_use_case.create_progressive_write_llm_executor",
        return_value=Mock(),
    ), patch(
        "noveler.application.use_cases.enhanced_writing_use_case.get_comprehensive_error_handler",
        return_value=Mock(handle_error=Mock(return_value={"error": {"type": "InputValidationError"}, "next_steps": []})),
    ):
        uc = EnhancedWritingUseCase(project_root=str(Path.cwd()), episode_number=1)
        res = uc.execute_writing_step_with_recovery(step_id="x", dry_run=False)  # type: ignore[arg-type]
        assert res["success"] is False
        assert res.get("user_action_required") is True


@pytest.mark.unit
def test_execute_step_partial_failure_recovered():
    mgr = DummyManager()

    async def _raise_partial(*_a, **_k):
        raise PartialFailureError("pf", failed_steps=[1], completed_steps=[], recovery_point=1)

    mgr.execute_writing_step_async = AsyncMock(side_effect=_raise_partial)

    with patch(
        "noveler.application.use_cases.enhanced_writing_use_case.create_progressive_write_manager",
        return_value=mgr,
    ), patch(
        "noveler.application.use_cases.enhanced_writing_use_case.create_progressive_write_llm_executor",
        return_value=Mock(),
    ), patch(
        "noveler.application.use_cases.enhanced_writing_use_case.get_comprehensive_error_handler",
        return_value=Mock(
            handle_error=Mock(
                return_value={
                    "recovery": {"successful": True},
                    "error": {"type": "PartialFailure"},
                    "next_steps": [],
                }
            )
        ),
    ):
        uc = EnhancedWritingUseCase(project_root=str(Path.cwd()), episode_number=1)
        res = uc.execute_writing_step_with_recovery(step_id=1, dry_run=False)
        assert res["success"] is True
        assert res.get("recovery_applied") is True


@pytest.mark.unit
def test_execute_step_system_error_returns_structured():
    mgr = DummyManager()

    async def _raise_generic(*_a, **_k):
        raise RuntimeError("bad")

    mgr.execute_writing_step_async = AsyncMock(side_effect=_raise_generic)

    with patch(
        "noveler.application.use_cases.enhanced_writing_use_case.create_progressive_write_manager",
        return_value=mgr,
    ), patch(
        "noveler.application.use_cases.enhanced_writing_use_case.create_progressive_write_llm_executor",
        return_value=Mock(),
    ), patch(
        "noveler.application.use_cases.enhanced_writing_use_case.get_comprehensive_error_handler",
        return_value=Mock(handle_error=Mock(return_value={"error": {"type": "Unexpected"}, "next_steps": []})),
    ):
        uc = EnhancedWritingUseCase(project_root=str(Path.cwd()), episode_number=1)
        res = uc.execute_writing_step_with_recovery(step_id=2, dry_run=False)
        assert res["success"] is False
        assert res.get("system_error") is True
        assert res.get("support_required") is True
