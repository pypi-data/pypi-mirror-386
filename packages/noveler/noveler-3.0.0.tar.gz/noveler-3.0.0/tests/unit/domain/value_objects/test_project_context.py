#!/usr/bin/env python3
"""ProjectContextの値オブジェクトテスト
TDD RED段階:値オブジェクトの不変条件とビジネスルールをテスト


仕様書: SPEC-DOMAIN-VALUE-OBJECTS
"""

import pytest

from noveler.domain.value_objects.project_context import ProjectContext

pytestmark = pytest.mark.vo_smoke



class TestProjectContextCreation:
    """ProjectContext作成時のテスト"""

    def test_create_with_minimal_required_fields(self) -> None:
        """最小限必須フィールドでの作成"""
        # Act
        context = ProjectContext(project_name="テストプロジェクト", genre="ファンタジー")

        # Assert
        assert context.project_name == "テストプロジェクト"
        assert context.genre == "ファンタジー"
        assert context.protagonist_name is None
        assert context.structure_type == "三幕構成"  # デフォルト値

    def test_create_with_all_fields(self) -> None:
        """全フィールド指定での作成"""
        # Arrange
        characters = [{"name": "勇者", "role": "主人公"}, {"name": "魔王", "role": "アンタゴニスト"}]

        # Act
        context = ProjectContext(
            project_name="完全版プロジェクト",
            genre="ファンタジー",
            protagonist_name="勇者",
            setting_world="異世界",
            theme="成長物語",
            structure_type="四幕構成",
            main_characters=characters,
            total_episodes=100,
            quality_threshold=85,
            target_audience="青年向け",
        )

        # Assert
        assert context.project_name == "完全版プロジェクト"
        assert context.protagonist_name == "勇者"
        assert context.total_episodes == 100
        assert len(context.main_characters) == 2

    def test_validation_empty_project_name_raises_error(self) -> None:
        """空のプロジェクト名でエラー"""
        # Act & Assert
        with pytest.raises(ValueError, match="プロジェクト名は必須です"):
            ProjectContext(project_name="", genre="ファンタジー")

    def test_validation_empty_genre_raises_error(self) -> None:
        """空のジャンルでエラー"""
        # Act & Assert
        with pytest.raises(ValueError, match="ジャンルは必須です"):
            ProjectContext(project_name="テスト", genre="")

    def test_validation_invalid_quality_threshold_raises_error(self) -> None:
        """無効な品質閾値でエラー"""
        # Act & Assert
        with pytest.raises(ValueError, match="品質閾値は0-100の範囲で指定してください"):
            ProjectContext(project_name="テスト", genre="ファンタジー", quality_threshold=150)

    def test_validation_negative_total_episodes_raises_error(self) -> None:
        """負の総話数でエラー"""
        # Act & Assert
        with pytest.raises(ValueError, match="総話数は正の整数で指定してください"):
            ProjectContext(project_name="テスト", genre="ファンタジー", total_episodes=-10)


class TestProjectContextBusinessMethods:
    """ProjectContextのビジネスメソッドテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.characters = [
            {"name": "勇者リック", "role": "主人公"},
            {"name": "魔法使いエルフィ", "role": "ヒロイン"},
            {"name": "魔王ダーク", "role": "アンタゴニスト"},
            {"name": "賢者オールド", "role": "メンター"},
        ]

        self.context = ProjectContext(
            project_name="テストプロジェクト",
            genre="ファンタジー",
            protagonist_name="勇者リック",
            main_characters=self.characters,
            total_episodes=50,
        )

    def test_has_character_info_with_characters(self) -> None:
        """キャラクター情報ありの場合"""
        # Act & Assert
        assert self.context.has_character_info() is True

    def test_has_character_info_without_characters(self) -> None:
        """キャラクター情報なしの場合"""
        # Arrange
        empty_context = ProjectContext(project_name="空プロジェクト", genre="ファンタジー")

        # Act & Assert
        assert empty_context.has_character_info() is False

    def test_get_protagonist_info_by_name(self) -> None:
        """名前による主人公情報取得"""
        # Act
        protagonist = self.context.get_protagonist_info()

        # Assert
        assert protagonist is not None
        assert protagonist["name"] == "勇者リック"
        assert protagonist["role"] == "主人公"

    def test_get_protagonist_info_by_role(self) -> None:
        """ロールによる主人公情報取得"""
        # Arrange
        context = ProjectContext(
            project_name="テスト", genre="ファンタジー", main_characters=[{"name": "名無し", "role": "主人公"}]
        )

        # Act
        protagonist = context.get_protagonist_info()

        # Assert
        assert protagonist is not None
        assert protagonist["role"] == "主人公"

    def test_get_antagonist_info_success(self) -> None:
        """アンタゴニスト情報取得成功"""
        # Act
        antagonist = self.context.get_antagonist_info()

        # Assert
        assert antagonist is not None
        assert antagonist["name"] == "魔王ダーク"
        assert antagonist["role"] == "アンタゴニスト"

    def test_get_antagonist_info_not_found(self) -> None:
        """アンタゴニスト情報が見つからない場合"""
        # Arrange
        context = ProjectContext(
            project_name="テスト", genre="恋愛", main_characters=[{"name": "主人公", "role": "主人公"}]
        )

        # Act
        antagonist = context.get_antagonist_info()

        # Assert
        assert antagonist is None

    def test_get_supporting_characters(self) -> None:
        """サポートキャラクター取得"""
        # Act
        supporting = self.context.get_supporting_characters()

        # Assert
        assert len(supporting) == 2  # ヒロインとメンター
        names = [char["name"] for char in supporting]
        assert "魔法使いエルフィ" in names
        assert "賢者オールド" in names

    def test_get_genre_characteristics_fantasy(self) -> None:
        """ファンタジージャンル特性取得"""
        # Act
        characteristics = self.context.get_genre_characteristics()

        # Assert
        assert "typical_locations" in characteristics
        assert "魔王城" in characteristics["typical_locations"]
        assert "神秘的" in characteristics["atmosphere_patterns"]

    def test_get_genre_characteristics_romance(self) -> None:
        """恋愛ジャンル特性取得"""
        # Arrange
        romance_context = ProjectContext(project_name="恋愛小説", genre="恋愛")

        # Act
        characteristics = romance_context.get_genre_characteristics()

        # Assert
        assert "学校" in characteristics["typical_locations"]
        assert "甘い" in characteristics["atmosphere_patterns"]

    def test_get_genre_characteristics_unknown_genre(self) -> None:
        """未知ジャンルのデフォルト特性"""
        # Arrange
        unknown_context = ProjectContext(project_name="未知ジャンル", genre="超未来SF")

        # Act
        characteristics = unknown_context.get_genre_characteristics()

        # Assert
        assert characteristics["typical_locations"] == ["重要な場所"]
        assert characteristics["atmosphere_patterns"] == ["緊張感"]

    def test_get_climax_episode_estimate(self) -> None:
        """クライマックス話数推定"""
        # Act
        climax_episode = self.context.get_climax_episode_estimate()

        # Assert
        assert climax_episode == 42  # 50 * 0.85 = 42.5 → 42

    def test_get_climax_episode_estimate_no_total_episodes(self) -> None:
        """総話数未設定時のクライマックス推定"""
        # Arrange
        context = ProjectContext(project_name="テスト", genre="ファンタジー")

        # Act
        climax_episode = context.get_climax_episode_estimate()

        # Assert
        assert climax_episode is None


class TestProjectContextSerialization:
    """ProjectContextのシリアライゼーション"""

    def test_to_dict_complete_conversion(self) -> None:
        """完全な辞書変換"""
        # Arrange
        context = ProjectContext(
            project_name="シリアライズテスト",
            genre="ファンタジー",
            protagonist_name="主人公",
            main_characters=[{"name": "主人公", "role": "主人公"}],
            total_episodes=30,
        )

        # Act
        result = context.to_dict()

        # Assert
        assert result["project_name"] == "シリアライズテスト"
        assert result["genre"] == "ファンタジー"
        assert "protagonist_info" in result
        assert "genre_characteristics" in result
        assert result["climax_episode_estimate"] == 25  # 30 * 0.85

    def test_from_project_files_construction(self) -> None:
        """プロジェクトファイルからの構築"""
        # Arrange
        project_data = {
            "project_settings": {
                "title": "ファイルから構築",
                "genre": "ミステリー",
                "protagonist": "探偵",
                "quality_threshold": 90,
            },
            "character_settings": {
                "main_characters": [{"name": "探偵", "role": "主人公"}, {"name": "犯人", "role": "敵"}]
            },
            "plot_settings": {"total_episodes": 20, "structure_type": "三幕構成", "theme": "真実の追求"},
        }

        # Act
        context = ProjectContext.from_project_files(project_data)

        # Assert
        assert context.project_name == "ファイルから構築"
        assert context.genre == "ミステリー"
        assert context.protagonist_name == "探偵"
        assert context.total_episodes == 20
        assert len(context.main_characters) == 2

    def test_from_project_files_minimal_data(self) -> None:
        """最小限データからの構築"""
        # Arrange
        minimal_data = {"project_settings": {"title": "最小限", "genre": "その他"}}

        # Act
        context = ProjectContext.from_project_files(minimal_data)

        # Assert
        assert context.project_name == "最小限"
        assert context.genre == "その他"
        assert context.protagonist_name == ""
        assert len(context.main_characters) == 0

    def test_is_valid_with_valid_context(self) -> None:
        """有効なコンテキストの検証"""
        # Arrange
        context = ProjectContext(project_name="有効なプロジェクト", genre="ファンタジー")

        # Act & Assert
        assert context.is_valid() is True

    def test_is_valid_with_invalid_context(self) -> None:
        """無効なコンテキストの検証"""
        # このテストは実際の実装では__post_init__でエラーになるため、
        # モック等を使って無効な状態を作る必要がある場合がある
        # 現在の実装では、作成時に検証されるため、このケースは難しい
