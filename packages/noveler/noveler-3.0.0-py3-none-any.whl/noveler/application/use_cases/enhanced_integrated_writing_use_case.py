#!/usr/bin/env python3

"""Application.use_cases.enhanced_integrated_writing_use_case
Where: Application use case orchestrating enhanced integrated writing flows.
What: Coordinates planning, drafting, and refinement services for integrated writing sessions.
Why: Provides a single entry point for advanced writing workflows without duplicate orchestration code.
"""

from __future__ import annotations



from typing import TYPE_CHECKING, Any

from noveler.application.use_cases.integrated_writing_use_case import (
    IntegratedWritingRequest,
    IntegratedWritingResponse,
    IntegratedWritingUseCase,
)
from noveler.infrastructure.logging.unified_logger import get_logger

if TYPE_CHECKING:
    from noveler.domain.repositories.episode_repository import EpisodeRepository
    from noveler.domain.repositories.plot_repository import PlotRepository
    from noveler.infrastructure.integrations.claude_code_integration_service import ClaudeCodeIntegrationService
    from noveler.infrastructure.repositories.ruamel_yaml_prompt_repository import RuamelYamlPromptRepository

logger = get_logger(__name__)

# Backwards-compatibility: some tests import EnhancedIntegratedWritingRequest
# from this module. It is an alias of IntegratedWritingRequest.
EnhancedIntegratedWritingRequest = IntegratedWritingRequest


class EnhancedIntegratedWritingUseCase(IntegratedWritingUseCase):
    """拡張統合執筆ユースケース

    IntegratedWritingUseCaseにClaude Code統合機能を追加
    - Claude Code統合サービス連携
    - 高度なプロンプト生成
    - エラー復旧機能強化
    """

    def __init__(
        self,
        claude_code_service: ClaudeCodeIntegrationService,
        yaml_prompt_repository: RuamelYamlPromptRepository,
        episode_repository: EpisodeRepository,
        plot_repository: PlotRepository,
        **kwargs: Any,
    ) -> None:
        """初期化

        Args:
            claude_code_service: Claude Code統合サービス
            yaml_prompt_repository: YAMLプロンプトリポジトリ
            episode_repository: エピソードリポジトリ
            plot_repository: プロットリポジトリ
            **kwargs: 基底クラスに渡される追加引数
        """
        # 基底クラス初期化
        super().__init__(**kwargs)

        # 拡張機能のサービス
        self.claude_code_service = claude_code_service
        self.yaml_prompt_repository = yaml_prompt_repository
        self.episode_repository = episode_repository
        self.plot_repository = plot_repository

        logger.debug("EnhancedIntegratedWritingUseCase initialized with Claude Code integration")

    async def execute(self, request: IntegratedWritingRequest) -> IntegratedWritingResponse:
        """拡張統合執筆ワークフロー実行

        Claude Code統合機能を使用した高度な執筆処理

        Args:
            request: 統合執筆リクエスト

        Returns:
            IntegratedWritingResponse: 実行結果
        """
        try:
            logger.info(f"Enhanced integrated writing started for episode {request.episode_number}")

            # Claude Code統合前処理
            await self._prepare_claude_code_integration(request)

            # 基本的な統合執筆実行
            response = await super().execute(request)

            # Claude Code統合後処理
            if response.success:
                return await self._enhance_with_claude_code(response, request)

            return response

        except Exception as e:
            logger.exception(f"Enhanced integrated writing failed: {e}")
            # エラー時はフォールバックとして基底クラス実行
            return await super().execute(request)

    async def _prepare_claude_code_integration(self, request: IntegratedWritingRequest) -> None:
        """Claude Code統合前処理

        Args:
            request: 統合執筆リクエスト
        """
        try:
            # Claude Code環境確認
            if self.claude_code_service:
                await self.claude_code_service.validate_environment()
                logger.debug("Claude Code environment validated")

        except Exception as e:
            logger.warning(f"Claude Code preparation failed: {e}")

    async def _enhance_with_claude_code(
        self, response: IntegratedWritingResponse, request: IntegratedWritingRequest
    ) -> IntegratedWritingResponse:
        """Claude Code統合による結果拡張

        Args:
            response: 基本実行結果
            request: 元のリクエスト

        Returns:
            IntegratedWritingResponse: 拡張された結果
        """
        try:
            if self.claude_code_service and response.manuscript_path:
                # Claude Codeによる品質チェックや拡張処理
                enhanced_metadata = await self.claude_code_service.enhance_manuscript(
                    manuscript_path=response.manuscript_path, episode_number=request.episode_number
                )

                # レスポンスにメタデータ追加
                if hasattr(response, "metadata"):
                    response.metadata.update(enhanced_metadata)

                logger.info(f"Manuscript enhanced with Claude Code for episode {request.episode_number}")

            return response

        except Exception as e:
            logger.warning(f"Claude Code enhancement failed: {e}")
            # エラー時は元のレスポンスをそのまま返す
            return response
