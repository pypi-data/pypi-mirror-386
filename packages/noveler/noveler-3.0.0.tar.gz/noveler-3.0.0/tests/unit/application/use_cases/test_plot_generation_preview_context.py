"""Tests.unit.application.use_cases.test_plot_generation_preview_context
Where: Automated unit test module for plot generation use case.
What: Validates preview metadata bridging from quality records.
Why: Ensures plot services can consume enriched preview metadata.
"""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from noveler.application.use_cases.plot_generation_use_case import (  # noqa: E402  # pylint: disable=C0413
    PlotGenerationUseCase,
    load_previous_preview_context,
)
from noveler.domain.entities.quality_record import QualityRecord, QualityRecordEntry  # noqa: E402  # pylint: disable=C0413
from noveler.domain.value_objects.project_time import project_now  # noqa: E402  # pylint: disable=C0413
from noveler.domain.value_objects.quality_check_result import (  # noqa: E402  # pylint: disable=C0413
    AutoFix,
    CategoryScores,
    QualityCheckResult,
    QualityError,
    QualityScore,
)


@pytest.fixture
def sample_preview_metadata() -> dict:
    """Provide representative preview metadata sections."""
    return {
        "preview": {"hook": "次回への布石", "dominant_sentiment": "hope"},
        "quality": {"passed": True, "score": 0.92},
        "source": {"dialogue_sentence_count": 4},
        "config": {"preview_style": "summary"},
        "preview_text": "テストプレビュー",
    }


def _build_quality_record(metadata: dict, episode: int) -> QualityRecord:
    scores = CategoryScores(
        basic_style=QualityScore.from_float(85.0),
        composition=QualityScore.from_float(82.0),
        character_consistency=QualityScore.from_float(87.0),
        readability=QualityScore.from_float(88.0),
    )
    result = QualityCheckResult(
        episode_number=episode,
        timestamp=project_now().datetime,
        checker_version="test",
        category_scores=scores,
        errors=[],
        warnings=[],
        auto_fixes=[AutoFix(type="spacing", description="auto", count=1)],
    )
    entry = QualityRecordEntry.create_from_result(result, metadata)
    return QualityRecord("sample_project", [entry])


def test_load_previous_preview_context(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, sample_preview_metadata: dict) -> None:
    """PlotGenerationUseCase should surface preview metadata from quality records."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    quality_record = _build_quality_record(sample_preview_metadata, episode=1)

    class DummyRepo:
        def __init__(self, base_path: Path) -> None:
            assert base_path == project_root

        def find_by_project(self, project_name: str) -> QualityRecord | None:
            assert project_name == project_root.name
            return quality_record

    use_case = PlotGenerationUseCase()
    setattr(use_case, "_quality_record_repository_cls", DummyRepo)

    preview_context = load_previous_preview_context(project_root, episode_number=2, repository_cls=DummyRepo)

    expected = sample_preview_metadata.copy()
    expected["score"] = quality_record.entries[0].quality_result.overall_score.to_float()

    assert preview_context == expected

    # Episode 1 has no previous preview, expect None
    assert load_previous_preview_context(project_root, episode_number=1, repository_cls=DummyRepo) is None


def test_save_enhanced_prompt_includes_reference_sections(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sample_preview_metadata: dict,
) -> None:
    """_save_enhanced_prompt should copy preview/quality/source sections into content_sections."""

    from types import SimpleNamespace

    use_case = PlotGenerationUseCase()
    use_case._latest_preview_context = sample_preview_metadata | {"score": 0.91}  # type: ignore[assignment]

    dummy_plot = SimpleNamespace(chapter_number=SimpleNamespace(value=1))
    monkeypatch.setattr(use_case, "_get_chapter_plot_entity", lambda *_: dummy_plot)
    monkeypatch.setattr(use_case, "_get_previous_episodes", lambda *_: [{"episode_number": 2, "summary": "前話"}])
    monkeypatch.setattr(use_case, "_get_following_episodes", lambda *_: [])

    class DummyTemplateService:
        def generate_enhanced_prompt(self, _context) -> str:
            return "generated prompt"

    captured: dict[str, SimpleNamespace] = {}

    class DummyPromptSaveUseCase:
        def __init__(self, *args: object, **kwargs: object) -> None:  # pragma: no cover - simple stub
            self._args = args
            self._kwargs = kwargs

        def execute(self, request: SimpleNamespace) -> SimpleNamespace:
            captured["request"] = request
            return SimpleNamespace(
                success=True,
                saved_file_path=tmp_path / "dummy.yaml",
                quality_score=0.88,
                error_message=None,
            )

    monkeypatch.setattr(
        "noveler.domain.services.enhanced_prompt_template_service.EnhancedPromptTemplateService",
        lambda: DummyTemplateService(),
    )
    monkeypatch.setattr(
        "noveler.application.use_cases.episode_prompt_save_use_case.EpisodePromptSaveUseCase",
        DummyPromptSaveUseCase,
    )

    chapter_plot_info = {
        "chapter_number": 1,
        "episodes": [
            {
                "episode_number": 3,
                "title": "第003話",
                "summary": "今話の概要",
            }
        ],
    }

    generation_result = SimpleNamespace(quality_score=0.8, generated_plot="plot content")

    use_case._save_enhanced_prompt(
        episode_number=3,
        chapter_plot_info=chapter_plot_info,
        generation_result=generation_result,
        project_root=tmp_path,
    )

    request = captured.get("request")
    assert request is not None, "PromptSaveRequest was not captured"

    sections = request.content_sections
    assert "reference_sections" in sections
    reference_sections = sections["reference_sections"]

    assert reference_sections["episode_number"] == 2
    assert reference_sections["preview"] == sample_preview_metadata["preview"]
    assert reference_sections["quality"] == sample_preview_metadata["quality"]
    assert reference_sections["source"] == sample_preview_metadata["source"]
    assert reference_sections["config"] == sample_preview_metadata["config"]
    assert reference_sections["preview_text"] == sample_preview_metadata["preview_text"]
    assert reference_sections["score"] == pytest.approx(0.91)
