"""プロジェクト初期化ドメインサービスのテスト

TDD準拠テスト:
    - TemplateSelectionService
- ProjectSetupService
- QualityStandardConfigService


仕様書: SPEC-UNIT-TEST
"""

from unittest.mock import Mock

import pytest

from noveler.domain.initialization.entities import ProjectTemplate
from noveler.domain.initialization.services import (
    ProjectSetupService,
    QualityStandardConfigService,
    TemplateRanking,
    TemplateSelectionService,
)
from noveler.domain.initialization.value_objects import (
    Genre,
    InitializationConfig,
    UpdateFrequency,
    WritingStyle,
)


class TestTemplateSelectionService:
    """TemplateSelectionServiceのテストクラス"""

    @pytest.fixture
    def template_service(self) -> TemplateSelectionService:
        """テンプレート選択サービスのインスタンス"""
        return TemplateSelectionService()

    @pytest.fixture
    def fantasy_light_config(self) -> InitializationConfig:
        """ファンタジー・ライト設定"""
        return InitializationConfig(
            genre=Genre.FANTASY,
            writing_style=WritingStyle.LIGHT,
            update_frequency=UpdateFrequency.DAILY,
            project_name="test_fantasy",
            author_name="test_author",
        )

    @pytest.fixture
    def romance_serious_config(self) -> InitializationConfig:
        """ロマンス・シリアス設定"""
        return InitializationConfig(
            genre=Genre.ROMANCE,
            writing_style=WritingStyle.SERIOUS,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="test_romance",
            author_name="test_author",
        )

    @pytest.fixture
    def sf_hard_config(self) -> InitializationConfig:
        """SF・シリアス設定"""
        return InitializationConfig(
            genre=Genre.SCIENCE_FICTION,
            writing_style=WritingStyle.SERIOUS,
            update_frequency=UpdateFrequency.MONTHLY,
            project_name="test_sf",
            author_name="test_author",
        )

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-SELECT_OPTIMAL_TEMPL")
    def test_select_optimal_template_fantasy_light(
        self, template_service: TemplateSelectionService, fantasy_light_config: InitializationConfig
    ) -> None:
        """ファンタジー・ライト設定での最適テンプレート選択テスト"""
        optimal_template = template_service.select_optimal_template(fantasy_light_config)

        # ファンタジー・ライトには fantasy_light が最適
        assert optimal_template == "fantasy_light"

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-SELECT_OPTIMAL_TEMPL")
    def test_select_optimal_template_sf_hard(
        self, template_service: TemplateSelectionService, sf_hard_config: InitializationConfig
    ) -> None:
        """SF・シリアス設定での最適テンプレート選択テスト"""
        optimal_template = template_service.select_optimal_template(sf_hard_config)

        # SF・シリアスには sf_hard が最適
        assert optimal_template == "sf_hard"

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-SELECT_OPTIMAL_TEMPL")
    def test_select_optimal_template_fallback(self, template_service: TemplateSelectionService) -> None:
        """フォールバック時のテンプレート選択テスト"""
        # ランキング結果が空の場合をシミュレート
        original_rank = template_service.rank_templates
        template_service.rank_templates = Mock(return_value=[])

        config = InitializationConfig(
            genre=Genre.MYSTERY,
            writing_style=WritingStyle.DARK,
            update_frequency=UpdateFrequency.MONTHLY,
            project_name="test",
            author_name="test",
        )

        optimal_template = template_service.select_optimal_template(config)

        # フォールバックで universal_basic が選択される
        assert optimal_template == "universal_basic"

        # 元のメソッドを復元
        template_service.rank_templates = original_rank

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-RANK_TEMPLATES_ORDER")
    def test_rank_templates_order(
        self, template_service: TemplateSelectionService, fantasy_light_config: InitializationConfig
    ) -> None:
        """テンプレートランキングの順序テスト"""
        rankings = template_service.rank_templates(fantasy_light_config)

        assert len(rankings) > 0
        assert all(isinstance(ranking, TemplateRanking) for ranking in rankings)

        # スコア降順でソートされている
        for i in range(len(rankings) - 1):
            assert rankings[i].score >= rankings[i + 1].score

        # fantasy_light が最高スコア
        assert rankings[0].template_id == "fantasy_light"

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-RANK_TEMPLATES_ROMAN")
    def test_rank_templates_romance_emotional(
        self, template_service: TemplateSelectionService, romance_serious_config: InitializationConfig
    ) -> None:
        """ロマンス設定でのランキングテスト"""
        rankings = template_service.rank_templates(romance_serious_config)

        # ロマンスジャンルのテンプレートが上位に来る
        top_template = rankings[0]
        assert "romance" in top_template.template_id
        assert top_template.score > 0.5

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-CALCULATE_COMPATIBIL")
    def test_calculate_compatibility_score_perfect_match(
        self, template_service: TemplateSelectionService, fantasy_light_config: InitializationConfig
    ) -> None:
        """完全一致時の互換性スコア計算テスト"""
        template_id = "fantasy_light"
        template_data = template_service._templates[template_id]
        score = template_service._calculate_compatibility_score(fantasy_light_config, template_id, template_data)

        # 高スコアが期待される(ジャンル40% + スタイル36% + 頻度16% + 特殊10% = 1.02、上限1.0)
        assert score >= 0.9
        assert score <= 1.0

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-CALCULATE_COMPATIBIL")
    def test_calculate_compatibility_score_genre_mismatch(self, template_service: TemplateSelectionService) -> None:
        """ジャンル不一致時のスコア計算テスト"""
        config = InitializationConfig(
            genre=Genre.MYSTERY,  # ミステリー
            writing_style=WritingStyle.LIGHT,
            update_frequency=UpdateFrequency.DAILY,
            project_name="test",
            author_name="test",
        )

        # ファンタジーテンプレートとの互換性
        template_id = "fantasy_light"
        template_data = template_service._templates[template_id]
        score = template_service._calculate_compatibility_score(config, template_id, template_data)

        # ジャンル不一致なので低スコア(スタイル一致分のみ)
        assert score < 0.5

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-CALCULATE_COMPATIBIL")
    def test_calculate_compatibility_score_universal_template(self, template_service: TemplateSelectionService) -> None:
        """汎用テンプレートのスコア計算テスト"""
        config = InitializationConfig(
            genre=Genre.MYSTERY,
            writing_style=WritingStyle.DARK,
            update_frequency=UpdateFrequency.MONTHLY,
            project_name="test",
            author_name="test",
        )

        template_id = "universal_basic"
        template_data = template_service._templates[template_id]
        score = template_service._calculate_compatibility_score(config, template_id, template_data)

        # 汎用テンプレートは中程度のスコア(25%のジャンルボーナス + スタイル適合度)
        assert score >= 0.25  # 最低でもジャンル汎用ボーナス
        assert score < 0.8  # 完全一致よりは低い

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-HAS_SPECIAL_COMPATIB")
    def test_has_special_compatibility_fantasy_light(
        self, template_service: TemplateSelectionService, fantasy_light_config: InitializationConfig
    ) -> None:
        """ファンタジー・ライトの特殊互換性テスト"""
        has_special = template_service._has_special_compatibility(fantasy_light_config, "fantasy_light")
        assert has_special is True

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-HAS_SPECIAL_COMPATIB")
    def test_has_special_compatibility_sf_hard(
        self, template_service: TemplateSelectionService, sf_hard_config: InitializationConfig
    ) -> None:
        """SF・ハードの特殊互換性テスト"""
        has_special = template_service._has_special_compatibility(sf_hard_config, "sf_hard")
        assert has_special is True

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-HAS_SPECIAL_COMPATIB")
    def test_has_special_compatibility_no_match(self, template_service: TemplateSelectionService) -> None:
        """特殊互換性なしのテスト"""
        config = InitializationConfig(
            genre=Genre.ROMANCE,
            writing_style=WritingStyle.COMEDY,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="test",
            author_name="test",
        )

        has_special = template_service._has_special_compatibility(config, "romance_emotional")
        assert has_special is False

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GENERATE_REASONING_H")
    def test_generate_reasoning_high_score(
        self, template_service: TemplateSelectionService, fantasy_light_config: InitializationConfig
    ) -> None:
        """高スコア時の理由生成テスト"""
        template_data = template_service._templates["fantasy_light"]
        score = 0.9

        reasoning = template_service._generate_reasoning(fantasy_light_config, template_data, score)

        assert "fantasyジャンルに特化" in reasoning
        assert "lightスタイルに適合" in reasoning
        assert "高い適合度" in reasoning

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GENERATE_REASONING_U")
    def test_generate_reasoning_universal_template(self, template_service: TemplateSelectionService) -> None:
        """汎用テンプレートの理由生成テスト"""
        config = InitializationConfig(
            genre=Genre.MYSTERY,
            writing_style=WritingStyle.DARK,
            update_frequency=UpdateFrequency.MONTHLY,
            project_name="test",
            author_name="test",
        )

        template_data = template_service._templates["universal_basic"]
        score = 0.5

        reasoning = template_service._generate_reasoning(config, template_data, score)

        assert "汎用テンプレートで柔軟性が高い" in reasoning
        assert "基本的な適合度" in reasoning

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GET_SELECTION_REASON")
    def test_get_selection_reasoning_valid_template(
        self, template_service: TemplateSelectionService, fantasy_light_config: InitializationConfig
    ) -> None:
        """有効なテンプレートの選択理由取得テスト"""
        reasoning = template_service.get_selection_reasoning(fantasy_light_config, "fantasy_light")

        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
        # 具体的な理由が含まれている
        assert any(keyword in reasoning for keyword in ["fantasy", "light", "適合"])

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GET_SELECTION_REASON")
    def test_get_selection_reasoning_invalid_template(
        self, template_service: TemplateSelectionService, fantasy_light_config: InitializationConfig
    ) -> None:
        """無効なテンプレートの選択理由取得テスト"""
        reasoning = template_service.get_selection_reasoning(fantasy_light_config, "invalid_template")

        assert reasoning == "不明なテンプレートです"


class TestProjectSetupService:
    """ProjectSetupServiceのテストクラス"""

    @pytest.fixture
    def setup_service(self) -> ProjectSetupService:
        """プロジェクトセットアップサービスのインスタンス"""
        return ProjectSetupService()

    @pytest.fixture
    def sample_config(self) -> InitializationConfig:
        """サンプル設定"""
        return InitializationConfig(
            genre=Genre.FANTASY,
            writing_style=WritingStyle.LIGHT,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="test_project",
            author_name="test_author",
        )

    @pytest.fixture
    def sample_template(self) -> ProjectTemplate:
        """サンプルテンプレート"""
        return ProjectTemplate(
            template_id="fantasy_light",
            genre=Genre.FANTASY,
            name="Fantasy Light Template",
            description="Light fantasy template",
        )

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GENERATE_DIRECTORY_S")
    def test_generate_directory_structure_base(
        self, setup_service: ProjectSetupService, sample_config: InitializationConfig, sample_template: ProjectTemplate
    ) -> None:
        """基本ディレクトリ構造生成テスト"""
        directories = setup_service.generate_directory_structure(sample_config, sample_template)

        # 基本ディレクトリが含まれている
        expected_base = [
            "test_project/",
            "test_project/10_企画/",
            "test_project/20_プロット/",
            "test_project/20_プロット/章別プロット/",
            "test_project/30_設定集/",
            "test_project/40_原稿/",
            "test_project/50_管理資料/",
            "test_project/90_アーカイブ/",
        ]

        for base_dir in expected_base:
            assert base_dir in directories

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GENERATE_DIRECTORY_S")
    def test_generate_directory_structure_fantasy_specific(
        self, setup_service: ProjectSetupService, sample_config: InitializationConfig, sample_template: ProjectTemplate
    ) -> None:
        """ファンタジー固有ディレクトリ生成テスト"""
        directories = setup_service.generate_directory_structure(sample_config, sample_template)

        # ファンタジー固有ディレクトリが含まれている
        fantasy_dirs = [
            "test_project/30_設定集/魔法システム/",
            "test_project/30_設定集/種族設定/",
        ]

        for fantasy_dir in fantasy_dirs:
            assert fantasy_dir in directories

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GENERATE_DIRECTORY_S")
    def test_generate_directory_structure_sf_specific(
        self, setup_service: ProjectSetupService, sample_template: ProjectTemplate
    ) -> None:
        """SF固有ディレクトリ生成テスト"""
        sf_config = InitializationConfig(
            genre=Genre.SCIENCE_FICTION,
            writing_style=WritingStyle.SERIOUS,
            update_frequency=UpdateFrequency.MONTHLY,
            project_name="sf_project",
            author_name="test_author",
        )

        directories = setup_service.generate_directory_structure(sf_config, sample_template)

        # SF固有ディレクトリが含まれている
        sf_dirs = [
            "sf_project/30_設定集/技術仕様/",
            "sf_project/30_設定集/世界年表/",
        ]

        for sf_dir in sf_dirs:
            assert sf_dir in directories

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GENERATE_DIRECTORY_S")
    def test_generate_directory_structure_other_genre(
        self, setup_service: ProjectSetupService, sample_template: ProjectTemplate
    ) -> None:
        """その他ジャンルのディレクトリ生成テスト"""
        romance_config = InitializationConfig(
            genre=Genre.ROMANCE,
            writing_style=WritingStyle.LIGHT,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="romance_project",
            author_name="test_author",
        )

        directories = setup_service.generate_directory_structure(romance_config, sample_template)

        # ジャンル固有ディレクトリは追加されない
        fantasy_dirs = ["romance_project/30_設定集/魔法システム/", "romance_project/30_設定集/種族設定/"]
        sf_dirs = ["romance_project/30_設定集/技術仕様/", "romance_project/30_設定集/世界年表/"]

        for genre_dir in fantasy_dirs + sf_dirs:
            assert genre_dir not in directories

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GENERATE_INITIAL_FIL")
    def test_generate_initial_files(
        self, setup_service: ProjectSetupService, sample_config: InitializationConfig
    ) -> None:
        """初期ファイル生成テスト"""
        files = setup_service.generate_initial_files(sample_config)

        # 必要なファイルが生成されている
        expected_files = [
            "test_project/プロジェクト設定.yaml",
            "test_project/10_企画/企画書.yaml",
            "test_project/20_プロット/全体構成.yaml",
            "test_project/30_設定集/キャラクター.yaml",
        ]

        for expected_file in expected_files:
            assert expected_file in files
            assert isinstance(files[expected_file], str)
            assert len(files[expected_file]) > 0

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GENERATE_PROJECT_CON")
    def test_generate_project_config_content(
        self, setup_service: ProjectSetupService, sample_config: InitializationConfig
    ) -> None:
        """プロジェクト設定ファイル内容テスト"""
        config_content = setup_service._generate_project_config(sample_config)

        # 設定内容が含まれている
        assert f'project_name: "{sample_config.project_name}"' in config_content
        assert f'author: "{sample_config.author_name}"' in config_content
        assert f'genre: "{sample_config.genre.value}"' in config_content
        assert f'writing_style: "{sample_config.writing_style.value}"' in config_content
        assert f'update_frequency: "{sample_config.update_frequency.value}"' in config_content

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GENERATE_PROJECT_PLA")
    def test_generate_project_plan_content(
        self, setup_service: ProjectSetupService, sample_config: InitializationConfig
    ) -> None:
        """企画書ファイル内容テスト"""
        plan_content = setup_service._generate_project_plan(sample_config)

        # 企画書内容が含まれている
        assert f'title: "{sample_config.project_name}"' in plan_content
        assert f'author: "{sample_config.author_name}"' in plan_content
        assert f'genre: "{sample_config.genre.value}"' in plan_content
        assert "concept:" in plan_content
        assert "synopsis:" in plan_content

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GENERATE_MASTER_PLOT")
    def test_generate_master_plot_content(
        self, setup_service: ProjectSetupService, sample_config: InitializationConfig
    ) -> None:
        """全体構成ファイル内容テスト"""
        plot_content = setup_service._generate_master_plot(sample_config)

        # 全体構成内容が含まれている
        assert f'title: "{sample_config.project_name}"' in plot_content
        assert "structure:" in plot_content
        assert "acts:" in plot_content
        assert "act1:" in plot_content
        assert "act2:" in plot_content
        assert "act3:" in plot_content

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GENERATE_CHARACTER_S")
    def test_generate_character_settings_content(
        self, setup_service: ProjectSetupService, sample_config: InitializationConfig
    ) -> None:
        """キャラクター設定ファイル内容テスト"""
        char_content = setup_service._generate_character_settings(sample_config)

        # キャラクター設定内容が含まれている
        assert "characters:" in char_content
        assert "main:" in char_content
        assert "protagonist:" in char_content
        assert "supporting:" in char_content
        assert "antagonist:" in char_content


class TestQualityStandardConfigService:
    """QualityStandardConfigServiceのテストクラス"""

    @pytest.fixture
    def quality_service(self) -> QualityStandardConfigService:
        """品質基準設定サービスのインスタンス"""
        return QualityStandardConfigService()

    @pytest.fixture
    def base_config(self) -> InitializationConfig:
        """基本設定"""
        return InitializationConfig(
            genre=Genre.SLICE_OF_LIFE,  # 特殊調整なしのジャンル
            writing_style=WritingStyle.COMEDY,  # 特殊調整なしのスタイル
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="test_project",
            author_name="test_author",
        )

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GENERATE_QUALITY_STA")
    def test_generate_quality_standards_base(
        self, quality_service: QualityStandardConfigService, base_config: InitializationConfig
    ) -> None:
        """基本品質基準生成テスト"""
        standards = quality_service.generate_quality_standards(base_config)

        # ベース基準が含まれている
        assert "readability" in standards
        assert "dialogue_ratio" in standards
        assert "sentence_variety" in standards

        # 各項目の構造チェック
        for standard in ["readability", "dialogue_ratio", "sentence_variety"]:
            assert "target_score" in standards[standard] or "target_ratio" in standards[standard]
            assert "weight" in standards[standard]
            assert "min_threshold" in standards[standard] or "acceptable_range" in standards[standard]

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GENERATE_QUALITY_STA")
    def test_generate_quality_standards_mystery_genre(self, quality_service: QualityStandardConfigService) -> None:
        """ミステリージャンルの品質基準生成テスト"""
        mystery_config = InitializationConfig(
            genre=Genre.MYSTERY,
            writing_style=WritingStyle.SERIOUS,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="mystery_project",
            author_name="test_author",
        )

        standards = quality_service.generate_quality_standards(mystery_config)

        # ミステリー固有の基準が追加されている
        assert "logical_consistency" in standards
        assert standards["logical_consistency"]["target_score"] == 85
        assert standards["logical_consistency"]["weight"] == 1.2

        # 会話比率がミステリー向けに調整されている
        assert standards["dialogue_ratio"]["target_ratio"] == 0.4

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GENERATE_QUALITY_STA")
    def test_generate_quality_standards_romance_genre(self, quality_service: QualityStandardConfigService) -> None:
        """ロマンスジャンルの品質基準生成テスト"""
        romance_config = InitializationConfig(
            genre=Genre.ROMANCE,
            writing_style=WritingStyle.LIGHT,
            update_frequency=UpdateFrequency.DAILY,
            project_name="romance_project",
            author_name="test_author",
        )

        standards = quality_service.generate_quality_standards(romance_config)

        # ロマンス固有の基準が追加されている
        assert "emotional_depth" in standards
        assert standards["emotional_depth"]["target_score"] == 80
        assert standards["emotional_depth"]["weight"] == 1.3

        # 会話比率がロマンス向けに調整されている
        assert standards["dialogue_ratio"]["target_ratio"] == 0.45

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GENERATE_QUALITY_STA")
    def test_generate_quality_standards_fantasy_genre(self, quality_service: QualityStandardConfigService) -> None:
        """ファンタジージャンルの品質基準生成テスト"""
        fantasy_config = InitializationConfig(
            genre=Genre.FANTASY,
            writing_style=WritingStyle.SERIOUS,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="fantasy_project",
            author_name="test_author",
        )

        standards = quality_service.generate_quality_standards(fantasy_config)

        # ファンタジー固有の基準が追加されている
        assert "world_building" in standards
        assert standards["world_building"]["target_score"] == 75
        assert standards["world_building"]["weight"] == 1.1

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GENERATE_QUALITY_STA")
    def test_generate_quality_standards_light_style(self, quality_service: QualityStandardConfigService) -> None:
        """ライトスタイルの品質基準生成テスト"""
        light_config = InitializationConfig(
            genre=Genre.SLICE_OF_LIFE,
            writing_style=WritingStyle.LIGHT,
            update_frequency=UpdateFrequency.DAILY,
            project_name="light_project",
            author_name="test_author",
        )

        standards = quality_service.generate_quality_standards(light_config)

        # ライトスタイル向けに調整されている
        assert standards["readability"]["target_score"] == 85
        assert standards["readability"]["weight"] == 1.2

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GENERATE_QUALITY_STA")
    def test_generate_quality_standards_serious_style(self, quality_service: QualityStandardConfigService) -> None:
        """シリアススタイルの品質基準生成テスト"""
        serious_config = InitializationConfig(
            genre=Genre.SLICE_OF_LIFE,
            writing_style=WritingStyle.SERIOUS,
            update_frequency=UpdateFrequency.WEEKLY,
            project_name="serious_project",
            author_name="test_author",
        )

        standards = quality_service.generate_quality_standards(serious_config)

        # シリアススタイル固有の基準が追加されている
        assert "narrative_depth" in standards
        assert standards["narrative_depth"]["target_score"] == 80
        assert standards["narrative_depth"]["weight"] == 1.2

    @pytest.mark.spec("SPEC-INITIALIZATION_SERVICES-GENERATE_QUALITY_STA")
    def test_generate_quality_standards_combined_adjustments(
        self, quality_service: QualityStandardConfigService
    ) -> None:
        """ジャンル・スタイル組み合わせ調整テスト"""
        config = InitializationConfig(
            genre=Genre.ROMANCE,  # emotional_depth 追加、dialogue_ratio 0.45
            writing_style=WritingStyle.LIGHT,  # readability 向上
            update_frequency=UpdateFrequency.DAILY,
            project_name="combined_project",
            author_name="test_author",
        )

        standards = quality_service.generate_quality_standards(config)

        # 両方の調整が適用されている
        assert "emotional_depth" in standards  # ロマンス調整
        assert standards["readability"]["target_score"] == 85  # ライト調整
        assert standards["dialogue_ratio"]["target_ratio"] == 0.45  # ロマンス調整
