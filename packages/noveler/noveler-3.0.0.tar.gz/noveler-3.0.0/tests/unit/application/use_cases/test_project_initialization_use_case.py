"""Interactive project initialization use case tests.

The legacy ``ProjectInitializationUseCase`` shim has been removed and these tests
now target the actual implementation under ``noveler.application.use_cases.initialization``.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from noveler.application.use_cases.initialization.interactive_project_initializer import (
    InteractiveProjectInitializerUseCase,
    ProjectInitializationOrchestrator,
)
from noveler.domain.initialization.entities import (
    InitializationStatus,
    ProjectInitialization,
    ProjectTemplate,
)
from noveler.domain.initialization.services import TemplateRanking
from noveler.domain.initialization.value_objects import (
    Genre,
    InitializationConfig,
    UpdateFrequency,
    WritingStyle,
)


@pytest.fixture
def sample_user_inputs() -> dict[str, str]:
    """Valid user inputs consumed by the interactive initializer."""

    return {
        "project_name": "テスト小説プロジェクト",
        "author_name": "テスト作者",
        "genre": Genre.FANTASY.value,
        "writing_style": WritingStyle.LIGHT.value,
        "update_frequency": UpdateFrequency.DAILY.value,
    }


@pytest.fixture
def initializer_fixture() -> SimpleNamespace:
    """Create the interactive initializer with mocked dependencies."""

    template_repository = MagicMock()
    initialization_repository = MagicMock()
    template_selection_service = MagicMock()
    setup_service = MagicMock()
    quality_config_service = MagicMock()

    use_case = InteractiveProjectInitializerUseCase(
        template_repository=template_repository,
        initialization_repository=initialization_repository,
        template_selection_service=template_selection_service,
        setup_service=setup_service,
        quality_config_service=quality_config_service,
    )

    return SimpleNamespace(
        use_case=use_case,
        template_repository=template_repository,
        initialization_repository=initialization_repository,
        template_selection_service=template_selection_service,
        setup_service=setup_service,
        quality_config_service=quality_config_service,
    )


@pytest.fixture
def fantasy_template() -> ProjectTemplate:
    """Fixture that mimics a fantasy template entity."""

    template = ProjectTemplate(
        template_id="fantasy_basic",
        genre=Genre.FANTASY,
        name="Fantasy Basic",
        description="Fantasy starter template",
        directory_structure=["chapters", "characters", "notes"],
    )
    template.template_name = template.name  # attribute used by preview responses
    return template


def test_initialize_project_interactively_success(initializer_fixture: SimpleNamespace, sample_user_inputs: dict[str, str], fantasy_template: ProjectTemplate) -> None:
    """The initializer returns a success payload and persists the result."""

    deps = initializer_fixture
    deps.template_selection_service.select_optimal_template.return_value = fantasy_template.template_id
    deps.template_repository.find_by_id.return_value = fantasy_template
    deps.setup_service.generate_directory_structure.return_value = [
        "chapters",
        "characters",
        "notes",
        "drafts",
        "world",
        "exports",
    ]
    deps.setup_service.generate_initial_files.return_value = {
        "README.md": "",
        "outline.md": "",
    }
    deps.quality_config_service.generate_quality_standards.return_value = {
        "readability_target": 0.9,
        "world_building_consistency": 0.8,
    }

    result = deps.use_case.initialize_project_interactively(sample_user_inputs)

    assert result["success"] is True
    assert result["project_name"] == sample_user_inputs["project_name"]
    assert result["template_used"] == fantasy_template.template_id
    assert result["initial_files"] == ["README.md", "outline.md"]
    assert result["quality_standards"]["readability_target"] == 0.9

    deps.initialization_repository.save.assert_called_once()
    saved_initialization = deps.initialization_repository.save.call_args[0][0]
    assert isinstance(saved_initialization, ProjectInitialization)
    assert saved_initialization.selected_template_id == fantasy_template.template_id
    assert saved_initialization.status is InitializationStatus.COMPLETED


def test_initialize_project_interactively_returns_error_on_missing_template(initializer_fixture: SimpleNamespace, sample_user_inputs: dict[str, str]) -> None:
    """Missing templates surface a descriptive error without persisting state."""

    deps = initializer_fixture
    deps.template_selection_service.select_optimal_template.return_value = "fantasy_basic"
    deps.template_repository.find_by_id.return_value = None

    result = deps.use_case.initialize_project_interactively(sample_user_inputs)

    assert result == {"success": False, "error": "テンプレート fantasy_basic が見つかりません"}
    deps.initialization_repository.save.assert_not_called()


def test_preview_template_selection_returns_top_candidates(initializer_fixture: SimpleNamespace, sample_user_inputs: dict[str, str], fantasy_template: ProjectTemplate) -> None:
    """Preview lists the top template recommendations with human readable names."""

    deps = initializer_fixture
    other_template = ProjectTemplate(
        template_id="romance_emotional",
        genre=Genre.ROMANCE,
        name="Romance Emotional",
        description="",
    )
    other_template.template_name = other_template.name
    third_template = ProjectTemplate(
        template_id="mystery_logical",
        genre=Genre.MYSTERY,
        name="Mystery Logical",
        description="",
    )
    third_template.template_name = third_template.name

    deps.template_selection_service.rank_templates.return_value = [
        TemplateRanking(template_id="fantasy_basic", score=0.95, reasoning="ベストフィット"),
        TemplateRanking(template_id="romance_emotional", score=0.75, reasoning="代替案"),
        TemplateRanking(template_id="mystery_logical", score=0.72, reasoning="第三候補"),
    ]
    deps.template_repository.find_by_id.side_effect = [fantasy_template, other_template, third_template]

    result = deps.use_case.preview_template_selection(sample_user_inputs)

    assert result["success"] is True
    assert result["optimal_choice"] == {"template_id": "fantasy_basic", "template_name": "Fantasy Basic"}
    assert result["recommended_templates"] == [
        {"template_id": "fantasy_basic", "template_name": "Fantasy Basic"},
        {"template_id": "romance_emotional", "template_name": "Romance Emotional"},
        {"template_id": "mystery_logical", "template_name": "Mystery Logical"},
    ]


def test_preview_template_selection_handles_exception(initializer_fixture: SimpleNamespace, sample_user_inputs: dict[str, str]) -> None:
    """Any ranking failure is surfaced to the caller as an error payload."""

    deps = initializer_fixture
    deps.template_selection_service.rank_templates.side_effect = RuntimeError("ranking failed")

    result = deps.use_case.preview_template_selection(sample_user_inputs)

    assert result == {"success": False, "error": "ranking failed"}


def test_get_available_options_matches_enums(initializer_fixture: SimpleNamespace) -> None:
    """Enumerated options mirror the domain value objects."""

    result = initializer_fixture.use_case.get_available_options()

    assert set(result["genres"]) == {genre.value for genre in Genre}
    assert set(result["writing_styles"]) == {style.value for style in WritingStyle}
    assert set(result["update_frequencies"]) == {freq.value for freq in UpdateFrequency}


def test_get_initialization_history_returns_serialized_records(initializer_fixture: SimpleNamespace, fantasy_template: ProjectTemplate) -> None:
    """Initialization history is converted into a serializable structure."""

    deps = initializer_fixture
    config = InitializationConfig(
        genre=Genre.FANTASY,
        writing_style=WritingStyle.LIGHT,
        update_frequency=UpdateFrequency.DAILY,
        project_name="物語A",
        author_name="作者A",
    )
    initialization = ProjectInitialization(initialization_id="init-1", config=config)
    initialization.select_template(fantasy_template.template_id)
    initialization.validate_configuration()
    initialization.create_project_files()
    initialization.complete_initialization()

    deps.initialization_repository.find_recent_initializations.return_value = [initialization]

    history = deps.use_case.get_initialization_history(limit=1)

    assert len(history) == 1
    record = history[0]
    assert record["initialization_id"] == "init-1"
    assert record["project_name"] == "物語A"
    assert record["success"] is True


def test_get_initialization_history_handles_exception(initializer_fixture: SimpleNamespace) -> None:
    """Repository failures are surfaced as an error entry."""

    deps = initializer_fixture
    deps.initialization_repository.find_recent_initializations.side_effect = RuntimeError("db unavailable")

    history = deps.use_case.get_initialization_history(limit=5)

    assert history == [{"error": "db unavailable"}]


def test_orchestrator_execute_full_initialization_workflow_success(initializer_fixture: SimpleNamespace, sample_user_inputs: dict[str, str]) -> None:
    """The orchestrator runs all phases when intermediate steps succeed."""

    deps = initializer_fixture
    init_result = {
        "success": True,
        "initial_files": ["README.md"],
        "directory_structure": ["chapters", "characters", "notes", "drafts", "world", "exports"],
        "quality_standards": {"readability_target": 0.9},
        "template_used": "fantasy_basic",
    }
    preview_result = {"success": True, "recommended_templates": [], "optimal_choice": None}

    deps.use_case.preview_template_selection = MagicMock(return_value=preview_result)
    deps.use_case.initialize_project_interactively = MagicMock(return_value=init_result)

    orchestrator = ProjectInitializationOrchestrator(deps.use_case)

    workflow = orchestrator.execute_full_initialization_workflow(sample_user_inputs)

    assert workflow["phase_1_preview"] is preview_result
    assert workflow["phase_2_initialization"] is init_result
    assert workflow["phase_3_verification"]["success"] is True
    deps.use_case.preview_template_selection.assert_called_once_with(sample_user_inputs)
    deps.use_case.initialize_project_interactively.assert_called_once_with(sample_user_inputs)


def test_orchestrator_stops_when_preview_fails(initializer_fixture: SimpleNamespace, sample_user_inputs: dict[str, str]) -> None:
    """Early failure returns partial results without executing later phases."""

    deps = initializer_fixture
    preview_result = {"success": False, "error": "ranking failed"}
    deps.use_case.preview_template_selection = MagicMock(return_value=preview_result)
    deps.use_case.initialize_project_interactively = MagicMock()

    orchestrator = ProjectInitializationOrchestrator(deps.use_case)

    workflow = orchestrator.execute_full_initialization_workflow(sample_user_inputs)

    assert workflow == {
        "phase_1_preview": preview_result,
        "phase_2_initialization": None,
        "phase_3_verification": None,
    }
    deps.use_case.initialize_project_interactively.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__])
