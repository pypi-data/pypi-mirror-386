"""YAMLベースのキャラクターリポジトリ実装

キャラクター設定情報をYAMLファイルから読み込む。
"""

from pathlib import Path
from typing import Any

import yaml

from noveler.domain.repositories.character_repository import CharacterRepository
from noveler.domain.value_objects.character_profile import CharacterProfile


class YamlCharacterRepository(CharacterRepository):
    """YAMLファイルベースのキャラクターリポジトリ"""

    def __init__(self, base_path: Path | str) -> None:
        """リポジトリを初期化

        Args:
            base_path: プロジェクトのベースパス
        """
        self.base_path = Path(base_path)
        self.character_file = self.base_path / "30_設定集" / "キャラクター.yaml"

    def find_all_by_project(self, _project_name: str) -> list[CharacterProfile]:
        """プロジェクトの全キャラクターを取得

        Args:
            _project_name: プロジェクト名

        Returns:
            キャラクタープロファイルのリスト
        """
        if not self.character_file.exists():
            return []

        try:
            with Path(self.character_file).open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "characters" not in data:
                return []

            characters = []
            for char_data in data["characters"]:
                profile = CharacterProfile(name=char_data["name"], attributes=char_data.get("attributes", {}))
                characters.append(profile)

            return characters

        except Exception:
            # エラーが発生した場合は空のリストを返す
            return []

    def find_by_name(self, _project_name: str, name: str) -> CharacterProfile | None:
        """名前でキャラクターを検索

        Args:
            project_name: プロジェクト名
            name: キャラクター名

        Returns:
            キャラクタープロファイル(見つからない場合はNone)
        """
        characters = self.find_all_by_project(_project_name)

        for character in characters:
            if character.name == name:
                return character

        return None

    def save(self, _project_name: str, character: CharacterProfile) -> None:
        """キャラクターを保存

        Args:
            project_name: プロジェクト名
            character: 保存するキャラクター
        """
        # 既存データを読み込む
        if self.character_file.exists():
            with Path(self.character_file).open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}
            self.character_file.parent.mkdir(parents=True, exist_ok=True)

        if "characters" not in data:
            data["characters"] = []

        # 既存のキャラクターを更新または新規追加
        char_data: dict[str, Any] = {"name": character.name, "attributes": character.attributes}

        # 同名のキャラクターがいる場合は更新
        for i, existing in enumerate(data["characters"]):
            if existing["name"] == character.name:
                data["characters"][i] = char_data
                break
        else:
            # 新規追加
            data["characters"].append(char_data)

        # ファイルに保存
        with Path(self.character_file).open("w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    def delete(self, _project_name: str, name: str) -> bool:
        """キャラクターを削除

        Args:
            project_name: プロジェクト名
            name: 削除するキャラクター名

        Returns:
            削除に成功した場合True
        """
        if not self.character_file.exists():
            return False

        try:
            with Path(self.character_file).open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "characters" not in data:
                return False

            # 指定された名前のキャラクターを削除
            original_count = len(data["characters"])
            data["characters"] = [char for char in data["characters"] if char["name"] != name]

            # 削除されたかチェック
            if len(data["characters"]) == original_count:
                return False

            # ファイルに保存
            with Path(self.character_file).open("w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

            return True

        except Exception:
            return False

    def find_by_attribute(self, project_name: str, attribute: str, value: object) -> list[CharacterProfile]:
        """特定の属性を持つキャラクターを検索

        Args:
            project_name: プロジェクト名
            attribute: 属性名
            value: 属性値

        Returns:
            条件に一致するキャラクターのリスト
        """
        all_characters = self.find_all_by_project(project_name)

        matching_characters = []
        for character in all_characters:
            if character.get_attribute(attribute) == value:
                matching_characters.append(character)

        return matching_characters

    def exists(self, project_name: str, name: str) -> bool:
        """キャラクターが存在するかチェック

        Args:
            project_name: プロジェクト名
            name: キャラクター名

        Returns:
            存在する場合True
        """
        return self.find_by_name(project_name, name) is not None
