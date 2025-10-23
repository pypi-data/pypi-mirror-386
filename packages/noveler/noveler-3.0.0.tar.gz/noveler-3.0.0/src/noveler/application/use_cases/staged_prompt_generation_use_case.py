"""
段階的プロンプト生成ユースケース

SPEC-STAGED-006: Application層での段階的プロンプト生成統合
- ドメインサービスとインフラストラクチャ層の統合
- 段階進行制御とエラー処理
- プロジェクト設定との統合
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from noveler.infrastructure.di.unified_repository_factory import UnifiedRepositoryFactory

from noveler.domain.entities.staged_prompt import StagedPrompt, StageTransitionError
from noveler.domain.services.staged_prompt_generation_service import (
    PromptGenerationResult,
    StagedPromptGenerationService,
    ValidationResult,
)
from noveler.domain.value_objects.prompt_stage import PromptStage, get_stage_by_number


@dataclass
class StagedPromptGenerationRequest:
    """段階的プロンプト生成リクエスト"""

    episode_number: int
    project_name: str
    project_root: Path | None = None
    target_stage: int | None = None  # None の場合は次段階
    generation_context: dict[str, Any] | None = None
    force_advance: bool = False  # 品質チェックを無視して強制進行
    save_to_file: bool = True  # ファイル保存するかどうか
    episode_title: str | None = None  # エピソードタイトル


@dataclass
class StagedPromptGenerationResponse:
    """段階的プロンプト生成レスポンス"""

    success: bool
    staged_prompt: StagedPrompt | None
    generated_prompt: str
    quality_score: float
    current_stage: int
    can_advance: bool
    execution_time_minutes: int
    warnings: list[str]
    error_message: str | None = None
    recommendations: dict[str, Any] | None = None
    saved_file_path: Path | None = None  # 保存されたファイルパス


@dataclass
class StageAdvanceRequest:
    """段階進行リクエスト"""

    staged_prompt: StagedPrompt
    target_stage: int
    generation_context: dict[str, Any]
    force_advance: bool = False


@dataclass
class StageAdvanceResponse:
    """段階進行レスポンス"""

    success: bool
    advanced_to_stage: int
    generation_result: PromptGenerationResult | None
    validation_result: ValidationResult | None
    error_message: str | None = None


class StagedPromptGenerationUseCase:
    """段階的プロンプト生成ユースケース

    段階的プロンプト生成の全体的なワークフローを管理し、
    ドメインサービスとインフラストラクチャ層を統合する。
    """

    def __init__(
        self,
        prompt_generation_service: StagedPromptGenerationService,
        project_root: Path,
        repository_factory: "UnifiedRepositoryFactory" = None,
    ) -> None:
        """ユースケース初期化（DDD準拠に修正）

        Args:
            prompt_generation_service: 段階的プロンプト生成ドメインサービス
            project_root: プロジェクトルートパス
            repository_factory: 統合リポジトリファクトリー（DI対応）
        """
        self._prompt_generation_service = prompt_generation_service
        self._project_root = project_root
        self._active_prompts: dict[str, StagedPrompt] = {}  # セッション管理

        # 統合リポジトリファクトリーのDI対応
        self._repository_factory = repository_factory or self._create_default_factory()

        # DDD準拠：統合ファクトリー経由でファイルサービス作成
        if self._repository_factory:
            self._file_service = self._repository_factory.create_staged_prompt_file_service()
        else:
            # DDD準拠フォールバック：依存性注入が必要
            self._file_service = None  # 依存性注入で設定される

    def _create_default_factory(self) -> "UnifiedRepositoryFactory":
        """デフォルトファクトリー作成（後方互換性維持）"""
        try:
            from noveler.infrastructure.di.unified_repository_factory import UnifiedRepositoryFactory

            return UnifiedRepositoryFactory(self._project_root)
        except ImportError:
            # フォールバック：緊急時対応
            return None

    async def generate_staged_prompt(self, request: StagedPromptGenerationRequest) -> StagedPromptGenerationResponse:
        """段階的プロンプト生成実行

        Args:
            request: 生成リクエスト

        Returns:
            生成レスポンス
        """
        start_time = datetime.now(timezone.utc)

        try:
            # StagedPromptエンティティの取得または作成
            staged_prompt = await self._get_or_create_staged_prompt(request)

            # 目標段階の決定
            target_stage = self._determine_target_stage(staged_prompt, request.target_stage)

            # 生成コンテキストの準備
            generation_context = await self._prepare_generation_context(staged_prompt, request.generation_context or {})

            # プロンプト生成実行
            generation_result = self._prompt_generation_service.generate_stage_prompt(
                staged_prompt=staged_prompt, target_stage=target_stage, context=generation_context
            )

            if not generation_result.success:
                return self._create_error_response(staged_prompt, generation_result.error_message, start_time)

            # 段階完了処理（強制進行でない場合）
            if not request.force_advance:
                completion_success = await self._complete_stage_if_valid(staged_prompt, target_stage, generation_result)

                if not completion_success:
                    return self._create_error_response(staged_prompt, "Stage completion failed", start_time)

            # 進行推奨の取得
            recommendations = self._prompt_generation_service.get_stage_progression_recommendation(staged_prompt)

            # ファイル保存処理
            saved_file_path = None
            if request.save_to_file:
                try:
                    saved_file_path = self._file_service.save_staged_prompt(
                        staged_prompt=staged_prompt,
                        generated_prompt=generation_result.generated_prompt,
                        stage_content=generation_result.stage_content,
                        episode_title=request.episode_title,
                    )

                except Exception as e:
                    generation_result.warnings.append(f"File save warning: {e!s}")

            execution_time = int((datetime.now(timezone.utc) - start_time).total_seconds() / 60)

            return StagedPromptGenerationResponse(
                success=True,
                staged_prompt=staged_prompt,
                generated_prompt=generation_result.generated_prompt,
                quality_score=generation_result.quality_score,
                current_stage=staged_prompt.current_stage.stage_number,
                can_advance=recommendations["can_advance"],
                execution_time_minutes=execution_time,
                warnings=generation_result.warnings,
                recommendations=recommendations,
                saved_file_path=saved_file_path,
            )

        except Exception as e:
            return self._create_error_response(None, f"Unexpected error: {e!s}", start_time)

    async def advance_to_stage(self, request: StageAdvanceRequest) -> StageAdvanceResponse:
        """段階進行実行

        Args:
            request: 段階進行リクエスト

        Returns:
            段階進行レスポンス
        """
        try:
            target_stage = get_stage_by_number(request.target_stage)

            # 進行可能性チェック
            if not request.force_advance and not request.staged_prompt.can_advance_to_stage(target_stage):
                return StageAdvanceResponse(
                    success=False,
                    advanced_to_stage=request.staged_prompt.current_stage.stage_number,
                    generation_result=None,
                    validation_result=None,
                    error_message=f"Cannot advance to stage {request.target_stage}",
                )

            # プロンプト生成
            generation_result = self._prompt_generation_service.generate_stage_prompt(
                staged_prompt=request.staged_prompt, target_stage=target_stage, context=request.generation_context
            )

            if not generation_result.success:
                return StageAdvanceResponse(
                    success=False,
                    advanced_to_stage=request.staged_prompt.current_stage.stage_number,
                    generation_result=generation_result,
                    validation_result=None,
                    error_message=generation_result.error_message,
                )

            # 段階進行実行
            request.staged_prompt.advance_to_stage(target_stage)

            # 段階完了処理
            request.staged_prompt.complete_current_stage(
                stage_result=generation_result.stage_content,
                quality_score=generation_result.quality_score,
                execution_time_minutes=generation_result.execution_time_minutes,
            )

            return StageAdvanceResponse(
                success=True,
                advanced_to_stage=request.target_stage,
                generation_result=generation_result,
                validation_result=None,
            )

        except StageTransitionError as e:
            return StageAdvanceResponse(
                success=False,
                advanced_to_stage=request.staged_prompt.current_stage.stage_number,
                generation_result=None,
                validation_result=None,
                error_message=str(e),
            )

        except Exception as e:
            return StageAdvanceResponse(
                success=False,
                advanced_to_stage=request.staged_prompt.current_stage.stage_number,
                generation_result=None,
                validation_result=None,
                error_message=f"Unexpected error: {e!s}",
            )

    async def validate_stage_completion(
        self, staged_prompt: StagedPrompt, stage: PromptStage, content: dict[str, Any]
    ) -> ValidationResult:
        """段階完了検証

        Args:
            staged_prompt: 段階的プロンプトエンティティ
            stage: 検証対象段階
            content: 検証対象コンテンツ

        Returns:
            検証結果
        """
        return self._prompt_generation_service.validate_stage_completion(
            staged_prompt=staged_prompt, stage=stage, generated_content=content
        )

    async def get_stage_progression_status(self, staged_prompt: StagedPrompt) -> dict[str, Any]:
        """段階進行状況取得

        Args:
            staged_prompt: 段階的プロンプトエンティティ

        Returns:
            進行状況辞書
        """
        recommendations = self._prompt_generation_service.get_stage_progression_recommendation(staged_prompt)

        status_summary = staged_prompt.get_status_summary()

        return {**status_summary, **recommendations, "available_actions": self._get_available_actions(staged_prompt)}

    async def rollback_to_stage(self, staged_prompt: StagedPrompt, target_stage_number: int) -> bool:
        """段階戻り実行

        Args:
            staged_prompt: 段階的プロンプトエンティティ
            target_stage_number: 目標段階番号

        Returns:
            成功した場合True
        """
        try:
            target_stage = get_stage_by_number(target_stage_number)
            return staged_prompt.rollback_to_stage(target_stage)
        except Exception:
            return False

    async def _get_or_create_staged_prompt(self, request: StagedPromptGenerationRequest) -> StagedPrompt:
        """StagedPromptエンティティの取得または作成

        Args:
            request: 生成リクエスト

        Returns:
            StagedPromptエンティティ
        """
        prompt_key = f"{request.project_name}:{request.episode_number}"

        # キャッシュから取得を試行
        if prompt_key in self._active_prompts:
            return self._active_prompts[prompt_key]

        # 新規作成
        staged_prompt = StagedPrompt(
            episode_number=request.episode_number,
            project_name=request.project_name,
            project_root=request.project_root or self._project_root,
        )

        self._active_prompts[prompt_key] = staged_prompt
        return staged_prompt

    def _determine_target_stage(self, staged_prompt: StagedPrompt, requested_stage: int | None) -> PromptStage:
        """目標段階の決定

        Args:
            staged_prompt: 段階的プロンプトエンティティ
            requested_stage: リクエストされた段階番号

        Returns:
            目標段階
        """
        if requested_stage is not None:
            return get_stage_by_number(requested_stage)

        # 次段階を取得
        next_stage = staged_prompt.get_next_stage()
        if next_stage is not None:
            return next_stage

        # 現在段階を返す（最終段階の場合）
        return staged_prompt.current_stage

    async def _prepare_generation_context(
        self, staged_prompt: StagedPrompt, base_context: dict[str, Any]
    ) -> dict[str, Any]:
        """生成コンテキストの準備

        Args:
            staged_prompt: 段階的プロンプトエンティティ
            base_context: ベースコンテキスト

        Returns:
            準備済みコンテキスト
        """
        context = base_context.copy()

        # プロジェクト情報の追加
        context.update(
            {
                "episode_number": staged_prompt.episode_number,
                "project_name": staged_prompt.project_name,
                "project_root": str(staged_prompt.project_root) if staged_prompt.project_root else None,
            }
        )

        # 前段階結果の統合
        for completed_stage in staged_prompt.completed_stages:
            stage_result = staged_prompt.get_stage_result(completed_stage)
            if stage_result:
                context[f"stage_{completed_stage.stage_number}_result"] = stage_result

        return context

    async def _complete_stage_if_valid(
        self, staged_prompt: StagedPrompt, stage: PromptStage, generation_result: PromptGenerationResult
    ) -> bool:
        """段階完了処理（検証付き）

        Args:
            staged_prompt: 段階的プロンプトエンティティ
            stage: 完了対象段階
            generation_result: 生成結果

        Returns:
            成功した場合True
        """
        try:
            # 段階完了検証
            validation_result = self._prompt_generation_service.validate_stage_completion(
                staged_prompt=staged_prompt, stage=stage, generated_content=generation_result.stage_content
            )

            # 検証が成功した場合のみ完了
            if validation_result.is_valid:
                staged_prompt.complete_current_stage(
                    stage_result=generation_result.stage_content,
                    quality_score=validation_result.quality_score,
                    execution_time_minutes=generation_result.execution_time_minutes,
                )

                return True

            return False

        except Exception:
            return False

    def _get_available_actions(self, staged_prompt: StagedPrompt) -> list[str]:
        """利用可能アクションの取得

        Args:
            staged_prompt: 段階的プロンプトエンティティ

        Returns:
            利用可能アクションのリスト
        """
        actions = []

        # 次段階進行
        next_stage = staged_prompt.get_next_stage()
        if next_stage and staged_prompt.can_advance_to_stage(next_stage):
            actions.append(f"advance_to_stage_{next_stage.stage_number}")

        # 段階戻り
        if staged_prompt.current_stage.stage_number > 1:
            actions.extend([
                f"rollback_to_stage_{stage_num}"
                for stage_num in range(1, staged_prompt.current_stage.stage_number)
            ])

        # 現段階再生成
        actions.append(f"regenerate_stage_{staged_prompt.current_stage.stage_number}")

        return actions

    def _create_error_response(
        self, staged_prompt: StagedPrompt | None, error_message: str, start_time: datetime
    ) -> StagedPromptGenerationResponse:
        """エラーレスポンス作成

        Args:
            staged_prompt: 段階的プロンプトエンティティ（None可）
            error_message: エラーメッセージ
            start_time: 開始時間

        Returns:
            エラーレスポンス
        """
        execution_time = int((datetime.now(timezone.utc) - start_time).total_seconds() / 60)
        current_stage = staged_prompt.current_stage.stage_number if staged_prompt else 1

        return StagedPromptGenerationResponse(
            success=False,
            staged_prompt=staged_prompt,
            generated_prompt="",
            quality_score=0.0,
            current_stage=current_stage,
            can_advance=False,
            execution_time_minutes=execution_time,
            warnings=[],
            error_message=error_message,
        )

    def clear_session(self, episode_number: int, project_name: str) -> None:
        """セッションクリア

        Args:
            episode_number: エピソード番号
            project_name: プロジェクト名
        """
        prompt_key = f"{project_name}:{episode_number}"
        if prompt_key in self._active_prompts:
            del self._active_prompts[prompt_key]

    def get_active_sessions(self) -> dict[str, dict[str, Any]]:
        """アクティブセッション取得

        Returns:
            アクティブセッション辞書
        """
        return {key: prompt.get_status_summary() for key, prompt in self._active_prompts.items()}
