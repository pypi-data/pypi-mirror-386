"""
エピソードプロンプト保存ユースケース

SPEC-PROMPT-SAVE-001: プロンプト保存機能仕様書準拠
"""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from noveler.domain.interfaces.console_service_protocol import IConsoleService
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.domain.interfaces.path_service_protocol import IPathService
    from noveler.infrastructure.unit_of_work import IUnitOfWork

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.application.orchestrators.error_handling_orchestrator import ErrorHandlingOrchestrator
from noveler.domain.entities.episode_prompt import EpisodePrompt
from noveler.domain.repositories.episode_prompt_repository import EpisodePromptRepository
from noveler.domain.value_objects.error_response import ErrorResponse
from noveler.domain.value_objects.prompt_save_result import PromptSaveResult

# DDD準拠: Infrastructure層への直接依存を排除（遅延初期化で対応）
# from noveler.infrastructure.di.unified_repository_factory import UnifiedRepositoryFactory


@dataclass
class PromptSaveRequest:
    """プロンプト保存リクエスト"""

    episode_number: int
    episode_title: str
    prompt_content: str
    project_root: Path | None = None
    content_sections: dict[str, Any] | None = None
    generation_mode: str = "enhanced"
    quality_level: str = "detailed"


@dataclass
class PromptSaveResponse:
    """プロンプト保存レスポンス"""

    success: bool
    saved_file_path: Path | None = None
    episode_prompt: EpisodePrompt | None = None
    error_message: str | None = None
    quality_score: float = 0.0


class EpisodePromptSaveUseCase(AbstractUseCase[PromptSaveRequest, PromptSaveResponse]):
    """エピソードプロンプト保存ユースケース

    責務:
    - エピソードプロンプトのドメインエンティティ作成
    - プロンプト保存先パス管理（CommonPathService統合）
    - ファイル保存処理の協調
    - エラーハンドリング統合
    """

    def __init__(self,
        logger_service: "ILoggerService" = None,
        unit_of_work: "IUnitOfWork" = None,
        console_service: Optional["IConsoleService"] = None,
        path_service: Optional["IPathService"] = None,
        repository_factory = None,
        **kwargs) -> None:
        """ユースケース初期化

        Args:
            repository_factory: 統合リポジトリファクトリー（DI対応）
            console_service: コンソールサービス（DI注入）
            path_service: パスサービス（DI注入）
        """
        # 基底クラス初期化（共通サービス）
        super().__init__(console_service=console_service, path_service=path_service, **kwargs)
        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work


        # DDD準拠: Infrastructure層への直接依存を回避（遅延初期化）
        self._repository_factory = repository_factory

        # 遅延初期化による依存関係管理
        self._prompt_repository = None
        self._error_orchestrator = None

    def _get_repository_factory(self) -> Any:
        # 不要な行を削除（下でself.repository_factoryを使用している）
        """統合リポジトリファクトリーの遅延初期化"""
        if self._repository_factory is None:
            # DDD準拠: Application→Infrastructure違反を遅延初期化で回避
            try:
                from noveler.infrastructure.di.unified_repository_factory import UnifiedRepositoryFactory

                self._repository_factory = UnifiedRepositoryFactory()
            except ImportError:
                self._repository_factory = None
        return self._repository_factory

    def _get_prompt_repository(self) -> Any:
        """プロンプトリポジトリの遅延初期化"""
        if self._prompt_repository is None:
            # DDD準拠: Application→Infrastructure違反を遅延初期化で回避
            try:
                from noveler.infrastructure.repositories.episode_prompt_repository import EpisodePromptRepository

                self._prompt_repository = EpisodePromptRepository()
            except ImportError:
                self._prompt_repository = None
        return self._prompt_repository

    @property
    def prompt_repository(self) -> Any:
        """プロンプトリポジトリプロパティ"""
        return self._get_prompt_repository()
        # DDD準拠 Constructor Injection パターン:
        # def __init__(self,
        #     logger_service: "ILoggerService" = None,
        #     unit_of_work: "IUnitOfWork" = None,
        #     **kwargs) -> None:
        #     self._repository_factory = repository_factory
        #     self._claude_adapter = claude_adapter
        #     self._template_adapter = template_adapter
        #     self._error_logger = error_logger

    def execute(self, request: PromptSaveRequest) -> PromptSaveResponse:
        """プロンプト保存実行

        Args:
            request: 保存リクエスト

        Returns:
            PromptSaveResponse: 保存結果
        """
        try:
            # 1. エピソードプロンプトエンティティ作成
            episode_prompt = self._create_episode_prompt(request)

            # 2. 保存先パス決定
            save_path = self._determine_save_path(request, episode_prompt)

            # 3. プロンプトリポジトリによる保存実行
            save_result = self._save_prompt(episode_prompt, save_path)

            if save_result.success:
                return PromptSaveResponse(
                    success=True,
                    saved_file_path=save_result.file_path,
                    episode_prompt=episode_prompt,
                    quality_score=episode_prompt.get_content_quality_score(),
                )

            return PromptSaveResponse(success=False, error_message=save_result.error_message)

        except FileNotFoundError as fnf_err:
            message = f"プロジェクトルートエラー: {fnf_err}"
            return PromptSaveResponse(success=False, error_message=message)
        except Exception as e:
            # エラーオーケストレーター連携
            try:
                error_response = self._handle_error(e, request)
                error_message = error_response.user_message if error_response else f"Error: {e!s}"
            except Exception:
                error_message = f"プロンプト保存エラー: {e!s}"

            return PromptSaveResponse(success=False, error_message=error_message)

    def _create_episode_prompt(self, request: PromptSaveRequest) -> EpisodePrompt:
        """エピソードプロンプトエンティティ作成

        Args:
            request: 保存リクエスト

        Returns:
            EpisodePrompt: 作成されたエンティティ
        """
        episode_prompt = EpisodePrompt(
            episode_number=request.episode_number,
            title=request.episode_title,
            prompt_content=request.prompt_content,
            generation_mode=request.generation_mode,
            quality_level=request.quality_level,
        )

        # コンテンツセクション追加
        if request.content_sections:
            for section_name, section_data in request.content_sections.items():
                episode_prompt.add_content_section(section_name, section_data)

        return episode_prompt

    def _determine_save_path(self, request: PromptSaveRequest, episode_prompt: EpisodePrompt) -> Path:
        """保存先パス決定

        Args:
            request: 保存リクエスト
            episode_prompt: エピソードプロンプトエンティティ

        Returns:
            Path: 保存先パス
        """
        project_root_path = self._normalise_project_root(request.project_root)
        if project_root_path and not project_root_path.exists():
            raise FileNotFoundError(f"Project root not found: {project_root_path}")

        # CommonPathServiceを使用して統一パス規約に従う
        path_service = None
        try:
            from noveler.presentation.shared.shared_utilities import get_common_path_service

            path_service = get_common_path_service()
            if path_service is None and project_root_path is not None:
                path_service = get_common_path_service(project_root_path)
        except Exception:
            path_service = None

        if path_service is None:
            path_service = self.get_path_service(project_root_path)

        prompt_dir = self._ensure_episode_prompt_dir(path_service, project_root_path)

        # ファイル名生成（バリューオブジェクト活用）
        filename = episode_prompt.get_file_name()

        return prompt_dir / filename.to_filename()

    def _normalise_project_root(self, explicit_root: Any | None) -> Path:
        """リクエストのプロジェクトルートをPath型に正規化"""

        if isinstance(explicit_root, Path):
            return explicit_root
        if isinstance(explicit_root, str):
            return Path(explicit_root)
        return self._get_project_root()


    def _ensure_episode_prompt_dir(self, path_service: Any, project_root: Path) -> Path:
        """エピソードプロンプト保存ディレクトリを取得し存在を保証"""

        def _as_path(value: Any) -> Path | None:
            try:
                return Path(value)
            except TypeError:
                return None

        service_root = _as_path(getattr(path_service, "project_root", None))
        base_root = service_root or project_root

        prompt_dir = None
        if hasattr(path_service, "get_episode_prompts_dir"):
            prompt_candidate = Path(path_service.get_episode_prompts_dir())
            if prompt_candidate.is_absolute():
                prompt_dir = prompt_candidate
            else:
                prompt_dir = (base_root or project_root) / prompt_candidate

        if prompt_dir is None:
            if hasattr(path_service, "get_prompts_dir"):
                prompt_base = Path(path_service.get_prompts_dir())
            else:
                prompt_base = Path("60_プロンプト")

            if prompt_base.is_absolute():
                prompt_dir = prompt_base / "話別プロット"
            else:
                prompt_dir = (base_root or project_root) / prompt_base / "話別プロット"

        prompt_dir.mkdir(parents=True, exist_ok=True)
        return prompt_dir

    def _save_prompt(self, episode_prompt: EpisodePrompt, save_path: Path) -> "PromptSaveResult":
        """プロンプトリポジトリによる保存

        Args:
            episode_prompt: 保存対象エンティティ
            save_path: 保存先パス

        Returns:
            PromptSaveResult: 保存結果
        """
        # リポジトリの遅延初期化（統合ファクトリー経由）
        if self._prompt_repository is None:
            self._prompt_repository = self._create_prompt_repository()

        return self._prompt_repository.save_prompt(episode_prompt, save_path)

    def _create_prompt_repository(self) -> "EpisodePromptRepository":
        """プロンプトリポジトリ作成（DDD準拠）"""
        # 統合リポジトリファクトリー経由でDDD準拠化
        if self._repository_factory:
            return self._repository_factory.create_episode_prompt_repository()

        # フォールバック：Infrastructure実装に直接依存（緊急時のみ）
        try:
            from noveler.infrastructure.repositories.episode_prompt_repository import (
                EpisodePromptRepository as InfraEpisodePromptRepository,
            )

            return InfraEpisodePromptRepository()
        except ImportError:
            # 取得に失敗した場合はNoneを返す（呼び出し側でハンドリング）
            return None

    def _get_project_root(self) -> Path:
        """プロジェクトルート取得"""
        import os

        env_project_root = os.environ.get("PROJECT_ROOT")
        if env_project_root:
            return Path(env_project_root)
        return Path.cwd()

    def _handle_error(self, exception: Exception, request: PromptSaveRequest) -> "ErrorResponse":
        """エラーハンドリング統合

        Args:
            exception: 発生した例外
            request: 元のリクエスト

        Returns:
            ErrorResponse: エラー応答
        """
        # エラーオーケストレーターの遅延初期化
        if self._error_orchestrator is None:
            self._error_orchestrator = self._create_error_orchestrator()

        from noveler.application.orchestrators.error_handling_orchestrator import ErrorHandlingRequest

        error_request = ErrorHandlingRequest(
            exception=exception,
            context={
                "operation_id": f"prompt_save_{request.episode_number}",
                "user_context": {
                    "operation_name": "episode_prompt_save",
                    "episode_number": request.episode_number,
                    "episode_title": request.episode_title,
                },
            },
            operation_name="prompt_save",
        )

        error_result = self._error_orchestrator.handle_error(error_request)
        return error_result.business_error_result

    def _create_error_orchestrator(self) -> "ErrorHandlingOrchestrator":
        """エラーハンドリングオーケストレーター作成（DDD準拠）"""
        from noveler.application.orchestrators.error_handling_orchestrator import ErrorHandlingOrchestrator
        from noveler.domain.services.error_classification_service import ErrorClassificationService
        from noveler.domain.services.error_recovery_service import ErrorRecoveryService
        from noveler.domain.services.error_reporting_service import ErrorReportingService

        # 統合リポジトリファクトリー経由でErrorLoggingAdapter取得（DDD準拠）
        if self._repository_factory:
            error_logging_adapter = self._repository_factory.create_error_logging_adapter()
        else:
            # フォールバック：統合ファクトリー作成
            try:
                # TODO: DI - Infrastructure DI container removed for DDD compliance
                # Use Application Factory interface via DI container instead
                # TODO: DI - Inject IRepositoryFactory via constructor
                factory = None  # 仮実装 - 後でDIコンテナで修正
                error_logging_adapter = factory.create_error_logging_adapter() if factory else None
            except ImportError:
                # 緊急時フォールバック：直接作成
                # TODO: DI - Infrastructure Adapter removed for DDD compliance
                # Use IErrorLogger interface via DI container instead
                # TODO: DI - Inject IErrorLogger via constructor
                error_logging_adapter = None  # 仮実装

        return ErrorHandlingOrchestrator(
            classification_service=ErrorClassificationService(),
            recovery_service=ErrorRecoveryService(),
            reporting_service=ErrorReportingService(),
            logging_adapter=error_logging_adapter,
        )
