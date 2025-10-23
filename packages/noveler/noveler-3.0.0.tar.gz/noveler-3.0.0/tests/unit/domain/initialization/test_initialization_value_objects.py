"""プロジェクト初期化ドメイン - 値オブジェクトのテスト

TDD準拠テスト:
    - Genre (Enum)
- WritingStyle (Enum)
- UpdateFrequency (Enum)
- InitializationConfig


仕様書: SPEC-UNIT-TEST
"""

import pytest

from noveler.domain.exceptions import DomainException
from noveler.domain.initialization.value_objects import (
    Genre,
    InitializationConfig,
    UpdateFrequency,
    WritingStyle,
)


class TestGenre:
    """Genreエンティティ(Enum)のテストクラス"""

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-GENRE_VALUES")
    def test_genre_values(self) -> None:
        """ジャンル値テスト"""
        assert Genre.FANTASY.value == "fantasy"
        assert Genre.ROMANCE.value == "romance"
        assert Genre.MYSTERY.value == "mystery"
        assert Genre.SLICE_OF_LIFE.value == "slice_of_life"
        assert Genre.SCIENCE_FICTION.value == "science_fiction"

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-GENRE_ENUM_COUNT")
    def test_genre_enum_count(self) -> None:
        """ジャンル数テスト"""
        assert len(Genre) == 5

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-GENRE_MEMBERSHIP")
    def test_genre_membership(self) -> None:
        """ジャンルメンバーシップテスト"""
        assert Genre.FANTASY in Genre
        assert Genre.ROMANCE in Genre
        assert Genre.MYSTERY in Genre
        assert Genre.SLICE_OF_LIFE in Genre
        assert Genre.SCIENCE_FICTION in Genre

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-GENRE_LEGACY_SUPPORT")
    def test_genre_legacy_members_excluded_from_iteration(self) -> None:
        """レガシージャンルが列挙に含まれないことを確認"""
        canonical_members = list(Genre)

        assert Genre.HORROR not in canonical_members
        assert Genre.LITERARY not in canonical_members
        assert Genre.OTHER not in canonical_members
        # SCIFI は SCIENCE_FICTION の別名として扱われる
        assert Genre.SCIENCE_FICTION in canonical_members


class TestWritingStyle:
    """WritingStyleエンティティ(Enum)のテストクラス"""

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-WRITING_STYLE_VALUES")
    def test_writing_style_values(self) -> None:
        """執筆スタイル値テスト"""
        assert WritingStyle.LIGHT.value == "light"
        assert WritingStyle.SERIOUS.value == "serious"
        assert WritingStyle.COMEDY.value == "comedy"
        assert WritingStyle.DARK.value == "dark"

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-WRITING_STYLE_ENUM_C")
    def test_writing_style_enum_count(self) -> None:
        """執筆スタイル数テスト"""
        assert len(WritingStyle) == 4

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-WRITING_STYLE_MEMBER")
    def test_writing_style_membership(self) -> None:
        """執筆スタイルメンバーシップテスト"""
        assert WritingStyle.LIGHT in WritingStyle
        assert WritingStyle.SERIOUS in WritingStyle
        assert WritingStyle.COMEDY in WritingStyle
        assert WritingStyle.DARK in WritingStyle


class TestUpdateFrequency:
    """UpdateFrequencyエンティティ(Enum)のテストクラス"""

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-UPDATE_FREQUENCY_VAL")
    def test_update_frequency_values(self) -> None:
        """更新頻度値テスト"""
        assert UpdateFrequency.DAILY.value == "daily"
        assert UpdateFrequency.WEEKLY.value == "weekly"
        assert UpdateFrequency.BIWEEKLY.value == "biweekly"
        assert UpdateFrequency.MONTHLY.value == "monthly"

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-UPDATE_FREQUENCY_ENU")
    def test_update_frequency_enum_count(self) -> None:
        """更新頻度数テスト"""
        assert len(UpdateFrequency) == 4

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-UPDATE_FREQUENCY_MEM")
    def test_update_frequency_membership(self) -> None:
        """更新頻度メンバーシップテスト"""
        assert UpdateFrequency.DAILY in UpdateFrequency
        assert UpdateFrequency.WEEKLY in UpdateFrequency
        assert UpdateFrequency.BIWEEKLY in UpdateFrequency
        assert UpdateFrequency.MONTHLY in UpdateFrequency


class TestInitializationConfig:
    """InitializationConfig値オブジェクトのテストクラス"""

    @pytest.fixture
    def valid_config(self) -> InitializationConfig:
        """有効な初期化設定"""
        return InitializationConfig(
            genre=Genre.FANTASY,
            writing_style=WritingStyle.LIGHT,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="転生したら最強の魔法使いだった件",
            author_name="テスト作家",
        )

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-INITIALIZATION_CONFI")
    def test_initialization_config_creation_valid(self, valid_config: InitializationConfig) -> None:
        """有効な値での初期化設定作成テスト"""
        assert valid_config.genre == Genre.FANTASY
        assert valid_config.writing_style == WritingStyle.LIGHT
        assert valid_config.update_frequency == UpdateFrequency.WEEKLY
        assert valid_config.project_name == "転生したら最強の魔法使いだった件"
        assert valid_config.author_name == "テスト作家"

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-INITIALIZATION_CONFI")
    def test_initialization_config_is_frozen(self, valid_config: InitializationConfig) -> None:
        """設定オブジェクトの不変性テスト"""
        with pytest.raises(AttributeError, match=".*"):
            valid_config.project_name = "新しい名前"  # type: ignore

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-VALIDATE_PROJECT_NAM")
    def test_validate_project_name_empty_error(self) -> None:
        """空のプロジェクト名エラーテスト"""
        with pytest.raises(DomainException, match="プロジェクト名は1文字以上50文字以下で入力してください"):
            InitializationConfig(
                genre=Genre.FANTASY,
                writing_style=WritingStyle.LIGHT,
                update_frequency=UpdateFrequency.WEEKLY,
                project_name="",
                author_name="テスト作家",
            )

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-VALIDATE_PROJECT_NAM")
    def test_validate_project_name_whitespace_only_error(self) -> None:
        """空白のみのプロジェクト名エラーテスト"""
        with pytest.raises(DomainException, match="プロジェクト名は1文字以上50文字以下で入力してください"):
            InitializationConfig(
                genre=Genre.FANTASY,
                writing_style=WritingStyle.LIGHT,
                update_frequency=UpdateFrequency.WEEKLY,
                project_name="   ",
                author_name="テスト作家",
            )

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-VALIDATE_PROJECT_NAM")
    def test_validate_project_name_too_long_error(self) -> None:
        """長すぎるプロジェクト名エラーテスト"""
        long_name = "あ" * 51  # 51文字
        with pytest.raises(DomainException, match="プロジェクト名は1文字以上50文字以下で入力してください"):
            InitializationConfig(
                genre=Genre.FANTASY,
                writing_style=WritingStyle.LIGHT,
                update_frequency=UpdateFrequency.WEEKLY,
                project_name=long_name,
                author_name="テスト作家",
            )

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-VALIDATE_PROJECT_NAM")
    def test_validate_project_name_max_length_valid(self) -> None:
        """最大文字数のプロジェクト名有効テスト"""
        max_name = "あ" * 50  # 50文字(上限)
        config = InitializationConfig(
            genre=Genre.FANTASY,
            writing_style=WritingStyle.LIGHT,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name=max_name,
            author_name="テスト作家",
        )

        assert config.project_name == max_name

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-VALIDATE_PROJECT_NAM")
    def test_validate_project_name_invalid_chars_error(self) -> None:
        """無効文字を含むプロジェクト名エラーテスト"""
        invalid_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]

        for char in invalid_chars:
            invalid_name = f"プロジェクト{char}名前"
            with pytest.raises(DomainException, match="プロジェクト名に使用できない文字が含まれています"):
                InitializationConfig(
                    genre=Genre.FANTASY,
                    writing_style=WritingStyle.LIGHT,
                    update_frequency=UpdateFrequency.WEEKLY,
                    project_name=invalid_name,
                    author_name="テスト作家",
                )

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-VALIDATE_PROJECT_NAM")
    def test_validate_project_name_valid_chars_success(self) -> None:
        """有効文字を含むプロジェクト名成功テスト"""
        valid_chars = ["ー", "!", "？", "(", ")", "【", "】", "〜", "・"]

        for char in valid_chars:
            valid_name = f"プロジェクト{char}名前"
            config = InitializationConfig(
                genre=Genre.FANTASY,
                writing_style=WritingStyle.LIGHT,
                update_frequency=UpdateFrequency.WEEKLY,
                project_name=valid_name,
                author_name="テスト作家",
            )

            assert char in config.project_name

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-VALIDATE_AUTHOR_NAME")
    def test_validate_author_name_empty_error(self) -> None:
        """空の作者名エラーテスト"""
        with pytest.raises(DomainException, match="作者名は必須です"):
            InitializationConfig(
                genre=Genre.FANTASY,
                writing_style=WritingStyle.LIGHT,
                update_frequency=UpdateFrequency.WEEKLY,
                project_name="テストプロジェクト",
                author_name="",
            )

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-VALIDATE_AUTHOR_NAME")
    def test_validate_author_name_whitespace_only_error(self) -> None:
        """空白のみの作者名エラーテスト"""
        with pytest.raises(DomainException, match="作者名は必須です"):
            InitializationConfig(
                genre=Genre.FANTASY,
                writing_style=WritingStyle.LIGHT,
                update_frequency=UpdateFrequency.WEEKLY,
                project_name="テストプロジェクト",
                author_name="   ",
            )

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-VALIDATE_AUTHOR_NAME")
    def test_validate_author_name_valid(self) -> None:
        """有効な作者名テスト"""
        valid_names = ["テスト作家", "Test Author", "作家123", "ペンネーム@site"]

        for name in valid_names:
            config = InitializationConfig(
                genre=Genre.FANTASY,
                writing_style=WritingStyle.LIGHT,
                update_frequency=UpdateFrequency.WEEKLY,
                project_name="テストプロジェクト",
                author_name=name,
            )

            assert config.author_name == name

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-IS_VALID_TRUE")
    def test_is_valid_true(self, valid_config: InitializationConfig) -> None:
        """有効性チェック(True)テスト"""
        assert valid_config.is_valid() is True

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-IS_VALID_FALSE_INVAL")
    def test_is_valid_false_invalid_project_name(self) -> None:
        """有効性チェック(False・無効プロジェクト名)テスト"""
        # NOTE: 現在の実装では、無効な設定で作成時に例外が発生するため、
        # このテストは実行されません。実装を修正する必要があります。
        # ここでは設計意図を示すためのテストとして残します。

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-IS_COMPATIBLE_WITH_S")
    def test_is_compatible_with_style_dark_comedy_false(self) -> None:
        """スタイル互換性(ダーク・コメディ非互換)テスト"""
        dark_config = InitializationConfig(
            genre=Genre.FANTASY,
            writing_style=WritingStyle.DARK,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="ダークファンタジー",
            author_name="ダーク作家",
        )

        assert dark_config.is_compatible_with_style(WritingStyle.COMEDY) is False

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-IS_COMPATIBLE_WITH_S")
    def test_is_compatible_with_style_comedy_dark_false(self) -> None:
        """スタイル互換性(コメディ・ダーク非互換)テスト"""
        comedy_config = InitializationConfig(
            genre=Genre.SLICE_OF_LIFE,
            writing_style=WritingStyle.COMEDY,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="コメディ小説",
            author_name="コメディ作家",
        )

        assert comedy_config.is_compatible_with_style(WritingStyle.DARK) is False

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-IS_COMPATIBLE_WITH_S")
    def test_is_compatible_with_style_compatible_combinations(self) -> None:
        """スタイル互換性(互換性のある組み合わせ)テスト"""
        test_cases = [
            (WritingStyle.LIGHT, WritingStyle.SERIOUS),
            (WritingStyle.LIGHT, WritingStyle.COMEDY),
            (WritingStyle.SERIOUS, WritingStyle.LIGHT),
            (WritingStyle.COMEDY, WritingStyle.LIGHT),
            (WritingStyle.DARK, WritingStyle.SERIOUS),
            (WritingStyle.SERIOUS, WritingStyle.DARK),
        ]

        for current_style, test_style in test_cases:
            config = InitializationConfig(
                genre=Genre.FANTASY,
                writing_style=current_style,
                update_frequency=UpdateFrequency.WEEKLY,
                project_name="テストプロジェクト",
                author_name="テスト作家",
            )

            assert config.is_compatible_with_style(test_style) is True

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-IS_COMPATIBLE_WITH_S")
    def test_is_compatible_with_style_self_compatibility(self) -> None:
        """スタイル互換性(自己互換性)テスト"""
        for style in WritingStyle:
            config = InitializationConfig(
                genre=Genre.FANTASY,
                writing_style=style,
                update_frequency=UpdateFrequency.WEEKLY,
                project_name="テストプロジェクト",
                author_name="テスト作家",
            )

            assert config.is_compatible_with_style(style) is True

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-GET_RECOMMENDED_SETT")
    def test_get_recommended_settings_default(self, valid_config: InitializationConfig) -> None:
        """推奨設定取得(デフォルト)テスト"""
        settings = valid_config.get_recommended_settings()

        assert "target_episode_length" in settings
        assert "chapters_per_arc" in settings
        assert "quality_focus_areas" in settings

        assert settings["chapters_per_arc"] == 10
        assert "readability" in settings["quality_focus_areas"]
        assert "engagement" in settings["quality_focus_areas"]

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-GET_RECOMMENDED_SETT")
    def test_get_recommended_settings_fantasy_genre(self) -> None:
        """推奨設定取得(ファンタジージャンル)テスト"""
        config = InitializationConfig(
            genre=Genre.FANTASY,
            writing_style=WritingStyle.SERIOUS,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="ファンタジー小説",
            author_name="ファンタジー作家",
        )

        settings = config.get_recommended_settings()

        assert settings["target_episode_length"] == 4000  # ファンタジーは長め
        assert "world_building" in settings["quality_focus_areas"]

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-GET_RECOMMENDED_SETT")
    def test_get_recommended_settings_mystery_genre(self) -> None:
        """推奨設定取得(ミステリージャンル)テスト"""
        config = InitializationConfig(
            genre=Genre.MYSTERY,
            writing_style=WritingStyle.SERIOUS,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="ミステリー小説",
            author_name="ミステリー作家",
        )

        settings = config.get_recommended_settings()

        assert "logical_consistency" in settings["quality_focus_areas"]
        assert "tension" in settings["quality_focus_areas"]

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-GET_RECOMMENDED_SETT")
    def test_get_recommended_settings_romance_genre(self) -> None:
        """推奨設定取得(ロマンスジャンル)テスト"""
        config = InitializationConfig(
            genre=Genre.ROMANCE,
            writing_style=WritingStyle.LIGHT,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="ロマンス小説",
            author_name="ロマンス作家",
        )

        settings = config.get_recommended_settings()

        assert "emotional_depth" in settings["quality_focus_areas"]
        assert "character_development" in settings["quality_focus_areas"]

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-GET_RECOMMENDED_SETT")
    def test_get_recommended_settings_light_style(self) -> None:
        """推奨設定取得(ライトスタイル)テスト"""
        config = InitializationConfig(
            genre=Genre.SLICE_OF_LIFE,
            writing_style=WritingStyle.LIGHT,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="日常系小説",
            author_name="日常系作家",
        )

        settings = config.get_recommended_settings()

        # ライトスタイルは短めに調整される
        assert settings["target_episode_length"] <= 3500

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-GET_RECOMMENDED_SETT")
    def test_get_recommended_settings_serious_style(self) -> None:
        """推奨設定取得(シリアススタイル)テスト"""
        config = InitializationConfig(
            genre=Genre.SLICE_OF_LIFE,
            writing_style=WritingStyle.SERIOUS,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="シリアス小説",
            author_name="シリアス作家",
        )

        settings = config.get_recommended_settings()

        # シリアススタイルは長めに調整される
        assert settings["target_episode_length"] >= 3500

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-GET_RECOMMENDED_SETT")
    def test_get_recommended_settings_fantasy_serious_combination(self) -> None:
        """推奨設定取得(ファンタジー・シリアス組み合わせ)テスト"""
        config = InitializationConfig(
            genre=Genre.FANTASY,
            writing_style=WritingStyle.SERIOUS,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="シリアスファンタジー",
            author_name="ファンタジー作家",
        )

        settings = config.get_recommended_settings()

        # ファンタジー(4000文字)× シリアス(3500文字以上)= max(4000, 3500) = 4000
        assert settings["target_episode_length"] == 4000
        assert "world_building" in settings["quality_focus_areas"]

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-GET_RECOMMENDED_SETT")
    def test_get_recommended_settings_romance_light_combination(self) -> None:
        """推奨設定取得(ロマンス・ライト組み合わせ)テスト"""
        config = InitializationConfig(
            genre=Genre.ROMANCE,
            writing_style=WritingStyle.LIGHT,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="ライトロマンス",
            author_name="ロマンス作家",
        )

        settings = config.get_recommended_settings()

        # ロマンス(3000文字)× ライト(3500文字以下)= min(3000, 3500) = 3000
        assert settings["target_episode_length"] == 3000
        assert "emotional_depth" in settings["quality_focus_areas"]
        assert "character_development" in settings["quality_focus_areas"]

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-GET_RECOMMENDED_SETT")
    def test_get_recommended_settings_all_genres(self) -> None:
        """推奨設定取得(全ジャンル)テスト"""
        for genre in Genre:
            config = InitializationConfig(
                genre=genre,
                writing_style=WritingStyle.LIGHT,
                update_frequency=UpdateFrequency.WEEKLY,
                project_name=f"{genre.value}小説",
                author_name="テスト作家",
            )

            settings = config.get_recommended_settings()

            # 全ジャンルで基本項目が含まれる
            assert "target_episode_length" in settings
            assert "chapters_per_arc" in settings
            assert "quality_focus_areas" in settings
            assert isinstance(settings["target_episode_length"], int)
            assert settings["target_episode_length"] > 0

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-GET_RECOMMENDED_SETT")
    def test_get_recommended_settings_all_styles(self) -> None:
        """推奨設定取得(全スタイル)テスト"""
        for style in WritingStyle:
            config = InitializationConfig(
                genre=Genre.SLICE_OF_LIFE,
                writing_style=style,
                update_frequency=UpdateFrequency.WEEKLY,
                project_name=f"{style.value}小説",
                author_name="テスト作家",
            )

            settings = config.get_recommended_settings()

            # 全スタイルで基本項目が含まれる
            assert "target_episode_length" in settings
            assert "chapters_per_arc" in settings
            assert "quality_focus_areas" in settings

            # スタイル別の文字数調整確認
            if style == WritingStyle.LIGHT:
                assert settings["target_episode_length"] <= 3500
            elif style == WritingStyle.SERIOUS:
                assert settings["target_episode_length"] >= 3500

    @pytest.mark.spec("SPEC-INITIALIZATION_VALUE_OBJECTS-GET_RECOMMENDED_SETT")
    def test_get_recommended_settings_immutability(self, valid_config: InitializationConfig) -> None:
        """推奨設定の不変性テスト"""
        settings1 = valid_config.get_recommended_settings()
        settings2 = valid_config.get_recommended_settings()

        # 異なるオブジェクトが返される(変更が他に影響しない)
        assert settings1 is not settings2
        assert settings1 == settings2

        # 変更が他の呼び出しに影響しない
        settings1["target_episode_length"] = 9999
        settings3 = valid_config.get_recommended_settings()
        assert settings3["target_episode_length"] != 9999
