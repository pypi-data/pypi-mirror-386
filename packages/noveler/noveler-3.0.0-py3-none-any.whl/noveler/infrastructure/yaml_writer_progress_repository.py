"""執筆者進捗リポジトリ - インフラストラクチャ層

YAMLファイルから執筆者の進捗情報を取得する
"""

from pathlib import Path
from typing import Any

import yaml

from noveler.infrastructure.adapters.path_service_adapter import create_path_service


class YamlWriterProgressRepository:
    """YAML形式の管理ファイルから進捗情報を取得"""

    def __init__(self, project_root) -> None:
        self.project_root = Path(project_root)

    def get_completed_episodes_count(self, _project_id) -> int:
        """完了したエピソード数を取得

        Args:
            _project_id: プロジェクトID(実際には使用しない)

        Returns:
            完了エピソード数
        """
        # 話数管理.yamlから情報を取得


        path_service = create_path_service(self.project_root)
        management_file = path_service.get_episode_management_file()

        if not management_file.exists():
            # ファイルが存在しない場合は原稿ファイルを数える
            return self._count_manuscript_files()

        try:
            with Path(management_file).open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            # エピソード情報から完了状態をカウント
            episodes = data.get("episodes", [])
            completed_count = 0

            for episode in episodes:
                status = episode.get("status", "")
                if status in ["completed", "完了", "published", "公開済み"]:
                    completed_count += 1

            return completed_count

        except Exception:
            # エラーの場合は原稿ファイルを数える
            return self._count_manuscript_files()

    def get_average_quality_score(self, _project_id) -> float:
        """平均品質スコアを取得

        Args:
            project_id: プロジェクトID(実際には使用しない)

        Returns:
            平均品質スコア(0-100)
        """
        # 品質記録.yamlから情報を取得

        path_service = create_path_service(self.project_root)
        quality_file = path_service.get_quality_record_file()

        if not quality_file.exists():
            # ファイルが存在しない場合はデフォルト値
            return 70.0  # 中級者相当のデフォルト値

        try:
            with Path(quality_file).open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            # 品質記録から最新のスコアを収集
            scores = []

            # 新形式(統合ファイル)の処理
            if "quality_records" in data:
                for record in data["quality_records"]:
                    if "overall_score" in record:
                        scores.append(record["overall_score"])
                    elif "quality_score" in record:
                        scores.append(record["quality_score"]["total"])

            # 旧形式の処理
            elif isinstance(data, list):
                for record in data:
                    if "overall_score" in record:
                        scores.append(record["overall_score"])
                    elif "quality_score" in record:
                        scores.append(record["quality_score"]["total"])

            # 平均を計算
            if scores:
                return sum(scores) / len(scores)
            return 70.0  # デフォルト値

        except Exception:
            return 70.0  # エラー時のデフォルト値

    def _count_manuscript_files(self) -> int:
        """原稿ファイル数をカウント"""

        path_service = create_path_service(self.project_root)
        manuscript_dir = path_service.get_manuscript_dir()

        if not manuscript_dir.exists():
            return 0

        # .mdファイルをカウント
        count = 0
        for _file in manuscript_dir.glob("第*話_*.md"):
            count += 1

        return count

    def get_recent_scores(self, limit) -> list[dict[str, Any]]:
        """最近の品質スコアを取得

        Args:
            limit: 取得する件数

        Returns:
            スコア情報のリスト
        """

        path_service = create_path_service(self.project_root)
        quality_file = path_service.get_quality_record_file()

        if not quality_file.exists():
            return []

        try:
            with Path(quality_file).open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            records = []

            # データ形式に応じて処理
            if "quality_records" in data:
                source_records = data["quality_records"]
            elif isinstance(data, list):
                source_records = data
            else:
                return []

            # 最新のものから取得
            for record in source_records[-limit:]:
                records.append(
                    {
                        "episode": record.get("episode", "不明"),
                        "score": record.get("overall_score", 0),
                        "date": record.get("check_date", ""),
                    },
                )

            return records

        except Exception:
            return []
