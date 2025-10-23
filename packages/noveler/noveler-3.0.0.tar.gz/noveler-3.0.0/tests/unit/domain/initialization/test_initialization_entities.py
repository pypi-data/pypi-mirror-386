"""プロジェクト初期化ドメインエンティティのテスト

TDD準拠テスト:
    - ProjectTemplate
- ProjectInitialization


仕様書: SPEC-UNIT-TEST
"""

import pytest

from noveler.domain.initialization.entities import (
    InitializationStatus,
    ProjectInitialization,
    ProjectTemplate,
)
from noveler.domain.initialization.value_objects import (
    Genre,
    InitializationConfig,
    UpdateFrequency,
    WritingStyle,
)
from noveler.presentation.shared.shared_utilities import get_common_path_service


class TestProjectTemplate:
    """ProjectTemplateのテストクラス"""

    @pytest.fixture
    def fantasy_template(self) -> ProjectTemplate:
        """ファンタジーテンプレート"""
        path_service = get_common_path_service()
        return ProjectTemplate(
            template_id="fantasy_basic",
            genre=Genre.FANTASY,
            name="Basic Fantasy Template",
            description="Standard fantasy novel template",
            directory_structure=[str(path_service.get_plots_dir()), str(path_service.get_plots_dir()), str(path_service.get_management_dir()), str(path_service.get_manuscript_dir()), str(path_service.get_management_dir())],
        )

    @pytest.fixture
    def universal_template(self) -> ProjectTemplate:
        """汎用テンプレート"""
        return ProjectTemplate(
            template_id="basic_universal",
            genre=Genre.FANTASY,  # 実際のジャンルは関係ない
            name="Universal Template",
            description="Universal template for any genre",
        )

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-IS_SUITABLE_FOR_GENR")
    def test_is_suitable_for_genre_exact_match(self, fantasy_template: ProjectTemplate) -> None:
        """完全一致ジャンル適合性テスト"""
        assert fantasy_template.is_suitable_for_genre(Genre.FANTASY) is True

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-IS_SUITABLE_FOR_GENR")
    def test_is_suitable_for_genre_mismatch(self, fantasy_template: ProjectTemplate) -> None:
        """ジャンル不一致適合性テスト"""
        assert fantasy_template.is_suitable_for_genre(Genre.ROMANCE) is False

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-IS_SUITABLE_FOR_GENR")
    def test_is_suitable_for_genre_universal_template(self, universal_template: ProjectTemplate) -> None:
        """汎用テンプレートの適合性テスト"""
        # universal で終わるテンプレートは全ジャンルに適合
        assert universal_template.is_suitable_for_genre(Genre.MYSTERY) is True
        assert universal_template.is_suitable_for_genre(Genre.SCIENCE_FICTION) is True

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-SET_DIRECTORY_STRUCT")
    def test_set_directory_structure(self, fantasy_template: ProjectTemplate) -> None:
        """ディレクトリ構造設定テスト"""
        new_structure = ["新_企画", "新_プロット", "新_原稿"]

        fantasy_template.set_directory_structure(new_structure)

        assert fantasy_template.directory_structure == new_structure

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-VALIDATE_STRUCTURE_V")
    def test_validate_structure_valid(self, fantasy_template: ProjectTemplate) -> None:
        """有効な構造の検証テスト"""
        assert fantasy_template.validate_structure() is True

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-VALIDATE_STRUCTURE_M")
    def test_validate_structure_missing_required(self, fantasy_template: ProjectTemplate) -> None:
        """必要ディレクトリ不足の検証テスト"""
        path_service = get_common_path_service()
        fantasy_template.set_directory_structure([str(path_service.get_plots_dir()), str(path_service.get_plots_dir())])  # 必要なディレクトリが不足

        assert fantasy_template.validate_structure() is False

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-VALIDATE_STRUCTURE_E")
    def test_validate_structure_empty(self, fantasy_template: ProjectTemplate) -> None:
        """空構造の検証テスト"""
        fantasy_template.set_directory_structure([])

        assert fantasy_template.validate_structure() is False

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-APPLY_CUSTOMIZATIONS")
    def test_apply_customizations_creates_new_instance(self, fantasy_template: ProjectTemplate) -> None:
        """カスタマイズ適用で新インスタンス作成テスト"""
        custom_settings = {"theme_color": "blue", "enable_magic": True}

        customized_template = fantasy_template.apply_customizations(custom_settings)

        # 新しいインスタンスが作成される
        assert customized_template is not fantasy_template
        assert customized_template.template_id == fantasy_template.template_id
        assert customized_template.customizations == custom_settings

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-APPLY_CUSTOMIZATIONS")
    def test_apply_customizations_preserves_original(self, fantasy_template: ProjectTemplate) -> None:
        """カスタマイズ適用で元インスタンス保持テスト"""
        original_customizations = fantasy_template.customizations.copy()
        custom_settings = {"new_setting": "value"}

        customized_template = fantasy_template.apply_customizations(custom_settings)

        # 元のテンプレートは変更されない
        assert fantasy_template.customizations == original_customizations
        # 新しいテンプレートには設定が追加される
        assert customized_template.customizations == custom_settings

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-APPLY_CUSTOMIZATIONS")
    def test_apply_customizations_merges_existing(self, fantasy_template: ProjectTemplate) -> None:
        """既存カスタマイズとのマージテスト"""
        # 既存のカスタマイズを設定
        existing_custom = {"existing_key": "existing_value"}
        customized_first = fantasy_template.apply_customizations(existing_custom)

        # さらにカスタマイズを適用
        additional_custom = {"new_key": "new_value"}
        final_template = customized_first.apply_customizations(additional_custom)

        expected_customizations = {**existing_custom, **additional_custom}
        assert final_template.customizations == expected_customizations

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-GET_CUSTOMIZATION_EX")
    def test_get_customization_existing_key(self, fantasy_template: ProjectTemplate) -> None:
        """既存キーのカスタマイズ取得テスト"""
        custom_settings = {"test_key": "test_value"}
        customized_template = fantasy_template.apply_customizations(custom_settings)

        assert customized_template.get_customization("test_key") == "test_value"

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-GET_CUSTOMIZATION_NO")
    def test_get_customization_nonexistent_key(self, fantasy_template: ProjectTemplate) -> None:
        """存在しないキーのカスタマイズ取得テスト"""
        assert fantasy_template.get_customization("nonexistent_key") is None

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-HAS_CUSTOMIZATION_EX")
    def test_has_customization_existing_key(self, fantasy_template: ProjectTemplate) -> None:
        """既存キーのカスタマイズ存在チェックテスト"""
        custom_settings = {"existing_key": "value"}
        customized_template = fantasy_template.apply_customizations(custom_settings)

        assert customized_template.has_customization("existing_key") is True

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-HAS_CUSTOMIZATION_NO")
    def test_has_customization_nonexistent_key(self, fantasy_template: ProjectTemplate) -> None:
        """存在しないキーのカスタマイズ存在チェックテスト"""
        assert fantasy_template.has_customization("nonexistent_key") is False


class TestProjectInitialization:
    """ProjectInitializationのテストクラス"""

    @pytest.fixture
    def sample_config(self) -> InitializationConfig:
        """サンプル初期化設定"""
        return InitializationConfig(
            genre=Genre.FANTASY,
            writing_style=WritingStyle.LIGHT,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="test_project",
            author_name="test_author",
        )

    @pytest.fixture
    def project_initialization(self, sample_config: InitializationConfig) -> ProjectInitialization:
        """プロジェクト初期化エンティティ"""
        return ProjectInitialization(initialization_id="init_001", config=sample_config)

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-INITIALIZATION_DEFAU")
    def test_initialization_default_status(self, project_initialization: ProjectInitialization) -> None:
        """初期化デフォルトステータステスト"""
        assert project_initialization.status == InitializationStatus.STARTED
        assert project_initialization.selected_template_id is None
        assert project_initialization.created_files == []
        assert project_initialization.error_message is None

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-SELECT_TEMPLATE_VALI")
    def test_select_template_valid_state(self, project_initialization: ProjectInitialization) -> None:
        """有効状態でのテンプレート選択テスト"""
        template_id = "fantasy_basic"

        project_initialization.select_template(template_id)

        assert project_initialization.selected_template_id == template_id
        assert project_initialization.status == InitializationStatus.TEMPLATE_SELECTED

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-SELECT_TEMPLATE_INVA")
    def test_select_template_invalid_state(self, project_initialization: ProjectInitialization) -> None:
        """無効状態でのテンプレート選択テスト"""
        # 先にステータスを変更
        project_initialization.status = InitializationStatus.COMPLETED

        with pytest.raises(ValueError, match="テンプレート選択は初期状態でのみ可能です"):
            project_initialization.select_template("any_template")

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-SELECT_TEMPLATE_INCO")
    def test_select_template_incompatible_template(self, project_initialization: ProjectInitialization) -> None:
        """非互換テンプレート選択テスト"""
        # ファンタジー設定に対してロマンステンプレートを選択
        incompatible_template = "romance_basic"  # ファンタジーでない

        with pytest.raises(ValueError, match="テンプレートがジャンルに適合していません"):
            project_initialization.select_template(incompatible_template)

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-SELECT_TEMPLATE_COMP")
    def test_select_template_compatible_fantasy(self, project_initialization: ProjectInitialization) -> None:
        """互換ファンタジーテンプレート選択テスト"""
        compatible_templates = ["fantasy_basic", "fantasy_light", "universal_basic"]

        for template_id in compatible_templates:
            # 新しいインスタンスで各テンプレートをテスト
            init = ProjectInitialization("test_id", project_initialization.config)
            init.select_template(template_id)

            assert init.selected_template_id == template_id
            assert init.status == InitializationStatus.TEMPLATE_SELECTED

    def test_accepts_legacy_argument_order(self, project_initialization: ProjectInitialization) -> None:
        """旧シグネチャ `(initialization_id, config)` でも初期化できる"""
        legacy_init = ProjectInitialization("legacy-001", project_initialization.config)

        assert legacy_init.initialization_id == "legacy-001"
        assert isinstance(legacy_init.config, InitializationConfig)
        assert legacy_init.config.project_name == project_initialization.config.project_name

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-IS_TEMPLATE_COMPATIB")
    def test_is_template_compatible_genre_mapping(self, project_initialization: ProjectInitialization) -> None:
        """テンプレート互換性のジャンルマッピングテスト"""
        # ファンタジー設定に対する互換性チェック
        compatible_templates = ["fantasy_basic", "fantasy_light", "universal_basic"]
        incompatible_templates = ["romance_basic", "mystery_basic", "sf_basic"]

        for template_id in compatible_templates:
            assert project_initialization._is_template_compatible(template_id) is True

        for template_id in incompatible_templates:
            assert project_initialization._is_template_compatible(template_id) is False

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-IS_TEMPLATE_COMPATIB")
    def test_is_template_compatible_other_genres(self) -> None:
        """他ジャンルでのテンプレート互換性テスト"""
        romance_config = InitializationConfig(
            genre=Genre.ROMANCE,
            writing_style=WritingStyle.SERIOUS,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="romance_project",
            author_name="test_author",
        )

        romance_init = ProjectInitialization("romance_init", romance_config)

        # ロマンス専用テンプレートは互換
        assert romance_init._is_template_compatible("romance_emotional") is True
        # ファンタジーテンプレートは非互換
        assert romance_init._is_template_compatible("fantasy_basic") is False
        # 汎用テンプレートは互換
        assert romance_init._is_template_compatible("universal_basic") is True

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-VALIDATE_CONFIGURATI")
    def test_validate_configuration_valid_state(self, project_initialization: ProjectInitialization) -> None:
        """有効状態での設定検証テスト"""
        # 先にテンプレート選択
        project_initialization.select_template("fantasy_basic")

        project_initialization.validate_configuration()

        assert project_initialization.status == InitializationStatus.CONFIG_VALIDATED
        assert project_initialization.error_message is None

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-VALIDATE_CONFIGURATI")
    def test_validate_configuration_invalid_state(self, project_initialization: ProjectInitialization) -> None:
        """無効状態での設定検証テスト"""
        # テンプレート選択なしで検証を試行
        with pytest.raises(ValueError, match="テンプレート選択後にのみ設定検証可能です"):
            project_initialization.validate_configuration()

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-VALIDATE_CONFIGURATI")
    def test_validate_configuration_invalid_config(self, sample_config: InitializationConfig) -> None:
        """無効設定での検証テスト"""
        # 無効な設定で初期化エンティティを作成(直接的にはできないため、モックを使用)
        init = ProjectInitialization("test_id", sample_config)
        init.select_template("fantasy_basic")

        # configのis_valid()メソッドをモック
        object.__setattr__(sample_config, "is_valid", lambda: False)  # type: ignore

        init.validate_configuration()

        assert init.status == InitializationStatus.FAILED
        assert "設定に不備があります" in init.error_message

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-CREATE_PROJECT_FILES")
    def test_create_project_files_valid_state(self, project_initialization: ProjectInitialization) -> None:
        """有効状態でのプロジェクトファイル作成テスト"""
        # 前段階を完了
        project_initialization.select_template("fantasy_basic")
        project_initialization.validate_configuration()

        project_initialization.create_project_files()

        assert project_initialization.status == InitializationStatus.FILES_CREATED
        assert len(project_initialization.created_files) > 0

        # 必要なファイルが含まれているかチェック
        expected_files = [
            "test_project/プロジェクト設定.yaml",
            "test_project/10_企画/企画書.yaml",
            "test_project/20_プロット/全体構成.yaml",
            "test_project/30_設定集/キャラクター.yaml",
            "test_project/50_管理資料/品質チェック設定.yaml",
        ]

        for expected_file in expected_files:
            assert expected_file in project_initialization.created_files

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-CREATE_PROJECT_FILES")
    def test_create_project_files_invalid_state(self, project_initialization: ProjectInitialization) -> None:
        """無効状態でのプロジェクトファイル作成テスト"""
        with pytest.raises(ValueError, match="設定検証後にのみファイル作成可能です"):
            project_initialization.create_project_files()

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-COMPLETE_INITIALIZAT")
    def test_complete_initialization_valid_state(self, project_initialization: ProjectInitialization) -> None:
        """有効状態での初期化完了テスト"""
        # 全段階を完了
        project_initialization.select_template("fantasy_basic")
        project_initialization.validate_configuration()
        project_initialization.create_project_files()

        project_initialization.complete_initialization()

        assert project_initialization.status == InitializationStatus.COMPLETED

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-COMPLETE_INITIALIZAT")
    def test_complete_initialization_invalid_state(self, project_initialization: ProjectInitialization) -> None:
        """無効状態での初期化完了テスト"""
        with pytest.raises(ValueError, match="ファイル作成後にのみ完了可能です"):
            project_initialization.complete_initialization()

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-FAIL_WITH_ERROR")
    def test_fail_with_error(self, project_initialization: ProjectInitialization) -> None:
        """エラーによる初期化失敗テスト"""
        error_message = "テストエラーが発生しました"

        project_initialization.fail_with_error(error_message)

        assert project_initialization.status == InitializationStatus.FAILED
        assert project_initialization.error_message == error_message

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-IS_COMPLETED_TRUE")
    def test_is_completed_true(self, project_initialization: ProjectInitialization) -> None:
        """完了状態チェック(True)テスト"""
        # 全段階を完了
        project_initialization.select_template("fantasy_basic")
        project_initialization.validate_configuration()
        project_initialization.create_project_files()
        project_initialization.complete_initialization()

        assert project_initialization.is_completed() is True

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-IS_COMPLETED_FALSE")
    def test_is_completed_false(self, project_initialization: ProjectInitialization) -> None:
        """完了状態チェック(False)テスト"""
        assert project_initialization.is_completed() is False

        # 途中段階でも False
        project_initialization.select_template("fantasy_basic")
        assert project_initialization.is_completed() is False

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-GENERATE_QUALITY_STA")
    def test_generate_quality_standards_default(self, project_initialization: ProjectInitialization) -> None:
        """デフォルト品質基準生成テスト"""
        standards = project_initialization.generate_quality_standards()

        # 基本的な品質基準が含まれている
        assert "readability_target" in standards
        assert "dialogue_ratio_target" in standards
        assert "sentence_variety_target" in standards
        assert "narrative_depth_target" in standards

        # デフォルト値の確認
        assert standards["readability_target"] == 0.8
        assert standards["dialogue_ratio_target"] == 0.35

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-GENERATE_QUALITY_STA")
    def test_generate_quality_standards_mystery_genre(self) -> None:
        """ミステリージャンルの品質基準生成テスト"""
        mystery_config = InitializationConfig(
            genre=Genre.MYSTERY,
            writing_style=WritingStyle.SERIOUS,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="mystery_project",
            author_name="test_author",
        )

        mystery_init = ProjectInitialization("mystery_id", mystery_config)

        standards = mystery_init.generate_quality_standards()

        # ミステリー固有の基準が追加される
        assert "logical_consistency" in standards
        assert "plot_tension" in standards
        assert standards["logical_consistency"] == 0.8
        assert standards["dialogue_ratio_target"] == 0.4

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-GENERATE_QUALITY_STA")
    def test_generate_quality_standards_romance_genre(self) -> None:
        """ロマンスジャンルの品質基準生成テスト"""
        romance_config = InitializationConfig(
            genre=Genre.ROMANCE,
            writing_style=WritingStyle.LIGHT,
            update_frequency=UpdateFrequency.DAILY,
            project_name="romance_project",
            author_name="test_author",
        )

        romance_init = ProjectInitialization("romance_id", romance_config)

        standards = romance_init.generate_quality_standards()

        # ロマンス固有の基準が追加される
        assert "emotional_depth" in standards
        assert "character_interaction" in standards
        assert standards["emotional_depth"] == 0.8
        assert standards["dialogue_ratio_target"] == 0.45

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-GENERATE_QUALITY_STA")
    def test_generate_quality_standards_fantasy_genre(self, project_initialization: ProjectInitialization) -> None:
        """ファンタジージャンルの品質基準生成テスト"""
        standards = project_initialization.generate_quality_standards()

        # ファンタジー固有の基準が追加される
        assert "world_building_consistency" in standards
        assert "descriptive_richness" in standards
        assert standards["world_building_consistency"] == 0.8

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-GENERATE_QUALITY_STA")
    def test_generate_quality_standards_writing_style_adjustments(self) -> None:
        """執筆スタイル別調整テスト"""
        # シリアススタイル
        serious_config = InitializationConfig(
            genre=Genre.FANTASY,
            writing_style=WritingStyle.SERIOUS,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="serious_project",
            author_name="test_author",
        )

        serious_init = ProjectInitialization("serious_id", serious_config)
        serious_standards = serious_init.generate_quality_standards()

        # ライトスタイル
        light_config = InitializationConfig(
            genre=Genre.FANTASY,
            writing_style=WritingStyle.LIGHT,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="light_project",
            author_name="test_author",
        )

        light_init = ProjectInitialization("light_id", light_config)
        light_standards = light_init.generate_quality_standards()

        # シリアスは会話比率が低め、内面深度が高め
        assert serious_standards["dialogue_ratio_target"] < light_standards["dialogue_ratio_target"]
        assert serious_standards["narrative_depth_target"] > light_standards["narrative_depth_target"]

        # ライトは読みやすさが高め、会話比率が高め
        assert light_standards["readability_target"] > serious_standards["readability_target"]

    @pytest.mark.spec("SPEC-INITIALIZATION_ENTITIES-FULL_INITIALIZATION_")
    def test_full_initialization_workflow(self, project_initialization: ProjectInitialization) -> None:
        """完全な初期化ワークフローテスト"""
        # 1. テンプレート選択
        project_initialization.select_template("fantasy_basic")
        assert project_initialization.status == InitializationStatus.TEMPLATE_SELECTED

        # 2. 設定検証
        project_initialization.validate_configuration()
        assert project_initialization.status == InitializationStatus.CONFIG_VALIDATED

        # 3. ファイル作成
        project_initialization.create_project_files()
        assert project_initialization.status == InitializationStatus.FILES_CREATED
        assert len(project_initialization.created_files) > 0

        # 4. 初期化完了
        project_initialization.complete_initialization()
        assert project_initialization.status == InitializationStatus.COMPLETED
        assert project_initialization.is_completed() is True

        # エラーがないことを確認
        assert project_initialization.error_message is None
