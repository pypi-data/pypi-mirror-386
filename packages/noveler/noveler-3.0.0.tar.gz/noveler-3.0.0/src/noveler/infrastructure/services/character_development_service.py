"""Infrastructure.services.character_development_service
Where: Infrastructure service supporting character development workflows.
What: Integrates with repositories and utilities to update character data.
Why: Provides reusable infrastructure logic for character-related features.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

"""キャラクター開発管理サービス

全体構成.yamlからキャラクター開発情報を読み込み、機械処理可能な形で提供するサービス。
StandardizedなHero/Heroine構造に基づく統一的なアクセスを提供。
"""


import yaml

from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.infrastructure.adapters.path_service_adapter import create_path_service

if TYPE_CHECKING:
    from pathlib import Path


class CharacterInfo:
    """キャラクター情報を表すデータクラス"""

    def __init__(
        self,
        name: str,
        role: str,
        character_type: str,
        arc_summary: str,
        personality_growth: str,
        start_state: str | None = None,
        end_state: str | None = None,
        key_growth_points: list[dict] | None = None,
    ) -> None:
        self.name = name
        self.role = role
        self.character_type = character_type
        self.arc_summary = arc_summary
        self.personality_growth = personality_growth
        self.start_state = start_state
        self.end_state = end_state
        self.key_growth_points = key_growth_points or []
    def get_growth_at_episode(self, episode_number: int) -> dict | None:
        """指定エピソードでの成長情報を取得"""
        for growth_point in self.key_growth_points:
            if growth_point.get("episode") == episode_number:
                return growth_point
        return None

    def get_growth_points_by_range(self, start_episode: int, end_episode: int) -> list[dict]:
        """指定エピソード範囲内の成長ポイントを取得"""
        return [gp for gp in self.key_growth_points if start_episode <= gp.get("episode", 0) <= end_episode]

    def __str__(self) -> str:
        return f"{self.name} ({self.role}): {self.arc_summary}"


class CharacterDevelopmentService:
    """キャラクター開発管理サービス

    全体構成.yamlからキャラクター開発情報を読み込み、標準化された形式で提供する。
    Hero/Heroine/Supporting Charactersを統一的にアクセス可能。
    """

    def __init__(self, project_root: Path | None = None, logger_service=None, console_service=None) -> None:
        """サービス初期化

        Args:
            project_root: プロジェクトルートパス（省略時は自動検出）
        """
        self._path_service = create_path_service(project_root)
        self._characters_cache: dict[str, CharacterInfo] | None = None

        self.logger_service = logger_service
        self.console_service = console_service
    def get_hero_info(self) -> CharacterInfo | None:
        """主人公（Hero）の情報を取得

        Returns:
            CharacterInfo | None: 主人公情報（見つからない場合はNone）
        """
        characters = self._load_characters()
        return characters.get("hero")

    def get_heroine_info(self) -> CharacterInfo | None:
        """ヒロイン（Heroine）の情報を取得

        Returns:
            CharacterInfo | None: ヒロイン情報（見つからない場合はNone）
        """
        characters = self._load_characters()
        return characters.get("heroine")

    def get_character_by_name(self, character_name: str) -> CharacterInfo | None:
        """キャラクター名から情報を取得

        Args:
            character_name: キャラクター名

        Returns:
            CharacterInfo | None: キャラクター情報（見つからない場合はNone）
        """
        characters = self._load_characters()

        for character in characters.values():
            if character.name == character_name:
                return character

        return None

    def get_character_by_type(self, character_type: str) -> CharacterInfo | None:
        """キャラクタータイプから情報を取得

        Args:
            character_type: キャラクタータイプ (hero, heroine, mentor, antagonist)

        Returns:
            CharacterInfo | None: キャラクター情報（見つからない場合はNone）
        """
        characters = self._load_characters()

        for character in characters.values():
            if character.character_type == character_type:
                return character

        return None

    def get_all_main_characters(self) -> dict[str, CharacterInfo]:
        """メインキャラクター全員の情報を取得

        Returns:
            dict[str, CharacterInfo]: メインキャラクター情報辞書（key: role）
        """
        return self._load_characters()

    def get_character_growth_at_episode(self, character_name: str, episode_number: EpisodeNumber) -> dict | None:
        """指定キャラクターの指定エピソードでの成長情報を取得

        Args:
            character_name: キャラクター名
            episode_number: エピソード番号

        Returns:
            dict | None: 成長情報（見つからない場合はNone）
        """
        character = self.get_character_by_name(character_name)
        if not character:
            return None

        return character.get_growth_at_episode(episode_number.value)

    def _load_characters(self) -> dict[str, CharacterInfo]:
        """キャラクター情報を全体構成.yamlから読み込み

        Returns:
            dict[str, CharacterInfo]: キャラクター情報辞書
        """
        if self._characters_cache is not None:
            return self._characters_cache

        try:
            overall_config_path = self._path_service.get_plot_dir() / "全体構成.yaml"

            if not overall_config_path.exists():
                self.console_service.print(f"全体構成.yamlが見つかりません: {overall_config_path}")
                return self._fallback_character_structure()

            with open(overall_config_path, encoding="utf-8") as f:
                config_data: dict[str, Any] = yaml.safe_load(f)

            character_development = config_data.get("character_development", {})

            # 新形式（推奨）: character_development.main_characters から読み込み
            main_characters = character_development.get("main_characters", {})
            if main_characters:
                characters = {}

                for role, character_data in main_characters.items():
                    character_info = CharacterInfo(
                        name=character_data.get("name", ""),
                        role=character_data.get("role", role),
                        character_type=character_data.get("character_type", role),
                        arc_summary=character_data.get("arc_summary", ""),
                        personality_growth=character_data.get("personality_growth", ""),
                        start_state=character_data.get("start_state"),
                        end_state=character_data.get("end_state"),
                        key_growth_points=character_data.get("key_growth_points", []),
                    )

                    characters[role] = character_info

                self._characters_cache = characters
                return characters

            # 旧形式からの変換（後方互換性）
            legacy_arcs = character_development.get("legacy_character_arcs", {})
            if legacy_arcs:
                characters = {}
                for role, character_data in legacy_arcs.items():
                    character_info = CharacterInfo(
                        name=character_data.get("name", ""),
                        role=role,
                        character_type=role,
                        arc_summary=character_data.get("arc_summary", ""),
                        personality_growth="",
                    )

                    characters[role] = character_info

                self._characters_cache = characters
                return characters

            return self._fallback_character_structure()

        except Exception as e:
            self.console_service.print(f"キャラクター開発情報の読み込みエラー: {e}")
            return self._fallback_character_structure()

    def _fallback_character_structure(self) -> dict[str, CharacterInfo]:
        """フォールバックキャラクター構造（全体構成.yamlが読み込めない場合）

        Returns:
            dict[str, CharacterInfo]: デフォルトキャラクター構造
        """
        fallback_characters = {
            "hero": CharacterInfo(
                name="虫取直人",
                role="主人公",
                character_type="hero",
                arc_summary="ひねくれ者の防御→本音の露出→素直な信頼→真の絆",
                personality_growth="皮肉屋・自己防衛的→徐々に心を開く→素直になれる瞬間増加→信頼できる仲間",
            ),
            "heroine": CharacterInfo(
                name="確野あすか",
                role="ヒロイン",
                character_type="heroine",
                arc_summary="内気な献身→静かな強さ→揺るがない支え→最強のパートナー",
                personality_growth="表面は大人しいが芯は強い→自分の価値に気づく→積極的にサポート→対等な相棒",
            ),
        }

        self._characters_cache = fallback_characters
        return fallback_characters

    def clear_cache(self) -> None:
        """キャッシュをクリア（設定ファイル更新時用）"""
        self._characters_cache = None


# グローバルインスタンス
_character_development_service: CharacterDevelopmentService | None = None


def get_character_development_service(project_root: Path | None = None) -> CharacterDevelopmentService:
    """キャラクター開発サービスのインスタンスを取得

    Args:
        project_root: プロジェクトルートパス（省略時は自動検出）

    Returns:
        CharacterDevelopmentService: キャラクター開発サービス
    """
    global _character_development_service

    if _character_development_service is None or (
        project_root and _character_development_service._path_service.project_root != project_root
    ):
        _character_development_service = CharacterDevelopmentService(project_root)

    return _character_development_service
