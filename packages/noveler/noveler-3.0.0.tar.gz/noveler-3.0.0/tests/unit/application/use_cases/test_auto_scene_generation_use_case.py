"""AutoSceneGenerationUseCase の B20 版ユニットテスト"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from noveler.application.use_cases.auto_scene_generation_use_case import (
    AutoSceneGenerationRequest,
    AutoSceneGenerationUseCase,
    SceneType,
)


@pytest.fixture
def use_case() -> AutoSceneGenerationUseCase:
    episode_repository = Mock()
    plot_repository = Mock()
    return AutoSceneGenerationUseCase(episode_repository=episode_repository, plot_repository=plot_repository)


@pytest.mark.asyncio
async def test_execute_generates_content(use_case: AutoSceneGenerationUseCase) -> None:
    request = AutoSceneGenerationRequest(project_id="proj", episode_number=5, scene_type=SceneType.ACTION)

    response = await use_case.execute(request)

    assert response.success is True
    assert "episode 5" in response.generated_content
    assert response.word_count == len(response.generated_content)


@pytest.mark.asyncio
async def test_execute_handles_exception(use_case: AutoSceneGenerationUseCase) -> None:
    class BrokenSceneType:
        def __init__(self) -> None:
            pass  # value 属性なし

    request = AutoSceneGenerationRequest(project_id="proj", episode_number=5, scene_type=BrokenSceneType())  # type: ignore[arg-type]

    response = await use_case.execute(request)

    assert response.success is False
    assert response.error_details is not None
