"""YAML章別プロットリポジトリ実装

SPEC-PLOT-001: Claude Code連携プロット生成システム
"""

from pathlib import Path
from typing import Any

import yaml

from noveler.domain.entities.chapter_plot import ChapterPlot
from noveler.domain.repositories.chapter_plot_repository import (
    ChapterPlotNotFoundError,
    ChapterPlotRepository,
)
from noveler.domain.value_objects.chapter_number import ChapterNumber


class YamlChapterPlotRepository(ChapterPlotRepository):
    """YAML章別プロットリポジトリ実装

    YAMLファイルベースの章別プロット情報永続化を担当する。
    優先配置: {project_root}/20_プロット/章別プロット/chXX.yaml
    旧形式: {project_root}/20_プロット/章別プロット/第X章.yaml
    """

    def find_by_chapter_number(self, chapter_number: ChapterNumber) -> ChapterPlot:
        """章番号による章別プロット取得

        Args:
            chapter_number: 章番号

        Returns:
            ChapterPlot: 章別プロット情報

        Raises:
            ChapterPlotNotFoundError: 章別プロットが見つからない場合
        """
        file_path = self.get_chapter_plot_file_path(chapter_number)

        if not file_path.exists():
            msg = f"章別プロットファイルが見つかりません: {file_path}"
            raise ChapterPlotNotFoundError(msg)

        try:
            f_content = file_path.read_text(encoding="utf-8")
            yaml_data: dict[str, Any] = yaml.safe_load(f_content) or {}

            return self._parse_yaml_to_chapter_plot(yaml_data)

        except yaml.YAMLError as e:
            msg = f"章別プロットファイルの読み込みに失敗しました: {file_path}, エラー: {e}"
            raise ChapterPlotNotFoundError(
                msg
            ) from e
        except Exception as e:
            msg = f"章別プロットファイルの処理に失敗しました: {file_path}, エラー: {e}"
            raise ChapterPlotNotFoundError(msg) from e

    def find_by_episode_number(self, episode_number: int) -> ChapterPlot:
        """エピソード番号による章別プロット取得

        Args:
            episode_number: エピソード番号

        Returns:
            ChapterPlot: エピソードを含む章の章別プロット情報

        Raises:
            ChapterPlotNotFoundError: 該当する章別プロットが見つからない場合
        """
        # エピソード番号から章番号を推定(デフォルト: 1章あたり10エピソード)
        estimated_chapter_number = ChapterNumber.from_episode_number(episode_number)

        try:
            chapter_plot = self.find_by_chapter_number(estimated_chapter_number)

            # エピソードが実際にその章に含まれているかチェック
            if chapter_plot.contains_episode(episode_number):
                return chapter_plot

            # 含まれていない場合は他の章を検索
            return self._search_episode_in_all_chapters(episode_number)

        except ChapterPlotNotFoundError:
            # 推定章が見つからない場合は全章を検索
            return self._search_episode_in_all_chapters(episode_number)

    def exists(self, chapter_number: ChapterNumber) -> bool:
        """章別プロットの存在確認

        Args:
            chapter_number: 章番号

        Returns:
            bool: 存在する場合True
        """
        return self.get_chapter_plot_file_path(chapter_number).exists()

    def list_all(self) -> list[ChapterPlot]:
        """全ての章別プロット一覧取得

        Returns:
            list[ChapterPlot]: 章別プロットのリスト(章番号順)
        """
        chapter_plots = []
        plot_dir = self._get_chapter_plot_directory()

        # 章別プロットファイルを検索
        chapter_files = list(plot_dir.glob("ch*.yaml"))
        if not chapter_files:
            chapter_files = list(plot_dir.glob("第*章*.yaml"))

        for file_path in sorted(chapter_files):
            try:
                f_content = file_path.read_text(encoding="utf-8")
                yaml_data: dict[str, Any] = yaml.safe_load(f_content) or {}

                chapter_plot = self._parse_yaml_to_chapter_plot(yaml_data)
                chapter_plots.append(chapter_plot)

            except Exception:
                # 個別ファイルの読み込みエラーは無視して続行
                continue

        # 章番号順にソート
        return sorted(chapter_plots, key=lambda cp: cp.chapter_number.value)

    def get_chapter_plot_file_path(self, chapter_number: ChapterNumber) -> Path:
        """章別プロットファイルパスを取得

        Args:
            chapter_number: 章番号

        Returns:
            Path: 章別プロットファイルのパス
        """
        directory = self._get_chapter_plot_directory()
        primary = directory / f"ch{chapter_number.value:02d}.yaml"
        if primary.exists():
            return primary

        legacy_candidates = [
            directory / f"第{chapter_number.value}章.yaml",
            directory / f"第{chapter_number.value:02d}章.yaml",
        ]
        for candidate in legacy_candidates:
            if candidate.exists():
                return candidate

        # 新規作成時は新形式パスを返す
        return primary

    def _get_chapter_plot_directory(self) -> Path:
        """章別プロットディレクトリパスを取得

        Returns:
            Path: 章別プロットディレクトリパス
        """
        return self.project_root / "20_プロット" / "章別プロット"

    def _search_episode_in_all_chapters(self, episode_number: int) -> ChapterPlot:
        """全ての章からエピソードを検索

        Args:
            episode_number: エピソード番号

        Returns:
            ChapterPlot: エピソードを含む章別プロット

        Raises:
            ChapterPlotNotFoundError: エピソードを含む章が見つからない場合
        """
        all_chapters = self.list_all()

        for chapter_plot in all_chapters:
            if chapter_plot.contains_episode(episode_number):
                return chapter_plot

        msg = f"エピソード{episode_number}を含む章別プロットが見つかりません"
        raise ChapterPlotNotFoundError(msg)

    def _parse_yaml_to_chapter_plot(self, yaml_data: dict[str, Any]) -> ChapterPlot:
        """YAMLデータから章別プロットエンティティを作成

        Args:
            yaml_data: YAMLデータ

        Returns:
            ChapterPlot: 章別プロットエンティティ

        Raises:
            ChapterPlotNotFoundError: 必須フィールドが不足している場合
        """
        try:
            # 必須フィールドチェック
            required_fields = ["chapter_number", "title", "summary"]
            missing_fields = [field for field in required_fields if field not in yaml_data]

            if missing_fields:
                msg = f"必須フィールドが不足しています: {', '.join(missing_fields)}"
                raise ChapterPlotNotFoundError(msg)

            # 章番号作成
            chapter_number = ChapterNumber(yaml_data["chapter_number"])

            # オプショナルフィールドの取得
            key_events = yaml_data.get("key_events", [])
            episodes = yaml_data.get("episodes", [])

            # chapter_info から詳細情報を取得(旧形式との互換性対応)
            chapter_info = yaml_data.get("chapter_info", {})
            central_theme = chapter_info.get("central_theme", yaml_data.get("central_theme", ""))
            viewpoint_management = chapter_info.get("viewpoint_management", yaml_data.get("viewpoint_management", {}))

            return ChapterPlot(
                chapter_number=chapter_number,
                title=yaml_data["title"],
                summary=yaml_data["summary"],
                key_events=key_events,
                episodes=episodes,
                central_theme=central_theme,
                viewpoint_management=viewpoint_management,
            )

        except ValueError as e:
            msg = f"章別プロットデータの変換に失敗しました: {e}"
            raise ChapterPlotNotFoundError(msg) from e
        except Exception as e:
            msg = f"章別プロットの作成に失敗しました: {e}"
            raise ChapterPlotNotFoundError(msg) from e

    def set_project_root(self, project_root: Path) -> None:
        """プロジェクトルートパスの設定

        Args:
            project_root: プロジェクトルートパス
        """
        self.project_root = project_root
