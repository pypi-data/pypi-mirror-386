"""B20対応版 A31 完全チェックユースケースのユニットテスト。"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from noveler.application.use_cases.a31_complete_check_use_case import A31CompleteCheckUseCase
from noveler.domain.entities.a31_checklist_item import A31ChecklistItem, ChecklistItemType
from noveler.domain.entities.a31_complete_evaluation_engine import (
    A31CompleteCheckRequest,
    A31CompleteCheckResponse,
    A31EvaluationBatch,
    A31EvaluationCategory,
    A31EvaluationResult,
)
from noveler.domain.value_objects.a31_auto_fix_strategy import AutoFixStrategy
from noveler.domain.value_objects.a31_threshold import Threshold, ThresholdType


@pytest.fixture
def logger_service() -> Mock:
    logger = Mock()
    logger.info.return_value = None
    logger.debug.return_value = None
    logger.error.return_value = None
    logger.warning.return_value = None
    return logger


@pytest.fixture
def unit_of_work() -> Mock:
    uow = Mock()
    uow.__enter__ = Mock(return_value=uow)
    uow.__exit__ = Mock(return_value=False)
    return uow


@pytest.fixture
def console_service() -> Mock:
    console = Mock()
    console.print.return_value = None
    return console


@pytest.fixture
def path_service() -> Mock:
    service = Mock()
    service.get_checklist_file_path.return_value = Path("generated_checklist.yaml")
    service.get_episode_file_path.return_value = Path("episode.md")
    service.get_manuscript_dir.return_value = Path("manuscripts")
    service.get_manuscript_path.return_value = Path("manuscripts/episode.md")
    return service


@pytest.fixture
def episode_repository() -> Mock:
    repo = Mock()
    repo.get_episode_content.return_value = "テストエピソード本文"
    repo.get_all_episodes.return_value = [1, 2, 3]
    repo.update_episode_content.return_value = None
    return repo


@pytest.fixture
def project_repository() -> Mock:
    repo = Mock()
    repo.get_project_config.return_value = {
        "quality_threshold": 70.0,
        "characters": {"主人公": {"口調": "丁寧語"}},
        "terminology": {"魔法": "マジック"},
    }
    repo.get_project_root.return_value = Path("project-root")
    repo.project_root = Path("project-root")
    return repo


@pytest.fixture
def a31_checklist_repository(sample_checklist_items: list[A31ChecklistItem]) -> Mock:
    repo = Mock()
    repo.get_all_checklist_items.return_value = sample_checklist_items
    repo.save_evaluation_results.return_value = None
    repo.create_episode_checklist.return_value = Path("generated_checklist.yaml")
    return repo


@pytest.fixture
def sample_checklist_items() -> list[A31ChecklistItem]:
    return [
        A31ChecklistItem(
            item_id="A31-045",
            title="段落頭の字下げを確認",
            required=True,
            item_type=ChecklistItemType.FORMAT_CHECK,
            threshold=Threshold(ThresholdType.PERCENTAGE, 95.0),
            auto_fix_strategy=AutoFixStrategy.create_safe_strategy(1),
        ),
        A31ChecklistItem(
            item_id="A31-022",
            title="会話と地の文のバランスを確認",
            required=True,
            item_type=ChecklistItemType.CONTENT_BALANCE,
            threshold=Threshold.create_range(30.0, 40.0),
            auto_fix_strategy=AutoFixStrategy.create_manual_strategy(),
        ),
    ]


@pytest.fixture
def sample_evaluation_batch() -> A31EvaluationBatch:
    results = {
        "A31-045": A31EvaluationResult(
            item_id="A31-045",
            category=A31EvaluationCategory.FORMAT_CHECK,
            score=100.0,
            passed=True,
            details="段落字下げ適正",
            execution_time_ms=50.0,
        ),
        "A31-022": A31EvaluationResult(
            item_id="A31-022",
            category=A31EvaluationCategory.CONTENT_BALANCE,
            score=25.0,
            passed=False,
            details="会話比率不足",
            execution_time_ms=30.0,
        ),
    }
    return A31EvaluationBatch(results=results, total_items=2, evaluated_items=2, execution_time_ms=80.0)


@pytest.fixture
def evaluation_engine(sample_evaluation_batch: A31EvaluationBatch) -> Mock:
    engine = Mock()
    engine.evaluate_all_items.return_value = sample_evaluation_batch

    def to_category(item_type: ChecklistItemType) -> A31EvaluationCategory:
        mapping = {
            ChecklistItemType.FORMAT_CHECK: A31EvaluationCategory.FORMAT_CHECK,
            ChecklistItemType.CONTENT_BALANCE: A31EvaluationCategory.CONTENT_BALANCE,
        }
        return mapping.get(item_type, A31EvaluationCategory.FORMAT_CHECK)

    engine._get_category_from_item_type = Mock(side_effect=to_category)
    return engine


@pytest.fixture
def use_case_setup(
    logger_service: Mock,
    unit_of_work: Mock,
    console_service: Mock,
    path_service: Mock,
    episode_repository: Mock,
    project_repository: Mock,
    a31_checklist_repository: Mock,
    evaluation_engine: Mock,
) -> SimpleNamespace:
    use_case = A31CompleteCheckUseCase(
        logger_service=logger_service,
        unit_of_work=unit_of_work,
        console_service=console_service,
        path_service=path_service,
    )

    use_case._episode_repository = episode_repository
    use_case._project_repository = project_repository
    use_case._a31_checklist_repository = a31_checklist_repository
    use_case._evaluation_engine = evaluation_engine
    use_case._claude_analyzer = None
    use_case._result_integrator = None

    use_case._get_episode_title = Mock(return_value="テストエピソード")
    use_case._get_project_root_path = Mock(return_value=Path("project-root"))
    use_case._find_actual_episode_file = Mock(return_value=None)
    use_case.get_path_service = Mock(return_value=path_service)

    use_case._execute_claude_analysis_integration = AsyncMock(return_value=None)
    use_case._merge_claude_results_with_local = Mock(side_effect=lambda local, _: local)
    use_case._update_episode_content = Mock()
    use_case._apply_integrated_auto_fixes = Mock(return_value=(0, "テストエピソード本文"))

    return SimpleNamespace(
        use_case=use_case,
        episode_repository=episode_repository,
        project_repository=project_repository,
        checklist_repository=a31_checklist_repository,
        evaluation_engine=evaluation_engine,
        path_service=path_service,
    )


def test_use_case_initialization(use_case_setup: SimpleNamespace) -> None:
    uc = use_case_setup.use_case
    assert uc._episode_repository is use_case_setup.episode_repository
    assert uc._project_repository is use_case_setup.project_repository
    assert uc._a31_checklist_repository is use_case_setup.checklist_repository
    assert uc._evaluation_engine is use_case_setup.evaluation_engine


@pytest.mark.asyncio
async def test_successful_complete_check(use_case_setup: SimpleNamespace, sample_checklist_items: list[A31ChecklistItem]) -> None:
    uc = use_case_setup.use_case
    use_case_setup.checklist_repository.get_all_checklist_items.return_value = sample_checklist_items

    request = A31CompleteCheckRequest(
        project_name="テストプロジェクト",
        episode_number=1,
        target_categories=[A31EvaluationCategory.FORMAT_CHECK, A31EvaluationCategory.CONTENT_BALANCE],
    )

    response = await uc.execute(request)

    assert response.success is True
    assert response.project_name == "テストプロジェクト"
    assert response.episode_number == 1
    assert response.total_items_checked == 2
    assert response.evaluation_batch is not None
    assert response.error_message is None


@pytest.mark.asyncio
async def test_episode_not_found_error(use_case_setup: SimpleNamespace, sample_checklist_items: list[A31ChecklistItem]) -> None:
    uc = use_case_setup.use_case
    use_case_setup.episode_repository.get_episode_content.side_effect = FileNotFoundError("missing")
    use_case_setup.checklist_repository.get_all_checklist_items.return_value = sample_checklist_items

    request = A31CompleteCheckRequest(project_name="テスト", episode_number=999)
    response = await uc.execute(request)

    assert response.success is False
    assert "エピソードファイルが見つかりません" in response.error_message
    assert response.total_items_checked == 0


@pytest.mark.asyncio
async def test_no_checklist_items_found(use_case_setup: SimpleNamespace) -> None:
    uc = use_case_setup.use_case
    use_case_setup.checklist_repository.get_all_checklist_items.return_value = []

    request = A31CompleteCheckRequest(project_name="テスト", episode_number=1)
    response = await uc.execute(request)

    assert response.success is False
    assert "対象のチェックリスト項目が見つかりません" in response.error_message


@pytest.mark.asyncio
async def test_category_filtering(
    use_case_setup: SimpleNamespace,
    sample_checklist_items: list[A31ChecklistItem],
    evaluation_engine: Mock,
) -> None:
    uc = use_case_setup.use_case
    use_case_setup.checklist_repository.get_all_checklist_items.return_value = sample_checklist_items

    request = A31CompleteCheckRequest(
        project_name="テスト",
        episode_number=1,
        target_categories=[A31EvaluationCategory.FORMAT_CHECK],
    )

    await uc.execute(request)

    passed_items = evaluation_engine.evaluate_all_items.call_args[0][1]
    assert len(passed_items) == 1
    assert passed_items[0].item_id == "A31-045"


@pytest.mark.asyncio
async def test_execute_by_category(use_case_setup: SimpleNamespace, sample_checklist_items: list[A31ChecklistItem]) -> None:
    uc = use_case_setup.use_case
    use_case_setup.checklist_repository.get_all_checklist_items.return_value = sample_checklist_items

    request = A31CompleteCheckRequest(project_name="テスト", episode_number=1)
    response = await uc.execute_by_category(request, A31EvaluationCategory.FORMAT_CHECK)

    assert response.success is True
    assert response.episode_number == 1


@pytest.mark.asyncio
async def test_get_evaluation_summary_success(
    use_case_setup: SimpleNamespace,
    sample_checklist_items: list[A31ChecklistItem],
) -> None:
    uc = use_case_setup.use_case
    use_case_setup.checklist_repository.get_all_checklist_items.return_value = sample_checklist_items

    request = A31CompleteCheckRequest(project_name="テスト", episode_number=1)
    response = await uc.execute(request)

    summary = uc.get_evaluation_summary(response)

    assert summary["success"] is True
    assert summary["total_items"] == 2
    assert summary["passed_items"] == 1
    assert summary["failed_items"] == 1


def test_get_evaluation_summary_failure(use_case_setup: SimpleNamespace) -> None:
    uc = use_case_setup.use_case
    response = A31CompleteCheckResponse(
        success=False,
        project_name="テスト",
        episode_number=1,
        evaluation_batch=A31EvaluationBatch({}, 0, 0, 0.0),
        error_message="テストエラー",
    )

    summary = uc.get_evaluation_summary(response)
    assert summary == {"success": False, "error": "テストエラー"}


def test_evaluation_context_preparation(use_case_setup: SimpleNamespace) -> None:
    uc = use_case_setup.use_case
    use_case_setup.episode_repository.get_episode_content.side_effect = ["前話コンテンツ"]

    context = uc._prepare_evaluation_context("テスト", 2)

    assert context["project_name"] == "テスト"
    assert context["episode_number"] == 2
    assert context["quality_threshold"] == 70.0
    assert context["previous_episode_content"] == "前話コンテンツ"


def test_save_checklist_results_success(use_case_setup: SimpleNamespace) -> None:
    uc = use_case_setup.use_case
    mock_batch = A31EvaluationBatch({}, 1, 1, 10.0)

    result_path = uc._save_checklist_results("テスト", 1, mock_batch)

    assert result_path == Path("generated_checklist.yaml")
    use_case_setup.checklist_repository.save_evaluation_results.assert_called_once_with("テスト", 1, mock_batch)


@pytest.mark.asyncio
async def test_complete_check_with_claude_integration(
    use_case_setup: SimpleNamespace,
    sample_checklist_items: list[A31ChecklistItem],
    sample_evaluation_batch: A31EvaluationBatch,
) -> None:
    uc = use_case_setup.use_case
    use_case_setup.checklist_repository.get_all_checklist_items.return_value = sample_checklist_items

    uc._claude_analyzer = object()
    uc._result_integrator = object()

    claude_payload = SimpleNamespace(
        success=True,
        analysis_result={
            "item_results": {
                "A31-045": SimpleNamespace(improvements=["改善案"], analysis_score=98.0, issues_found=["issue"])
            }
        },
    )
    uc._execute_claude_analysis_integration = AsyncMock(return_value=claude_payload)
    uc._merge_claude_results_with_local = Mock(return_value=sample_evaluation_batch)

    request = A31CompleteCheckRequest(
        project_name="テスト",
        episode_number=1,
        include_claude_analysis=True,
    )

    response = await uc.execute(request)

    uc._execute_claude_analysis_integration.assert_awaited()
    uc._merge_claude_results_with_local.assert_called_once()
    assert response.claude_analysis_applied is True


@pytest.mark.asyncio
async def test_complete_check_without_claude_integration(
    use_case_setup: SimpleNamespace,
    sample_checklist_items: list[A31ChecklistItem],
) -> None:
    uc = use_case_setup.use_case
    use_case_setup.checklist_repository.get_all_checklist_items.return_value = sample_checklist_items

    uc._claude_analyzer = None
    uc._result_integrator = None

    request = A31CompleteCheckRequest(
        project_name="テスト",
        episode_number=1,
        include_claude_analysis=True,
    )

    response = await uc.execute(request)

    uc._execute_claude_analysis_integration.assert_not_called()
    assert response.claude_analysis_applied is False
