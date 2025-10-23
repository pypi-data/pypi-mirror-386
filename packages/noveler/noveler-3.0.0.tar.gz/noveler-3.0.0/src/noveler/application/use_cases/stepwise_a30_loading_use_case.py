#!/usr/bin/env python3

"""Application.use_cases.stepwise_a30_loading_use_case
Where: Application use case orchestrating the stepwise A30 loading process.
What: Guides users through staged loading steps, validating progress at each phase.
Why: Provides a structured flow so large A30 imports stay reliable and auditable.
"""

from __future__ import annotations



import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from noveler.domain.interfaces.console_service_protocol import IConsoleService
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.domain.interfaces.path_service_protocol import IPathService
    from noveler.infrastructure.unit_of_work import IUnitOfWork

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.entities.a30_guide_content import A30GuideContent
from noveler.domain.services.stepwise_a30_guide_loader import StepwiseA30GuideLoader
from noveler.domain.value_objects.writing_phase import WritingPhase


@dataclass
class StepwiseA30LoadingRequest:
    """段階的A30読み込みリクエスト"""

    phase: WritingPhase
    project_name: str
    problem_type: str | None = None
    guide_root_path: Path | None = None
    use_configuration_service: bool = False


@dataclass
class StepwiseA30LoadingResponse:
    """段階的A30読み込みレスポンス"""

    success: bool
    guide_content: A30GuideContent | None = None
    error_message: str | None = None
    execution_time_ms: float = 0.0
    fallback_executed: bool = False
    configuration_service_used: bool = False
    relevant_troubleshooting_items: list[str] = field(default_factory=list)
    # 追加属性
    loaded_files_count: int = 0
    performance_improvement: float = 0.0
    phase: WritingPhase | None = None

    # 互換性のためのプロパティ
    @property
    def loading_time_ms(self) -> float:
        """execution_time_msの別名（互換性）"""
        return self.execution_time_ms


class StepwiseA30LoadingUseCase(AbstractUseCase[StepwiseA30LoadingRequest, StepwiseA30LoadingResponse]):
    """段階的A30読み込みユースケース

    執筆フェーズに応じた適切なA30ガイドコンテンツの読み込みを提供
    """

    def __init__(self,
        logger_service: ILoggerService = None,
        unit_of_work: IUnitOfWork = None,
        console_service: IConsoleService | None = None,
        path_service: IPathService | None = None,
        guide_loader = None,
        **kwargs) -> None:
        """初期化

        Args:
            guide_loader: 段階的ガイドローダー（未指定時はデフォルト作成）
            console_service: コンソールサービス（DI注入）
            path_service: パスサービス（DI注入）
        """
        # 基底クラス初期化（共通サービス）
        super().__init__(console_service=console_service, path_service=path_service, **kwargs)
        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work


        default_logger = logger_service or self.logger
        self._default_logger = default_logger
        self._guide_loader = guide_loader or StepwiseA30GuideLoader(default_logger)

    def execute(self, request: StepwiseA30LoadingRequest) -> StepwiseA30LoadingResponse:
        """段階的A30読み込み実行

        Args:
            request: 読み込みリクエスト

        Returns:
            StepwiseA30LoadingResponse: 読み込み結果
        """
        start_time = time.time()

        try:
            # リクエスト検証
            validation_result = self._validate_request(request)
            if not validation_result["is_valid"]:
                return StepwiseA30LoadingResponse(
                    success=False,
                    error_message=f"Invalid request: {validation_result['error']}",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # 設定サービス統合（設定フラグが有効な場合）
            if request.use_configuration_service:
                self._configure_with_configuration_service(request)

            # ガイドローダーの設定（カスタムパスが指定された場合）
            if request.guide_root_path:
                guide_loader = StepwiseA30GuideLoader(self._default_logger, request.guide_root_path)
            else:
                guide_loader = self._guide_loader

            # フェーズに応じたコンテンツ読み込み
            guide_content = guide_loader.load_for_phase(request.phase)

            # トラブルシューティング項目の抽出（必要な場合）
            relevant_items = self._extract_relevant_troubleshooting_items(guide_content, request.problem_type)

            # フォールバック実行の判定
            fallback_executed = self._was_fallback_executed(guide_content)

            execution_time = (time.time() - start_time) * 1000

            return StepwiseA30LoadingResponse(
                success=True,
                guide_content=guide_content,
                execution_time_ms=execution_time,
                fallback_executed=fallback_executed,
                configuration_service_used=request.use_configuration_service,
                relevant_troubleshooting_items=relevant_items,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.exception("段階的A30読み込みエラー")

            # フォールバック実行
            try:
                fallback_content = self._create_emergency_fallback_content(request.phase)
                return StepwiseA30LoadingResponse(
                    success=True,
                    guide_content=fallback_content,
                    execution_time_ms=execution_time,
                    fallback_executed=True,
                    configuration_service_used=request.use_configuration_service,
                )

            except Exception:
                return StepwiseA30LoadingResponse(success=False, error_message=str(e), execution_time_ms=execution_time)

    def _validate_request(self, request: StepwiseA30LoadingRequest) -> dict[str, Any]:
        """リクエスト妥当性検証

        Args:
            request: 検証対象リクエスト

        Returns:
            dict[str, Any]: 検証結果
        """
        if request.phase is None:
            return {"is_valid": False, "error": "フェーズが指定されていません"}

        if not request.project_name:
            return {"is_valid": False, "error": "プロジェクト名が指定されていません"}

        return {"is_valid": True}

    def _configure_with_configuration_service(self, request: StepwiseA30LoadingRequest) -> None:
        """統合設定管理システムとの連携設定

        Args:
            request: 設定対象リクエスト
        """
        try:
            # DDD準拠: AbstractUseCaseのconfig_serviceを使用（Infrastructure依存排除）
            config_manager = self.config_service

            # A30ガイド関連設定の取得
            a30_guide_root = config_manager.get_path_setting("a30_guide", "guide_root_path")
            if a30_guide_root and not request.guide_root_path:
                request.guide_root_path = Path(a30_guide_root)
                self.logger.info("統合設定からA30ガイドパス設定: %s", a30_guide_root)

            # フェーズ別設定の確認
            phase_setting = config_manager.get_default_setting("a30_guide", f"{request.phase.value}_mode", "standard")
            self.logger.info("フェーズ%sの設定モード: %s", (request.phase.value), phase_setting)

            # パフォーマンス関連設定
            enable_caching = config_manager.is_feature_enabled("a30_guide", "content_caching")
            if enable_caching:
                self.logger.info("A30ガイドコンテンツキャッシュが有効")

        except ImportError:
            self.logger.warning("統合設定管理システムが利用できません - デフォルト設定を使用")
        except Exception:
            self.logger.exception("統合設定管理システム連携エラー - デフォルト設定を使用")

    def _extract_relevant_troubleshooting_items(
        self, guide_content: A30GuideContent, problem_type: str | None
    ) -> list[str]:
        """関連するトラブルシューティング項目の抽出

        Args:
            guide_content: ガイドコンテンツ
            problem_type: 問題タイプ

        Returns:
            list[str]: 関連項目リスト
        """
        if not guide_content.troubleshooting_guide:
            return []

        # フォールバック用の基本項目を生成
        if problem_type:
            # 既に_issuesで終わっている場合はそのまま、そうでなければ_issuesを付加
            item = problem_type if problem_type.endswith("_issues") else f"{problem_type}_issues"
            return [item]

        # デフォルトのトラブルシューティング項目
        return ["dialogue_issues", "plot_consistency", "character_development"]

    def _was_fallback_executed(self, guide_content: A30GuideContent) -> bool:
        """フォールバック実行の判定

        Args:
            guide_content: ガイドコンテンツ

        Returns:
            bool: フォールバックが実行された場合True
        """
        if not guide_content.master_guide:
            return True

        metadata = guide_content.master_guide.get("metadata", {})
        return metadata.get("source") == "fallback"

    def _create_emergency_fallback_content(self, phase: WritingPhase) -> A30GuideContent:
        """緊急時フォールバックコンテンツの作成

        Args:
            phase: 対象フェーズ

        Returns:
            A30GuideContent: 緊急時用コンテンツ
        """
        emergency_content = {
            "metadata": {"source": "emergency_fallback", "phase": phase.value},
            "rules": ["基本的な執筆ルール"],
            "emergency": True,
        }

        # フェーズ別の追加コンテンツ
        additional_content = {}
        if phase == WritingPhase.TROUBLESHOOTING:
            additional_content["troubleshooting_guide"] = {
                "common_issues": ["文章の冗長性", "キャラクターの一貫性"],
                "solutions": ["簡潔な表現を心がける", "キャラクター設定を再確認"],
            }
        elif phase == WritingPhase.REFINEMENT:
            additional_content["detailed_rules"] = {
                "style": ["読みやすさ重視", "適切な改行"],
                "quality": ["誤字脱字チェック", "論理的構成"],
            }
            additional_content["quality_checklist"] = {
                "structure": ["論理的構成確認"],
                "style": ["表現の一貫性チェック"],
            }
        elif phase == WritingPhase.DRAFT:
            additional_content["quality_checklist"] = {"structure": ["起承転結の確認"], "content": ["テーマの一貫性"]}

        return A30GuideContent(
            master_guide=emergency_content,
            troubleshooting_guide=additional_content.get("troubleshooting_guide"),
            detailed_rules=additional_content.get("detailed_rules"),
            quality_checklist=additional_content.get("quality_checklist"),
            phase=phase,
        )
