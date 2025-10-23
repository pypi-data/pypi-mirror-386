"""プロジェクト検出サービス"""

from pathlib import Path

import yaml

from noveler.domain.exceptions import ProjectNotFoundError
from noveler.domain.value_objects.project_info import ProjectInfo


class ProjectDetectionService:
    """現在のディレクトリからプロジェクトを検出するサービス"""

    CONFIG_FILE_NAME = "プロジェクト設定.yaml"
    MAX_DEPTH = 5  # 最大5階層まで遡る

    def detect(self) -> ProjectInfo:
        """現在のディレクトリからプロジェクトを検出"""
        current_path = Path.cwd()

        # 現在のディレクトリから上に向かって検索
        for _ in range(self.MAX_DEPTH):
            config_path = current_path / self.CONFIG_FILE_NAME

            if config_path.exists() and config_path.is_file():
                # 設定ファイルが見つかった(root_pathは設定ファイルがあるディレクトリ)
                return self._load_project_info(config_path, current_path)

            # 親ディレクトリへ
            parent = current_path.parent
            if parent == current_path:
                # ルートディレクトリに到達
                break
            current_path = parent

        msg = f"{self.CONFIG_FILE_NAME}が見つかりません。小説プロジェクトのディレクトリで実行してください。"
        raise ProjectNotFoundError(msg)

    def _load_project_info(self, config_path: Path, root_path: Path) -> ProjectInfo:
        """設定ファイルからプロジェクト情報を読み込む"""
        try:
            with config_path.open(encoding="utf-8") as f:  # TODO: IPathServiceを使用するように修正
                config = yaml.safe_load(f)

            project_name = config.get("title", "")
            if not project_name:
                msg = "プロジェクト設定にtitleが設定されていません"
                raise ProjectNotFoundError(msg)

            return ProjectInfo(name=project_name, root_path=root_path, config_path=config_path)
        except yaml.YAMLError as e:
            msg = f"プロジェクト設定の読み込みに失敗しました: {e}"
            raise ProjectNotFoundError(msg) from e
        except Exception as e:
            msg = f"プロジェクト設定の読み込み中にエラーが発生しました: {e}"
            raise ProjectNotFoundError(msg) from e
