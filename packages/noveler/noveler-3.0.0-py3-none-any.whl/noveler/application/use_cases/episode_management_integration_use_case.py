#!/usr/bin/env python3

"""Application.use_cases.episode_management_integration_use_case
Where: Application use case integrating episode management workflows.
What: Coordinates repositories and services to manage episode metadata, statuses, and exports.
Why: Keeps episode management operations consistent and reusable across callers.
"""

from __future__ import annotations



import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from noveler.domain.entities.episode import Episode, EpisodeStatus
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.episode_title import EpisodeTitle
from noveler.domain.value_objects.word_count import WordCount

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service import ILoggerService
    from noveler.domain.repositories.episode_repository import EpisodeRepository
    from noveler.domain.repositories.plot_repository import PlotRepository


class PlotInfo(Protocol):
    """プロット情報のプロトコル"""

    title: str
    summary: str | None
    keywords: list[str] | None
    scene_setting: str | None
    character_focus: list[str] | None
    target_words: int | None


@dataclass(frozen=True)
class FindNextUnwrittenEpisodeRequest:
    """未執筆エピソード検索要求"""

    project_id: str
    include_plot_info: bool = True


@dataclass
class FindNextUnwrittenEpisodeResponse:
    """未執筆エピソード検索応答"""

    success: bool
    episode_number: int | None = None
    episode_title: str | None = None
    plot_available: bool = False
    plot_summary: str | None = None
    message: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class CreateEpisodeFromPlotRequest:
    """プロットからエピソード作成要求"""

    project_id: str
    episode_number: int
    generate_initial_content: bool = False
    override_existing: bool = False


@dataclass
class CreateEpisodeFromPlotResponse:
    """プロットからエピソード作成応答"""

    success: bool
    episode_number: int | None = None
    episode_title: str | None = None
    created_file_path: Path | None = None
    initial_content_generated: bool = False
    project_statistics: dict[str, Any] | None = None
    existing_episode_title: str | None = None
    error_message: str | None = None


@dataclass
class EpisodeManagementIntegrationUseCase:
    """エピソード管理統合ユースケース

    B20準拠DIパターン
    レガシーEpisodeManagerの機能をDDDアーキテクチャで再実装。
    ドメインエンティティとリポジトリパターンを活用してビジネスロジックを整理。
    """

    episode_repository: "EpisodeRepository"
    plot_repository: "PlotRepository"
    logger_service: "ILoggerService | None" = None

    def __post_init__(self) -> None:
        if self.logger_service is None:
            from noveler.domain.interfaces.logger_service import NullLoggerService

            self.logger_service = NullLoggerService()

    def find_next_unwritten_episode(self, request: FindNextUnwrittenEpisodeRequest) -> FindNextUnwrittenEpisodeResponse:
        """未執筆の次のエピソードを検索

        ビジネスフロー:
        1. 既存エピソードの取得
        2. プロット情報の取得
        3. 未執筆エピソードの特定
        4. 次の執筆対象エピソードの決定
        """
        try:
            self.logger_service.info(f"未執筆エピソード検索開始: Project {request.project_id}")

            # 1. 既存エピソードの取得
            existing_episodes = self.episode_repository.find_all_by_project(request.project_id)
            existing_numbers = {ep.number.value for ep in existing_episodes}

            # 2. プロット情報の取得
            plot_episodes = self.plot_repository.find_all_episodes() if request.include_plot_info else []

            # 3. 未執筆エピソードの特定
            unwritten_episodes = []
            for plot_ep in plot_episodes:
                episode_num = plot_ep.episode_number
                plot_status = getattr(plot_ep, "status", "未執筆")

                # プロットが未執筆で、実際のエピソードも存在しない
                if plot_status == "未執筆" and episode_num not in existing_numbers:
                    unwritten_episodes.append(plot_ep)

            # 4. 次の執筆対象エピソードの決定
            if not unwritten_episodes:
                msg = "全てのエピソードが執筆済みです"
                self.logger_service.info(msg)
                return FindNextUnwrittenEpisodeResponse(success=True, message=msg)

            # 最も小さい番号の未執筆エピソードを選択
            next_episode = min(unwritten_episodes, key=lambda x: x.episode_number)

            self.logger_service.info(f"次の執筆対象エピソード発見: Episode {next_episode.episode_number}")
            return FindNextUnwrittenEpisodeResponse(
                success=True,
                episode_number=next_episode.episode_number,
                episode_title=getattr(next_episode, "title", ""),
                plot_available=True,
                plot_summary=getattr(next_episode, "summary", ""),
            )

        except Exception as e:
            error_msg = f"未執筆エピソード検索エラー: {e}"
            self.logger_service.exception(error_msg)
            return FindNextUnwrittenEpisodeResponse(success=False, error_message=error_msg)

    def create_episode_from_plot(self, request: CreateEpisodeFromPlotRequest) -> CreateEpisodeFromPlotResponse:
        """プロット情報からエピソードを作成

        ビジネスフロー:
        1. 重複チェック
        2. プロット情報の取得
        3. エピソードエンティティの作成
        4. 初期コンテンツ生成(オプション)
        5. エピソードの保存
        6. 統計情報の更新
        """
        try:
            self.logger_service.info(f"プロットからエピソード作成開始: Episode {request.episode_number}")

            # 1. 重複チェック
            if not request.override_existing:
                existing_episode = self.episode_repository.find_by_project_and_number(
                    request.project_id, request.episode_number
                )

                if existing_episode:
                    error_msg = f"エピソード{request.episode_number}は既に存在します"
                    self.logger_service.warning(error_msg)
                    return CreateEpisodeFromPlotResponse(
                        success=False,
                        error_message=error_msg,
                        existing_episode_title=existing_episode.title.value,
                    )

            # 2. プロット情報の取得
            plot_info = self.plot_repository.find_episode_plot(request.project_id, request.episode_number)
            if not plot_info:
                error_msg = f"エピソード{request.episode_number}のプロット情報が見つかりません"
                self.logger_service.error(error_msg)
                return CreateEpisodeFromPlotResponse(
                    success=False,
                    episode_number=request.episode_number,
                    error_message=error_msg,
                )

            # 3. エピソードエンティティの作成
            normalized_title = self._normalize_title(plot_info.title)
            target_words = getattr(plot_info, "target_words", 3000)

            episode = Episode(
                number=EpisodeNumber(request.episode_number),
                title=EpisodeTitle(normalized_title),
                content=self._generate_initial_content(plot_info) if request.generate_initial_content else "",
                target_words=WordCount(target_words),
                status=EpisodeStatus.DRAFT,
            )

            # 4. エピソードの保存
            self.episode_repository.save(episode, request.project_id)

            # 5. 統計情報の更新
            updated_statistics = self.episode_repository.get_statistics(request.project_id)

            self.logger_service.info(f"エピソード作成完了: Episode {request.episode_number}")
            # 5. 作成ファイルパスの提示（共通基盤に統一）
            try:
                from noveler.infrastructure.adapters.path_service_adapter import create_path_service
                created_path = create_path_service().get_manuscript_path(request.episode_number)
            except Exception:
                created_path = Path(f"第{request.episode_number:03d}話_{normalized_title}.md")

            return CreateEpisodeFromPlotResponse(
                success=True,
                episode_number=request.episode_number,
                episode_title=normalized_title,
                created_file_path=created_path,
                initial_content_generated=request.generate_initial_content,
                project_statistics=updated_statistics,
            )

        except Exception as e:
            error_msg = f"エピソード作成エラー: {e}"
            self.logger_service.exception(error_msg)
            return CreateEpisodeFromPlotResponse(
                success=False, episode_number=request.episode_number, error_message=error_msg
            )

    def _normalize_title(self, raw_title: str) -> str:
        """タイトルの正規化

        ファイル名に使用できない文字を除去し、適切な形式に変換。
        """
        if not raw_title:
            return "無題"

        # 不正な文字を除去
        normalized = re.sub(r'[<>"/\\|?*]', "", raw_title)

        # 特殊記号の処理
        normalized = normalized.replace("「", "").replace("」", "")
        normalized = normalized.replace("『", "").replace("』", "")
        normalized = normalized.replace("~", "-")

        # 連続する空白を単一の空白に
        normalized = re.sub(r"\s+", " ", normalized)

        # 前後の空白を除去
        normalized = normalized.strip()

        # 長すぎる場合は切り詰め
        if len(normalized) > 50:
            normalized = normalized[:47] + "..."

        return normalized or "無題"

    def _generate_initial_content(self, plot_info: PlotInfo) -> str:
        """初期コンテンツの生成

        プロット情報から基本的な構成案を生成。
        """
        title = getattr(plot_info, "title", "無題")
        summary = getattr(plot_info, "summary", "")
        keywords = getattr(plot_info, "keywords", [])
        scene_setting = getattr(plot_info, "scene_setting", "")
        character_focus = getattr(plot_info, "character_focus", [])

        content_parts = [
            f"# {title}\n",
            "",
            "## あらすじ",
            summary if summary else "(あらすじを記述してください)",
            "",
            "## 主要要素",
        ]

        if keywords and isinstance(keywords, list):
            content_parts.extend(["**キーワード**: " + ", ".join(f"*{k}*" for k in keywords), ""])

        if scene_setting:
            content_parts.extend([f"**舞台**: {scene_setting}", ""])

        if character_focus and isinstance(character_focus, list):
            content_parts.extend(["**登場人物**: " + ", ".join(f"*{c}*" for c in character_focus), ""])

        content_parts.extend(
            [
                "## 本文",
                "",
                "(ここから本文を執筆してください)",
                "",
            ]
        )

        return "\n".join(content_parts)

    @classmethod
    def create_with_di(cls) -> EpisodeManagementIntegrationUseCase:
        """DIを使用したインスタンス作成

        Phase 5統一DIパターン: Factory Method

        Returns:
            EpisodeManagementIntegrationUseCase: 設定済みインスタンス
        """
        try:
            # DIコンテナから依存関係解決
            from noveler.infrastructure.di.simple_di_container import get_container

            container = get_container()

            # Interface経由で依存関係取得
            from noveler.domain.interfaces.logger_service import ILoggerService
            from noveler.domain.repositories.episode_repository import EpisodeRepository
            from noveler.domain.repositories.plot_repository import PlotRepository

            return cls(
                episode_repository=container.get(EpisodeRepository),
                plot_repository=container.get(PlotRepository),
                logger_service=container.get(ILoggerService),
            )

        except Exception:
            # フォールバック: 直接インスタンス化
            from pathlib import Path

            from noveler.domain.interfaces.logger_service import NullLoggerService
            from noveler.infrastructure.repositories.simple_yaml_episode_repository import SimpleYamlEpisodeRepository
            from noveler.infrastructure.repositories.simple_yaml_plot_repository import SimpleYamlPlotRepository

            logger_service = NullLoggerService()
            data_path = Path.cwd() / "data"

            return cls(
                episode_repository=SimpleYamlEpisodeRepository(data_path),
                plot_repository=SimpleYamlPlotRepository(data_path),
                logger_service=logger_service,
            )


# Factory関数（便利メソッド）
def create_episode_management_integration_use_case() -> EpisodeManagementIntegrationUseCase:
    """エピソード管理統合ユースケースの簡単作成

    Phase 5統一パターン: Factory Function

    Returns:
        EpisodeManagementIntegrationUseCase: 設定済みインスタンス
    """
    return EpisodeManagementIntegrationUseCase.create_with_di()
