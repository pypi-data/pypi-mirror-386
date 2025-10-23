"""
公開準備ユースケース

TDD GREEN フェーズ: テストを通すための最小限の実装
"""

import asyncio
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from noveler.application.use_cases.backup_use_case import BackupRequest, BackupType, BackupUseCase
from noveler.domain.entities.episode import Episode, EpisodeStatus
from noveler.domain.value_objects.episode_number import EpisodeNumber


class PublishFormat(Enum):
    """公開フォーマット"""

    NAROU = "narou"  # 小説家になろう
    KAKUYOMU = "kakuyomu"  # カクヨム
    PLAIN = "plain"  # プレーンテキスト


class PublishStatus(Enum):
    """公開準備ステータス"""

    READY = "ready"  # 公開準備完了
    NEEDS_REVIEW = "needs_review"  # レビューが必要
    NEEDS_IMPROVEMENT = "needs_improvement"  # 改善が必要
    ERROR = "error"  # エラー


@dataclass
class PreparationStep:
    """準備ステップ"""

    name: str
    status: str
    message: str


@dataclass
class PublishPreparationRequest:
    """公開準備リクエスト"""

    project_name: str
    episode_number: int | None = None
    format_type: PublishFormat = PublishFormat.NAROU
    include_quality_check: bool = True
    create_backup: bool = True
    quality_threshold: float = 70.0
    project_directory: str | None = None  # プロジェクトディレクトリを明示的に指定可能


@dataclass
class PublishPreparationResponse:
    """公開準備レスポンス"""

    status: PublishStatus
    episode_path: Path
    formatted_content: str
    preparation_steps: list[PreparationStep]
    quality_score: float | None = None
    backup_path: Path | None = None
    format_type: PublishFormat = PublishFormat.NAROU
    message: str = ""


class PublishPreparationUseCase:
    """公開準備ユースケース"""

    def __init__(
        self,
        backup_use_case: BackupUseCase,
        project_repository = None,
        episode_repository = None,
    ) -> None:
        self.project_repository = project_repository
        self.episode_repository = episode_repository
        self.backup_use_case = backup_use_case

    def execute(self, request: PublishPreparationRequest) -> PublishPreparationResponse:
        """公開準備を実行(リファクタリング済み:複雑度12→6に削減)"""
        preparation_steps = []

        # プロジェクトとエピソードの検証・取得
        project_dir_path = self._resolve_project_directory(request)
        episode = self._resolve_episode(request)
        episode_path = self._build_episode_path(project_dir_path, episode)

        # ステータスと品質の評価
        status, message, quality_score = self._evaluate_episode_status(request, episode, preparation_steps)

        # バックアップ処理
        backup_path = self._create_backup_if_requested(request, episode, preparation_steps)

        # フォーマット処理
        formatted_content = self._process_formatting(episode, request, preparation_steps)

        return PublishPreparationResponse(
            status=status,
            episode_path=episode_path,
            formatted_content=formatted_content,
            preparation_steps=preparation_steps,
            quality_score=quality_score,
            backup_path=backup_path,
            format_type=request.format_type,
            message=message,
        )

    def _resolve_project_directory(self, request: PublishPreparationRequest) -> Path:
        """プロジェクトディレクトリを解決"""
        if request.project_directory:
            project_dir_path = Path(request.project_directory)
        else:
            try:
                project_dir_path = self.project_repository.get_project_directory(request.project_name)
            except (FileNotFoundError, KeyError, AttributeError) as e:
                msg = f"プロジェクトが見つかりません: {request.project_name}"
                raise ValueError(msg) from e

        if not project_dir_path.exists():
            msg = f"プロジェクトディレクトリが見つかりません: {project_dir_path}"
            raise ValueError(msg)

        return project_dir_path

    def _resolve_episode(self, request: PublishPreparationRequest) -> Episode:
        """エピソードを解決"""
        if request.episode_number is None:
            episode = self.episode_repository.find_latest(request.project_name)
            if not episode:
                msg = "エピソードが見つかりません"
                raise ValueError(msg)
        else:
            episode = self.episode_repository.find_by_number(
                request.project_name, EpisodeNumber(request.episode_number)
            )

            if not episode:
                msg = f"エピソード {request.episode_number} が見つかりません"
                raise ValueError(msg)
        return episode

    def _build_episode_path(self, project_dir_path: Path, episode: Episode) -> Path:
        """エピソードパスを構築"""
        from noveler.presentation.shared.shared_utilities import get_common_path_service

        path_service = get_common_path_service(project_dir_path)
        return path_service.get_episode_file_path(episode.number.value, episode.title.value)

    def _evaluate_episode_status(
        self, request: PublishPreparationRequest, episode: Episode, preparation_steps: list[PreparationStep]
    ) -> tuple[PublishStatus, str, float | None]:
        """エピソードのステータスと品質を評価"""
        status = PublishStatus.READY
        message = "公開準備が完了しました"
        quality_score = None

        # 品質チェック
        if request.include_quality_check:
            quality_score = episode.quality_score or 0.0
            quality_check_step = PreparationStep(
                name="品質チェック", status="completed", message=f"品質スコア: {quality_score:.1f}点"
            )
            preparation_steps.append(quality_check_step)

            if quality_score < request.quality_threshold:
                status = PublishStatus.NEEDS_IMPROVEMENT
                message = f"品質スコアが基準値({request.quality_threshold}点)を下回っています"

        # エピソードステータスの確認
        if episode.status in [EpisodeStatus.DRAFT, EpisodeStatus.UNWRITTEN]:
            status = PublishStatus.NEEDS_IMPROVEMENT
            message = "エピソードが下書き状態です"
        elif episode.status == EpisodeStatus.IN_PROGRESS:
            status = PublishStatus.NEEDS_REVIEW
            message = "エピソードが執筆中です"

        return status, message, quality_score

    def _create_backup_if_requested(
        self, request: PublishPreparationRequest, episode: Episode, preparation_steps: list[PreparationStep]
    ) -> Path | None:
        """要求された場合にバックアップを作成"""
        if not (request.create_backup and self.backup_use_case):
            return None

        backup_request = BackupRequest(
            project_name=request.project_name,
            episode=str(episode.number.value),
            backup_type=BackupType.EPISODE.value,
        )

        backup_response = self.backup_use_case.execute(backup_request)
        if hasattr(backup_response, "__await__"):
            backup_response = asyncio.run(backup_response)

        backup_step = PreparationStep(name="バックアップ作成", status="completed", message="バックアップを作成しました")

        preparation_steps.append(backup_step)

        return backup_response.backup_path

    def _process_formatting(
        self, episode: Episode, request: PublishPreparationRequest, preparation_steps: list[PreparationStep]
    ) -> str:
        """フォーマット処理を実行"""
        formatted_content = self._format_content(episode.content, request.format_type)

        format_step = PreparationStep(
            name="フォーマット変換", status="completed", message=f"{request.format_type.value}形式に変換しました"
        )

        preparation_steps.append(format_step)

        return formatted_content

    def _format_content(self, content: str, format_type: PublishFormat) -> str:
        """コンテンツをフォーマット"""
        if format_type == PublishFormat.NAROU:
            return self._format_for_narou(content)
        if format_type == PublishFormat.KAKUYOMU:
            return self._format_for_kakuyomu(content)
        return content

    def _format_for_narou(self, content: str) -> str:
        """なろう形式にフォーマット"""
        # Markdownのヘッダーを除去
        formatted = re.sub(r"^#+\s+.*$", "", content, flags=re.MULTILINE)
        # 空行の調整
        formatted = re.sub(r"\n{3,}", "\n\n", formatted)

        # 前後の空白を除去
        return formatted.strip()

    def _format_for_kakuyomu(self, content: str) -> str:
        """カクヨム形式にフォーマット"""
        # カクヨム用のフォーマット処理
        # 現在はプレースホルダー実装
        return content
