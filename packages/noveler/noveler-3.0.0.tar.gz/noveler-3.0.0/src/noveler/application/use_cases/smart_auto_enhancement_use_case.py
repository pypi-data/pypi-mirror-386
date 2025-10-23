"""Smart Auto-Enhancement Use Case

SPEC-SAE-003: Smart Auto-Enhancement ユースケース仕様
- novel check コマンドのSmart Auto-Enhancement機能を実現
- ドメインサービスとインフラストラクチャを協調させる
- Clean Architecture原則に基づく実装
"""

import os
import traceback
from dataclasses import dataclass
from pathlib import Path

from noveler.domain.entities.smart_auto_enhancement import (
    EnhancementMode,
    EnhancementRequest,
    SmartAutoEnhancement,
)
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.project_info import ProjectInfo


@dataclass(frozen=True)
class SmartAutoEnhancementUseCaseRequest:
    """Smart Auto-Enhancement ユースケースリクエスト"""

    project_name: str
    episode_number: int
    mode: str = "smart_auto"  # "standard", "smart_auto", "detailed", "enhanced"
    skip_basic: bool = False
    skip_a31: bool = False
    skip_claude: bool = False
    auto_fix: bool = False
    show_detailed_review: bool = False
    rhythm_analysis: bool = False


@dataclass(frozen=True)
class SmartAutoEnhancementUseCaseResponse:
    """Smart Auto-Enhancement ユースケースレスポンス"""

    success: bool
    enhancement: SmartAutoEnhancement | None
    error_message: str | None
    execution_time_ms: float
    final_score: float | None
    improvements_count: int

    @property
    def is_smart_auto_executed(self) -> bool:
        """Smart Auto-Enhancement が実行されたか"""
        return self.enhancement is not None and self.enhancement.is_smart_auto_mode and self.enhancement.is_success()


class SmartAutoEnhancementUseCase:
    """Smart Auto-Enhancement ユースケース

    novel check コマンドのSmart Auto-Enhancement機能を実現する。
    ドメインサービスを活用し、統合的な品質チェックを提供する。
    """

    def __init__(
        self,
        logger_service: object,
        unit_of_work: object,
        enhancement_service: object | None = None,
        **kwargs: object,
    ) -> None:
        """初期化 - B20準拠

        Args:
            logger_service: ロガーサービス
            unit_of_work: Unit of Work
            enhancement_service: エンハンスメントサービス（オプション）
            **kwargs: AbstractUseCaseの引数
        """
        super().__init__(**kwargs)
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work
        # Unit of Workからエピソードリポジトリを取得
        self._episode_repository = unit_of_work.episode_repository
        self._enhancement_service = enhancement_service

    async def execute(self, request: SmartAutoEnhancementUseCaseRequest) -> SmartAutoEnhancementUseCaseResponse:
        """Smart Auto-Enhancement を実行

        Args:
            request: ユースケースリクエスト

        Returns:
            実行結果レスポンス
        """
        try:
            # エピソード内容を取得
            episode_content = await self._get_episode_content(request.project_name, request.episode_number)

            # ドメインリクエストを作成
            enhancement_request = self._create_enhancement_request(request)

            # Smart Auto-Enhancement エンティティを作成
            enhancement = SmartAutoEnhancement(enhancement_request)

            # ドメインサービスで拡張チェックを実行
            completed_enhancement = await self._enhancement_service.execute_enhancement(enhancement, episode_content)

            # レスポンスを作成
            return self._create_response(completed_enhancement)

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e) or '不明なエラー'}"
            traceback_msg = traceback.format_exc()
            full_error_msg = f"{error_msg}\n\nTraceback:\n{traceback_msg}"

            return SmartAutoEnhancementUseCaseResponse(
                success=False,
                enhancement=None,
                error_message=full_error_msg,
                execution_time_ms=0.0,
                final_score=None,
                improvements_count=0,
            )

    async def _get_episode_content(self, project_name: str, episode_number: int) -> str:
        """エピソード内容を取得"""
        try:
            return self._episode_repository.get_episode_content(project_name, episode_number)
        except Exception as e:
            msg = f"エピソード取得エラー: {e!s}"
            raise ValueError(msg) from e

    def _create_enhancement_request(self, request: SmartAutoEnhancementUseCaseRequest) -> EnhancementRequest:
        """ドメインリクエストを作成"""
        # モード変換
        mode_mapping = {
            "standard": EnhancementMode.STANDARD,
            "smart_auto": EnhancementMode.SMART_AUTO,
            "detailed": EnhancementMode.DETAILED,
            "enhanced": EnhancementMode.ENHANCED,
        }

        mode = mode_mapping.get(request.mode, EnhancementMode.SMART_AUTO)

        # Smart Auto-Enhancement のビジネスルール適用
        skip_basic = request.skip_basic
        skip_a31 = request.skip_a31
        skip_claude = request.skip_claude
        show_detailed_review = request.show_detailed_review

        if mode in [EnhancementMode.SMART_AUTO, EnhancementMode.ENHANCED]:
            # Smart Auto-Enhancement では全段階実行＋詳細表示
            skip_basic = False
            skip_a31 = False
            skip_claude = False
            show_detailed_review = True

        # PROJECT_ROOTから直接ProjectInfoを作成
        try:
            project_root_env = os.getenv("PROJECT_ROOT")
            if not project_root_env:
                msg = "PROJECT_ROOT環境変数が設定されていません"
                raise ValueError(msg)

            project_root = Path(project_root_env)
            config_path = project_root / "プロジェクト設定.yaml"

            if not config_path.exists():
                msg = f"プロジェクト設定ファイルが見つかりません: {config_path}"
                raise ValueError(msg)

            project_info = ProjectInfo(name=request.project_name, root_path=project_root, config_path=config_path)

        except Exception as e:
            msg = f"プロジェクト情報作成エラー: {e}"
            raise ValueError(msg) from e

        return EnhancementRequest(
            episode_number=EpisodeNumber(request.episode_number),
            project_info=project_info,
            mode=mode,
            skip_basic=skip_basic,
            skip_a31=skip_a31,
            skip_claude=skip_claude,
            auto_fix=request.auto_fix,
            show_detailed_review=show_detailed_review,
            rhythm_analysis=request.rhythm_analysis,
        )

    def _create_response(self, enhancement: SmartAutoEnhancement) -> SmartAutoEnhancementUseCaseResponse:
        """レスポンスを作成"""
        try:
            final_result = enhancement.get_final_result()
            final_score = None
            error_message = None

            if final_result:
                if final_result.get_final_score():
                    final_score = final_result.get_final_score().value
                error_message = final_result.error_message

            # final_resultがNoneでも、enhancementが失敗状態の場合はエラー情報を取得
            if not enhancement.is_success() and error_message is None:
                # 失敗した段階からエラーメッセージを取得
                from noveler.domain.entities.smart_auto_enhancement import EnhancementStage

                for stage in [
                    EnhancementStage.BASIC_CHECK,
                    EnhancementStage.A31_EVALUATION,
                    EnhancementStage.CLAUDE_ANALYSIS,
                    EnhancementStage.FAILED,
                ]:
                    stage_result = enhancement.get_stage_result(stage)
                    if stage_result and stage_result.error_message:
                        error_message = stage_result.error_message
                        break

                # それでもエラーメッセージがない場合のフォールバック
                if error_message is None:
                    error_message = "Smart Auto-Enhancement実行中に不明なエラーが発生しました"

            return SmartAutoEnhancementUseCaseResponse(
                success=enhancement.is_success(),
                enhancement=enhancement,
                error_message=error_message,
                execution_time_ms=enhancement.get_execution_duration_ms(),
                final_score=final_score,
                improvements_count=enhancement.get_total_improvements_count(),
            )
        except Exception as e:
            # _create_response自体でエラーが発生した場合のフォールバック
            return SmartAutoEnhancementUseCaseResponse(
                success=False,
                enhancement=None,
                error_message=f"レスポンス作成エラー: {e}",
                execution_time_ms=0.0,
                final_score=None,
                improvements_count=0,
            )

    def should_use_smart_auto_enhancement(self, request: SmartAutoEnhancementUseCaseRequest) -> bool:
        """Smart Auto-Enhancement の使用判定

        ビジネスルール:
        - mode が "smart_auto" または "enhanced"
        - または従来の "standard" でも全段階有効な場合は自動適用
        """
        if request.mode in ["smart_auto", "enhanced"]:
            return True

        # 従来モードでも全段階が有効な場合は Smart Auto-Enhancement を適用
        return bool(not (request.skip_basic and request.skip_a31 and request.skip_claude))
