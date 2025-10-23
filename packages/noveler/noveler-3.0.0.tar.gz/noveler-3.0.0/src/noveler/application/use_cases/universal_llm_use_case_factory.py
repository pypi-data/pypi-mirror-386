#!/usr/bin/env python3
"""汎用Claude Code統合ユースケースファクトリー

DDD準拠：依存性注入管理
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from noveler.domain.value_objects.claude_code_integration_config import ClaudeCodeIntegrationConfig

from noveler.application.use_cases.universal_llm_use_case import (
    UniversalLLMUseCase,
)


class UniversalLLMUseCaseFactory:
    """汎用Claude Code統合ユースケースファクトリー

    DDD準拠：適切な依存性注入を管理
    """

    @staticmethod
    def create_use_case(config: Optional["ClaudeCodeIntegrationConfig"] = None) -> UniversalLLMUseCase:
        """ユースケース作成（依存性注入）

        Args:
            config: Claude Code統合設定

        Returns:
            UniversalLLMUseCase: 設定済みユースケース
        """
        # インフラ層依存の解決
        try:
            from noveler.infrastructure.integrations.universal_claude_code_service import UniversalClaudeCodeService

            universal_service = UniversalClaudeCodeService(config)
        except ImportError as e:
            msg = f"汎用Claude Code統合サービスの初期化に失敗: {e}"
            raise RuntimeError(msg)

        # プレゼンテーション層依存の解決（B30統一コンソール使用）
        from noveler.presentation.shared.shared_utilities import console

        console_service = console

        return UniversalLLMUseCase(universal_service=universal_service, console=console_service)
