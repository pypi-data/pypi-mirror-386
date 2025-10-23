"""執筆完了ユースケース
アプリケーション層:ビジネスフローの調整
"""

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.entities.episode_completion import CompletedEpisode
from noveler.domain.exceptions import EpisodeCompletionError
from noveler.domain.interfaces.console_service_protocol import IConsoleService

# 実行時に使用するため、TYPE_CHECKINGブロック外でインポート
from noveler.domain.interfaces.logger_service_protocol import ILoggerService
from noveler.domain.interfaces.path_service_protocol import IPathService
from noveler.domain.repositories.episode_completion_repository import (
    ChapterPlotRepository,
    CharacterGrowthRepository,
    CompletionTransactionManager,
    EpisodeManagementRepository,
    ForeshadowingRepository,
    ImportantSceneRepository,
    RevisionHistoryRepository,
)
from noveler.domain.value_objects.episode_completion import (
    CharacterGrowthEvent,
    EpisodeCompletionEvent,
)
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.infrastructure.unit_of_work import IUnitOfWork

JST = ProjectTimezone.jst().timezone


class TransactionProtocol(Protocol):
    """トランザクションプロトコル"""

    def update_episode_status(self, episode_number: int, status: str) -> None:
        """エピソードステータスを更新"""
        ...

    def plant_foreshadowing(self, foreshadowing_id: str, episode_number: int) -> None:
        """伏線を設置"""
        ...

    def resolve_foreshadowing(self, foreshadowing_id: str, episode_number: int) -> None:
        """伏線を解決"""
        ...

    def add_character_growth(self, character_name: str, episode_number: int) -> None:
        """キャラクター成長を追加"""
        ...

    def add_important_scene(self, episode_number: int, scene_data: dict[str, Any]) -> None:
        """重要シーンを追加"""
        ...

    def add_revision_history(self, episode_number: int, data: dict[str, Any]) -> None:
        """改訂履歴を追加"""
        ...

    def update_chapter_plot(self, chapter: str, episode_number: int) -> None:
        """章別プロットを更新"""
        ...


@dataclass(frozen=True)
class CompleteEpisodeDependencies:
    """執筆完了ユースケースの依存性設定"""

    episode_management_repository: EpisodeManagementRepository
    foreshadowing_repository: ForeshadowingRepository
    character_growth_repository: CharacterGrowthRepository
    important_scene_repository: ImportantSceneRepository
    revision_history_repository: RevisionHistoryRepository
    chapter_plot_repository: ChapterPlotRepository
    transaction_manager: CompletionTransactionManager


@dataclass(frozen=True)
class CompleteEpisodeRequest:
    """執筆完了リクエスト"""

    project_name: str
    project_path: Path
    episode_number: int
    quality_score: Decimal
    plot_data: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.project_name or not self.project_name.strip():
            msg = "Project name cannot be empty"
            raise ValueError(msg)
        if self.episode_number <= 0:
            msg = "Episode number must be positive"
            raise ValueError(msg)


@dataclass
class CompleteEpisodeResponse:
    """執筆完了レスポンス"""

    success: bool
    error_message: str | None = None
    updated_files: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def success(
        cls, updated_files: list[str], summary: dict[str, Any], warnings: list[str] | None = None
    ) -> "CompleteEpisodeResponse":
        """成功レスポンス作成"""
        return cls(
            success=True, error_message=None, updated_files=updated_files, summary=summary, warnings=warnings or []
        )

    @classmethod
    def failure(cls, error_message: str) -> "CompleteEpisodeResponse":
        """失敗レスポンス作成"""
        return cls(success=False, error_message=error_message, updated_files=[], summary={})


class CompleteEpisodeUseCase(AbstractUseCase["CompleteEpisodeRequest", "CompleteEpisodeResponse"]):
    """執筆完了ユースケース

    責務:
    1. 執筆完了イベントの処理
    2. 管理ファイルの統合的な更新
    3. トランザクション制御
    4. サマリー情報の生成
    """

    def __init__(self,
        dependencies: Any = None,  # 依存性オブジェクト（第一引数）
        logger_service: ILoggerService | None = None,
        unit_of_work: IUnitOfWork | None = None,
        console_service: IConsoleService | None = None,
        path_service: IPathService | None = None,
        **kwargs) -> None:
        """コンストラクタ。

        依存性注入により各リポジトリとトランザクションマネージャーを設定する。

        Args:
            logger_service: ロガーサービス（DI注入）
            unit_of_work: 作業単位（DI注入）
            console_service: コンソールサービス（DI注入）
            path_service: パスサービス（DI注入）
            dependencies: 完了処理に必要な依存性をまとめたオブジェクト
        """
        # 基底クラス初期化（共通サービス）
        super().__init__(console_service=console_service, path_service=path_service, **kwargs)
        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work

        # 依存性の初期化（Noneチェックでエラー防止）
        if dependencies:
            self._episode_repo = getattr(dependencies, "episode_management_repository", None)
            self._foreshadowing_repo = getattr(dependencies, "foreshadowing_repository", None)
            self._growth_repo = getattr(dependencies, "character_growth_repository", None)
            self._scene_repo = getattr(dependencies, "important_scene_repository", None)
            self._history_repo = getattr(dependencies, "revision_history_repository", None)
            self._chapter_plot_repo = getattr(dependencies, "chapter_plot_repository", None)
            self._transaction_manager = getattr(dependencies, "transaction_manager", None)
        else:
            # デフォルト値を設定（Noneでランタイムエラーを防止）
            self._episode_repo = None
            self._foreshadowing_repo = None
            self._growth_repo = None
            self._scene_repo = None
            self._history_repo = None
            self._chapter_plot_repo = None
            self._transaction_manager = None

    def execute(self, request: CompleteEpisodeRequest) -> CompleteEpisodeResponse:
        """執筆完了処理の実行"""
        try:
            completion_event = self._create_completion_event(request)

            completed_episode = CompletedEpisode.create_from_event(completion_event)

            if request.plot_data:
                completed_episode.extract_from_plot_data()

            updated_files = self._update_all_records_transactionally(completed_episode, request)

            summary = self._generate_summary(completed_episode, request)

            warnings = completed_episode.get_warnings()

            return CompleteEpisodeResponse.success(updated_files=updated_files, summary=summary, warnings=warnings)

        except Exception as e:
            return CompleteEpisodeResponse.failure(str(e))

    def _create_completion_event(self, request: CompleteEpisodeRequest) -> EpisodeCompletionEvent:
        """完了イベントを作成"""
        word_count = self._calculate_word_count(request.project_path, request.episode_number)

        return EpisodeCompletionEvent(
            episode_number=request.episode_number,
            completed_at=project_now().datetime,
            quality_score=request.quality_score,
            word_count=word_count,
            plot_data=request.plot_data,
        )

    def _calculate_word_count(self, project_path: Path, episode_number: int) -> int:
        """原稿の文字数を計算（PathService優先）"""
        try:
            path_service = self.get_path_service(project_path)
            manuscript_file = path_service.get_manuscript_path(episode_number)
            if not manuscript_file.exists():
                return 0
            content = manuscript_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    content = parts[2]
            return len(content.strip())
        except Exception as e:
            self.logger.warning("文字数カウント中にエラー: %s", e)
            return 0

    def _update_all_records_transactionally(
        self, completed_episode: CompletedEpisode, request: CompleteEpisodeRequest
    ) -> list[str]:
        """トランザクション内での全記録更新(リファクタリング済み:複雑度11→5に削減)"""
        transaction = None
        try:
            transaction = self._transaction_manager.begin_transaction()
            with transaction:
                updated_files = self._execute_all_updates(transaction, completed_episode, request)
                transaction.commit()
                return list(set(updated_files))  # 重複を除去

        except Exception as e:
            if transaction:
                transaction.rollback()
            msg = f"Transaction failed: {e!s}"
            raise EpisodeCompletionError(request.episode_number, msg) from e

    def _execute_all_updates(
        self, transaction: TransactionProtocol, completed_episode: CompletedEpisode, request: CompleteEpisodeRequest
    ) -> list[str]:
        """全ての更新処理を実行"""
        updated_files = []

        updated_files.extend(self._update_episode_status(transaction, completed_episode))
        updated_files.extend(self._update_foreshadowing_records(transaction, completed_episode))
        updated_files.extend(self._update_character_growth_records(transaction, completed_episode))
        updated_files.extend(self._update_important_scenes(transaction, completed_episode))
        updated_files.extend(self._update_revision_history(transaction, completed_episode))
        updated_files.extend(self._update_chapter_plot(transaction, completed_episode, request))

        return updated_files

    def _update_episode_status(
        self, transaction: TransactionProtocol, completed_episode: CompletedEpisode
    ) -> list[str]:
        """話数管理の更新"""
        transaction.update_episode_status(
            episode_number=completed_episode.episode_number,
            status="completed",
            metadata={
                "quality_score": completed_episode.quality_score,
                "word_count": completed_episode.word_count,
                "completed_at": completed_episode.completed_at.isoformat(),
            },
        )

        return ["話数管理.yaml"]

    def _update_foreshadowing_records(
        self, transaction: TransactionProtocol, completed_episode: CompletedEpisode
    ) -> list[str]:
        """伏線管理の更新"""
        if not completed_episode.foreshadowing_records:
            return []

        for foreshadowing in completed_episode.foreshadowing_records:
            if foreshadowing.planted_episode == completed_episode.episode_number:
                transaction.plant_foreshadowing(foreshadowing.foreshadowing_id, completed_episode.episode_number)

            if foreshadowing.resolved_episode == completed_episode.episode_number:
                transaction.resolve_foreshadowing(foreshadowing.foreshadowing_id, completed_episode.episode_number)

        return ["伏線管理.yaml"]

    def _update_character_growth_records(
        self, transaction: TransactionProtocol, completed_episode: CompletedEpisode
    ) -> list[str]:
        """キャラクター成長記録の更新"""
        if not completed_episode.character_growth_records:
            return []

        for growth in completed_episode.character_growth_records:
            event = CharacterGrowthEvent(
                character_name=growth.character_name,
                growth_type=growth.growth_type,
                description=growth.description,
                importance=growth.importance,
                auto_detected=growth.auto_detected,
            )

            transaction.add_character_growth(growth.character_name, completed_episode.episode_number, event)

        return ["キャラ成長.yaml"]

    def _update_important_scenes(
        self, transaction: TransactionProtocol, completed_episode: CompletedEpisode
    ) -> list[str]:
        """重要シーンの更新"""
        if not completed_episode.important_scenes:
            return []

        for scene in completed_episode.important_scenes:
            scene_data: dict[str, Any] = {
                "scene_id": scene.scene_id if hasattr(scene, "scene_id") else "unknown",
                "type": scene.scene_type if hasattr(scene, "scene_type") else "unknown",
                "data": scene.to_dict() if hasattr(scene, "to_dict") else {},
            }
            transaction.add_important_scene(completed_episode.episode_number, scene_data)

        return ["重要シーン.yaml"]

    def _update_revision_history(
        self, transaction: TransactionProtocol, completed_episode: CompletedEpisode
    ) -> list[str]:
        """改訂履歴の更新"""
        transaction.add_revision_history(
            completed_episode.episode_number,
            {
                "event": "episode_completed",
                "quality_score": completed_episode.quality_score,
                "word_count": completed_episode.word_count,
                "timestamp": project_now().datetime.isoformat(),
            },
        )

        return ["改訂履歴.yaml"]

    def _update_chapter_plot(
        self, transaction: TransactionProtocol, completed_episode: CompletedEpisode, request: CompleteEpisodeRequest
    ) -> list[str]:
        """章別プロットの更新"""
        chapter = self._determine_chapter(completed_episode.episode_number)
        plot_updates = self._create_plot_updates(completed_episode, request)
        transaction.update_chapter_plot(chapter, completed_episode.episode_number, plot_updates)
        return [f"章別プロット/{chapter}.yaml"]

    def _generate_summary(
        self, completed_episode: CompletedEpisode, _request: CompleteEpisodeRequest
    ) -> dict[str, Any]:
        """サマリー情報を生成"""
        return {
            "episode_number": completed_episode.episode_number,
            "quality_score": float(completed_episode.quality_score),
            "word_count": completed_episode.word_count,
            "character_growth_count": len(completed_episode.character_growth_records),
            "important_scenes_count": len(completed_episode.important_scenes),
            "foreshadowing_planted": sum(
                1
                for f in completed_episode.foreshadowing_records
                if f.planted_episode == completed_episode.episode_number
            ),
            "foreshadowing_resolved": sum(
                1
                for f in completed_episode.foreshadowing_records
                if f.resolved_episode == completed_episode.episode_number
            ),
            "completed_at": completed_episode.completed_at.isoformat(),
        }

    def _determine_chapter(self, episode_number: int) -> str:
        """エピソード番号から章を判定"""
        chapter_num = ((episode_number - 1) // 10) + 1
        return f"chapter{chapter_num:02d}"

    def _create_plot_updates(
        self, completed_episode: CompletedEpisode, _request: CompleteEpisodeRequest
    ) -> dict[str, Any]:
        """プロット更新データを作成"""
        return {
            "status": "執筆済み",
            "actual_implementation": {
                "word_count": completed_episode.word_count,
                "quality_score": float(completed_episode.quality_score),
                "character_growth_count": len(completed_episode.character_growth_records),
                "important_scenes_count": len(completed_episode.important_scenes),
                "completed_at": completed_episode.completed_at.isoformat(),
            },
            "next_episode_impact": {
                "new_foreshadowing": self._get_foreshadowing_ids(
                    completed_episode.foreshadowing_records, completed_episode.episode_number, "planted"
                ),
                "resolved_foreshadowing": self._get_foreshadowing_ids(
                    completed_episode.foreshadowing_records, completed_episode.episode_number, "resolved"
                ),
            },
            "improvements": {
                "quality_warnings": completed_episode.get_warnings(),
                "timestamp": project_now().datetime.isoformat(),
            },
        }

    def _get_foreshadowing_ids(self, foreshadowing_records: list, episode_number: int, filter_type: str) -> list[str]:
        """伏線IDのリストを取得"""
        if filter_type == "planted":
            return [f.foreshadowing_id for f in foreshadowing_records if f.planted_episode == episode_number]
        if filter_type == "resolved":
            return [f.foreshadowing_id for f in foreshadowing_records if f.resolved_episode == episode_number]
        return []

    @classmethod
    def create_with_di(cls) -> "CompleteEpisodeUseCase":
        """DIを使用したインスタンス作成

        Phase 5統一DIパターン: Factory Method

        Returns:
            CompleteEpisodeUseCase: 設定済みインスタンス
        """
        try:
            # DIコンテナから依存関係解決
            from noveler.infrastructure.di.simple_di_container import get_container

            container = get_container()

            # Interface経由で依存関係取得
            from noveler.domain.interfaces.console_service_protocol import IConsoleService
            from noveler.domain.interfaces.path_service_protocol import IPathService
            from noveler.domain.repositories.episode_completion_repository import (
                ChapterPlotRepository,
                CharacterGrowthRepository,
                CompletionTransactionManager,
                EpisodeManagementRepository,
                ForeshadowingRepository,
                ImportantSceneRepository,
                RevisionHistoryRepository,
            )

            # 依存関係を構築
            dependencies = CompleteEpisodeDependencies(
                episode_management_repository=container.get(EpisodeManagementRepository),
                foreshadowing_repository=container.get(ForeshadowingRepository),
                character_growth_repository=container.get(CharacterGrowthRepository),
                important_scene_repository=container.get(ImportantSceneRepository),
                revision_history_repository=container.get(RevisionHistoryRepository),
                chapter_plot_repository=container.get(ChapterPlotRepository),
                transaction_manager=container.get(CompletionTransactionManager),
            )

            return cls(
                dependencies=dependencies,
                console_service=container.get(IConsoleService),
                path_service=container.get(IPathService),
            )

        except Exception:
            # フォールバック: 簡易実装
            from noveler.domain.interfaces.console_service_protocol import NullConsoleService
            from noveler.domain.interfaces.path_service_protocol import SimplePathService
            from noveler.infrastructure.repositories.simple_yaml_episode_completion_repository import (
                SimpleYamlCompletionTransactionManager,
            )

            # 簡易依存関係構築
            transaction_manager = SimpleYamlCompletionTransactionManager()
            dependencies = CompleteEpisodeDependencies(
                episode_management_repository=transaction_manager,
                foreshadowing_repository=transaction_manager,
                character_growth_repository=transaction_manager,
                important_scene_repository=transaction_manager,
                revision_history_repository=transaction_manager,
                chapter_plot_repository=transaction_manager,
                transaction_manager=transaction_manager,
            )

            return cls(
                dependencies=dependencies, console_service=NullConsoleService(), path_service=SimplePathService()
            )


# Factory関数（便利メソッド）
def create_complete_episode_use_case() -> CompleteEpisodeUseCase:
    """エピソード完了ユースケースの簡単作成

    Phase 5統一パターン: Factory Function

    Returns:
        CompleteEpisodeUseCase: 設定済みインスタンス
    """
    return CompleteEpisodeUseCase.create_with_di()
