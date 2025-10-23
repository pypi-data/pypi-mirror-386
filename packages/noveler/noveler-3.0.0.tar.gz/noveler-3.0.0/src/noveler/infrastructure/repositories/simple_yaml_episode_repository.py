"""シンプルなYAMLベースのエピソードリポジトリ実装"""

from pathlib import Path

import yaml

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


from noveler.infrastructure.adapters.path_service_adapter import create_path_service


class SimpleYamlEpisodeRepository:
    """CLIテスト用のシンプルなエピソードリポジトリ"""

    def __init__(self, project_root: Path | None) -> None:
        self.project_root = project_root

    def update_status(self, episode_file: Path, status: str) -> None:
        """エピソードのステータスを簡易更新"""
        # 話数管理.yamlファイルを更新
        if self.project_root:
            path_service = create_path_service(self.project_root)
            management_file = path_service.get_management_dir() / "話数管理.yaml"
        else:
            path_service = create_path_service(episode_file.parent.parent)
            management_file = path_service.get_management_dir() / "話数管理.yaml"

        if not management_file.exists():
            # ファイルがない場合は作成
            management_file.parent.mkdir(parents=True, exist_ok=True)
            data = {"episodes": {}}
        else:
            # YAMLファイルを読み込み
            with Path(management_file).open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        # エピソード番号を取得
        episode_name = episode_file.stem

        # エピソード情報を更新
        if "episodes" not in data:
            data["episodes"] = {}

        if episode_name not in data["episodes"]:
            data["episodes"][episode_name] = {}

        data["episodes"][episode_name]["status"] = status
        data["episodes"][episode_name]["updated_at"] = project_now().datetime.isoformat()

        # YAMLファイルに書き戻し
        with Path(management_file).open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
