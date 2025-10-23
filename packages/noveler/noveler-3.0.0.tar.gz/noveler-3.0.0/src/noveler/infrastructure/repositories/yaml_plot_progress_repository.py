"""YAMLベースのプロット進捗管理リポジトリ実装

ファイルI/OとYAML解析の実装をインフラ層に配置
"""

from pathlib import Path
from typing import Any

import yaml

from noveler.domain.repositories.plot_progress_repository import PlotProgressRepository
from noveler.infrastructure.adapters.path_service_adapter import create_path_service


class YamlPlotProgressRepository(PlotProgressRepository):
    """YAMLファイルベースのプロット進捗管理リポジトリ"""

    def read_file_content(self, file_path: Path) -> str:
        """ファイルの内容を読み込む

        Args:
            file_path: ファイルパス

        Returns:
            ファイルの内容

        Raises:
            FileNotFoundError: ファイルが存在しない場合
        """
        with Path(file_path).open(encoding="utf-8") as f:
            return f.read()

    def parse_yaml_content(self, content: str) -> dict[str, Any]:
        """YAML形式の文字列を解析する

        Args:
            content: YAML形式の文字列

        Returns:
            解析結果の辞書

        Raises:
            ValueError: YAML形式が不正な場合
        """
        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError as e:
            msg = f"Invalid YAML format: {e}"
            raise ValueError(msg) from e

    def file_exists(self, file_path: Path) -> bool:
        """ファイルの存在を確認する

        Args:
            file_path: ファイルパス

        Returns:
            ファイルが存在する場合True
        """
        return file_path.exists()

    def list_files(self, directory: Path, pattern: str) -> list[Path]:
        """ディレクトリ内のファイルを検索する

        Args:
            directory: 検索対象ディレクトリ
            pattern: ファイル名パターン

        Returns:
            マッチしたファイルのリスト
        """
        if not directory.exists():
            return []

        return list(directory.glob(pattern))

    def find_master_plot(self, project_id: str) -> dict[str, Any] | None:
        path_service = create_path_service()
        """マスタープロットを取得

        Args:
            project_id: プロジェクトID

        Returns:
            マスタープロット情報(存在しない場合はNone)
        """
        project_root = Path(project_id)
        path_service = create_path_service(project_root)
        master_plot_path = path_service.get_plot_dir() / "全体構成.yaml"

        if not self.file_exists(master_plot_path):
            return None

        try:
            content = self.read_file_content(master_plot_path)
            return self.parse_yaml_content(content)
        except Exception:
            return None

    def find_chapter_plots(self, project_id: str) -> list[dict[str, Any]]:
        """章別プロットを取得

        Args:
            project_id: プロジェクトID

        Returns:
            章別プロットのリスト
        """
        Path(project_id)
        path_service = create_path_service()
        chapter_plot_dir = path_service.get_plot_dir() / "章別プロット"

        if not chapter_plot_dir.exists():
            return []

        plots = []
        for file_path in self.list_files(chapter_plot_dir, "第*章.yaml"):
            try:
                content = self.read_file_content(file_path)
                plot_data: dict[str, Any] = self.parse_yaml_content(content)
                plot_data["_file_path"] = str(file_path)
                plots.append(plot_data)
            except Exception:
                continue

        return plots

    def find_episode_plots(self, project_id: str) -> list[dict[str, Any]]:
        """話別プロットを取得

        Args:
            project_id: プロジェクトID

        Returns:
            話別プロットのリスト
        """
        Path(project_id)
        path_service = create_path_service()
        episode_plot_dir = path_service.get_plot_dir() / "話別プロット"

        if not episode_plot_dir.exists():
            return []

        plots = []
        for file_path in self.list_files(episode_plot_dir, "第*話.yaml"):
            try:
                content = self.read_file_content(file_path)
                plot_data: dict[str, Any] = self.parse_yaml_content(content)
                plot_data["_file_path"] = str(file_path)
                plots.append(plot_data)
            except Exception:
                continue

        return plots

    def find_incomplete_chapters(self, project_id: str) -> list[int]:
        """未完成の章番号を取得

        Args:
            project_id: プロジェクトID

        Returns:
            未完成章番号のリスト
        """
        chapter_plots = self.find_chapter_plots(project_id)
        incomplete = []

        for plot in chapter_plots:
            chapter_num = plot.get("metadata", {}).get("chapter_number", 0)
            if chapter_num and self.calculate_file_completion(plot) < 100:
                incomplete.append(chapter_num)

        return sorted(incomplete)

    def calculate_file_completion(self, file_content: dict[str, Any]) -> int:
        """ファイル完成度を計算(0-100)

        Args:
            file_content: ファイル内容

        Returns:
            完成度(0-100)
        """
        if not file_content:
            return 0

        # 必須フィールドの存在確認
        required_fields = ["metadata", "episodes"]
        completed_fields = sum(1 for field in required_fields if field in file_content)

        # エピソードの完成度
        episodes = file_content.get("episodes", [])
        if not episodes:
            return int((completed_fields / len(required_fields)) * 50)

        # 各エピソードの必須フィールド
        episode_completion = 0
        for episode in episodes:
            if isinstance(episode, dict):
                episode_fields = ["number", "title", "summary"]
                episode_completion += sum(1 for field in episode_fields if field in episode)

        if episodes:
            episode_completion = (episode_completion / (len(episodes) * 3)) * 50

        return int((completed_fields / len(required_fields)) * 50 + episode_completion)

    def get_project_root(self, project_id: str) -> str | None:
        """プロジェクトルートパスを取得

        Args:
            project_id: プロジェクトID

        Returns:
            プロジェクトルートパス(存在しない場合はNone)
        """
        project_root = Path(project_id)
        if project_root.exists() and project_root.is_dir():
            return str(project_root.absolute())
        return None
