"""ファイルベースの固有名詞リポジトリ実装"""

from pathlib import Path
from typing import Any

import yaml

from noveler.domain.quality.repositories import ProperNounRepository


class FileProperNounRepository(ProperNounRepository):
    """ファイルシステムから固有名詞を読み込むリポジトリ実装"""

    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path

    def get_all_by_project(self, project_id: str) -> set[str]:
        """プロジェクトの全固有名詞を取得"""
        proper_nouns = set()

        # プロジェクトパスを構築
        project_path = self.base_path / project_id / "30_設定集"

        if not project_path.exists():
            return proper_nouns

        # YAMLファイルから固有名詞を抽出
        yaml_files = [
            "世界観.yaml",
            "キャラクター.yaml",
            "魔法システム.yaml",
            "用語集.yaml",
        ]

        for yaml_file in yaml_files:
            file_path = project_path / yaml_file
            if file_path.exists():
                try:
                    with Path(file_path).open(encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        if data:
                            self._extract_proper_nouns(data, proper_nouns)
                except Exception:
                    # エラーは無視して続行
                    continue

        return proper_nouns

    def exists(self, project_id: str, proper_noun: str) -> bool:
        """固有名詞が存在するか確認"""
        all_proper_nouns = self.get_all_by_project(project_id)
        return proper_noun in all_proper_nouns

    def _extract_proper_nouns(self, data: dict[str, Any], proper_nouns: set[str]) -> None:
        """辞書から固有名詞を再帰的に抽出"""
        if isinstance(data, dict):
            # キー名に基づいて固有名詞を抽出
            name_keys = ["名前", "name", "正式名称", "formal_name", "呼称", "title"]

            for key, value in data.items():
                if key in name_keys and isinstance(value, str):
                    proper_nouns.add(value)
                elif isinstance(value, dict | list):
                    self._extract_proper_nouns(value, proper_nouns)

        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict | list):
                    self._extract_proper_nouns(item, proper_nouns)
                elif isinstance(item, str) and len(item) > 1:
                    # リスト内の文字列も固有名詞として扱う可能性
                    # (ただし短すぎるものは除外)
                    proper_nouns.add(item)
