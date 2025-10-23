#!/usr/bin/env python3

"""Application.use_cases.auto_scene_generation_use_case
Where: Application use case responsible for automated scene generation.
What: Coordinates domain services to create scene drafts based on project context.
Why: Streamlines scene creation so writers can iterate from system-generated drafts.
"""

from __future__ import annotations



from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.infrastructure.logging.unified_logger import get_logger

if TYPE_CHECKING:
    from noveler.domain.repositories.episode_repository import EpisodeRepository
    from noveler.domain.repositories.plot_repository import PlotRepository

logger = get_logger(__name__)


class SceneType(Enum):
    """シーンタイプ"""

    DIALOGUE = "dialogue"
    ACTION = "action"
    DESCRIPTION = "description"


@dataclass
class AutoSceneGenerationRequest:
    """自動シーン生成リクエスト"""

    project_id: str
    episode_number: int
    scene_type: SceneType = SceneType.DESCRIPTION
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AutoSceneGenerationResponse:
    """自動シーン生成レスポンス"""

    success: bool
    generated_content: str = ""
    word_count: int = 0
    error_details: str | None = None


class AutoSceneGenerationUseCase(AbstractUseCase[AutoSceneGenerationRequest, AutoSceneGenerationResponse]):
    """自動シーン生成ユースケース

    AIを活用した自動シーン生成処理
    """

    def __init__(self, episode_repository: EpisodeRepository, plot_repository: PlotRepository, **kwargs: Any) -> None:
        """初期化

        Args:
            episode_repository: エピソードリポジトリ
            plot_repository: プロットリポジトリ
            **kwargs: 基底クラスに渡される追加引数
        """
        super().__init__(**kwargs)
        self.episode_repository = episode_repository
        self.plot_repository = plot_repository

        logger.debug("AutoSceneGenerationUseCase initialized")

    async def execute(self, request: AutoSceneGenerationRequest) -> AutoSceneGenerationResponse:
        """自動シーン生成実行

        Args:
            request: 自動シーン生成リクエスト

        Returns:
            AutoSceneGenerationResponse: 生成結果
        """
        try:
            logger.info(f"Starting auto scene generation for episode {request.episode_number}")

            # 簡易実装
            generated_content = f"Generated {request.scene_type.value} scene for episode {request.episode_number}"

            return AutoSceneGenerationResponse(
                success=True, generated_content=generated_content, word_count=len(generated_content)
            )

        except Exception as e:
            logger.exception(f"Auto scene generation failed: {e}")
            return AutoSceneGenerationResponse(success=False, error_details=str(e))
