"""スマートテンプレートサービスのテスト

DDD準拠テスト:
    - ビジネスロジックのテスト
- テンプレート生成アルゴリズムの検証
- ジャンル別カスタマイズの動作確認


仕様書: SPEC-DOMAIN-SERVICES
"""

import pytest

from noveler.domain.services.smart_template_service import (
    GenreType,
    ProjectCharacteristics,
    SmartTemplateService,
)
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType


class TestSmartTemplateService:
    """SmartTemplateServiceのテスト"""

    @pytest.fixture
    def service(self):
        """サービスインスタンス"""
        return SmartTemplateService()

    @pytest.fixture
    def fantasy_characteristics(self):
        """ファンタジー作品の特性"""
        return ProjectCharacteristics(
            genre=GenreType.FANTASY,
            target_length=50,
            target_audience="10-20代",
            serialization_pace="週1回",
            complexity_level="medium",
        )

    @pytest.fixture
    def sf_characteristics(self):
        """SF作品の特性"""
        return ProjectCharacteristics(
            genre=GenreType.SF,
            target_length=30,
            target_audience="20-30代",
            serialization_pace="月2回",
            complexity_level="high",
        )

    @pytest.fixture
    def short_story_characteristics(self):
        """短編作品の特性"""
        return ProjectCharacteristics(
            genre=GenreType.ROMANCE,
            target_length=15,
            target_audience="20-40代",
            serialization_pace="完結済み",
            complexity_level="low",
        )

    @pytest.fixture
    def project_context(self):
        """プロジェクトコンテキスト"""
        return {
            "title": "異世界魔法学院物語",
            "genre": "ファンタジー",
            "target_audience": "中高生",
            "author": "テスト作者",
        }

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-INIT")
    def test_init(self, service: object) -> None:
        """初期化のテスト"""
        assert hasattr(service, "genre_templates")
        assert hasattr(service, "length_adjustments")
        assert isinstance(service.genre_templates, dict)
        assert isinstance(service.length_adjustments, dict)

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-GENERATE_OPTIMIZED_T")
    def test_generate_optimized_template_master_plot_fantasy(
        self, service: object, fantasy_characteristics: object, project_context: object
    ) -> None:
        """ファンタジーマスタープロットテンプレート生成テスト"""
        template = service.generate_optimized_template(
            WorkflowStageType.MASTER_PLOT,
            fantasy_characteristics,
            project_context,
        )

        # 基本構造の確認
        assert "project_info" in template
        assert "story_structure" in template
        assert "character_arcs" in template
        assert "plot_progression" in template

        # ファンタジー固有要素の確認
        assert "magic_system" in template
        assert "world_building" in template
        assert "fantasy_elements" in template["world_building"]

        # 魔法システムの詳細確認
        magic_system = template["magic_system"]
        assert "type" in magic_system
        assert "rules" in magic_system
        assert "limitations" in magic_system
        assert "cost" in magic_system

        # プロジェクト固有情報の反映確認
        assert "異世界魔法学院物語" in str(template)
        assert "ファンタジー" in str(template)

        # メタデータの確認
        assert "template_metadata" in template
        assert template["template_metadata"]["generated_for_genre"] == "ファンタジー"
        assert template["template_metadata"]["target_length"] == 50

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-GENERATE_OPTIMIZED_T")
    def test_generate_optimized_template_master_plot_sf(
        self, service: object, sf_characteristics: object, project_context: object
    ) -> None:
        """SFマスタープロットテンプレート生成テスト"""
        sf_context = project_context.copy()
        sf_context["title"] = "未来都市の謎"
        sf_context["genre"] = "SF"

        template = service.generate_optimized_template(
            WorkflowStageType.MASTER_PLOT,
            sf_characteristics,
            sf_context,
        )

        # SF固有要素の確認
        assert "technology_system" in template
        tech_system = template["technology_system"]
        assert "tech_level" in tech_system
        assert "key_technologies" in tech_system
        assert "scientific_basis" in tech_system
        assert "social_impact" in tech_system

        # プロジェクト情報の反映
        assert "未来都市の謎" in str(template)
        assert "SF" in str(template)

        # メタデータの確認
        assert template["template_metadata"]["generated_for_genre"] == "SF"
        assert template["template_metadata"]["target_length"] == 30

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-GENERATE_OPTIMIZED_T")
    def test_generate_optimized_template_chapter_plot(
        self, service: object, fantasy_characteristics: object, project_context: object
    ) -> None:
        """章別プロットテンプレート生成テスト"""
        template = service.generate_optimized_template(
            WorkflowStageType.CHAPTER_PLOT,
            fantasy_characteristics,
            project_context,
        )

        # 章別プロット基本構造の確認
        assert "chapter_info" in template
        assert "chapter_arc" in template
        assert "character_focus" in template
        assert "plot_threads" in template
        assert "foreshadowing" in template

        # 章アーク構造の確認
        chapter_arc = template["chapter_arc"]
        assert "opening" in chapter_arc
        assert "development" in chapter_arc
        assert "climax" in chapter_arc
        assert "resolution" in chapter_arc

        # プロジェクト情報の反映
        assert "異世界魔法学院物語" in str(template)

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-GENERATE_OPTIMIZED_T")
    def test_generate_optimized_template_episode_plot(
        self, service: object, fantasy_characteristics: object, project_context: object
    ) -> None:
        """話別プロットテンプレート生成テスト"""
        template = service.generate_optimized_template(
            WorkflowStageType.EPISODE_PLOT,
            fantasy_characteristics,
            project_context,
        )

        # 話別プロット基本構造の確認
        assert "episode_info" in template
        assert "episode_structure" in template
        assert "scenes" in template
        assert "character_interactions" in template
        assert "advancement" in template

        # エピソード構造の確認
        episode_structure = template["episode_structure"]
        assert "hook" in episode_structure
        assert "development" in episode_structure
        assert "climax" in episode_structure
        assert "conclusion" in episode_structure

        # エピソード情報の確認
        episode_info = template["episode_info"]
        assert "word_count_target" in episode_info
        assert episode_info["word_count_target"] == 3000

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-LENGTH_ADJUSTMENTS_S")
    def test_length_adjustments_short(
        self, service: object, short_story_characteristics: object, project_context: object
    ) -> None:
        """短編向け調整のテスト"""
        template = service.generate_optimized_template(
            WorkflowStageType.MASTER_PLOT,
            short_story_characteristics,
            project_context,
        )

        # 短編向けペーシング調整の確認
        assert "pacing" in template
        pacing = template["pacing"]
        assert pacing["type"] == "compressed"
        assert pacing["development_speed"] == "fast"
        assert "核心的な要素に集中" in pacing["focus"]

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-LENGTH_ADJUSTMENTS_M")
    def test_length_adjustments_medium(
        self, service: object, fantasy_characteristics: object, project_context: object
    ) -> None:
        """中編向け調整のテスト"""
        template = service.generate_optimized_template(
            WorkflowStageType.MASTER_PLOT,
            fantasy_characteristics,
            project_context,
        )

        # 中編向けペーシング調整の確認
        assert "pacing" in template
        pacing = template["pacing"]
        assert pacing["type"] == "balanced"
        assert pacing["development_speed"] == "medium"

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-LENGTH_ADJUSTMENTS_L")
    def test_length_adjustments_long(self, service: object, project_context: object) -> None:
        """長編向け調整のテスト"""
        long_characteristics = ProjectCharacteristics(
            genre=GenreType.FANTASY,
            target_length=150,  # 長編
            target_audience="全年齢",
            serialization_pace="週1回",
            complexity_level="high",
        )

        template = service.generate_optimized_template(
            WorkflowStageType.MASTER_PLOT,
            long_characteristics,
            project_context,
        )

        # 長編向けペーシング調整の確認
        assert "pacing" in template
        pacing = template["pacing"]
        assert pacing["type"] == "extended"
        assert pacing["development_speed"] == "slow"
        assert "詳細な世界構築" in pacing["focus"]

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-MYSTERY_GENRE_CUSTOM")
    def test_mystery_genre_customization(self, service: object, project_context: object) -> None:
        """ミステリージャンルのカスタマイズテスト"""
        mystery_characteristics = ProjectCharacteristics(
            genre=GenreType.MYSTERY,
            target_length=40,
            target_audience="大人",
            serialization_pace="週1回",
            complexity_level="high",
        )

        template = service.generate_optimized_template(
            WorkflowStageType.MASTER_PLOT,
            mystery_characteristics,
            project_context,
        )

        # ミステリー固有要素の確認
        assert "mystery_structure" in template
        mystery_structure = template["mystery_structure"]
        assert "crime" in mystery_structure
        assert "clues" in mystery_structure
        assert "red_herrings" in mystery_structure
        assert "revelation" in mystery_structure

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-ROMANCE_GENRE_CUSTOM")
    def test_romance_genre_customization(self, service: object, project_context: object) -> None:
        """恋愛ジャンルのカスタマイズテスト"""
        romance_characteristics = ProjectCharacteristics(
            genre=GenreType.ROMANCE,
            target_length=25,
            target_audience="女性",
            serialization_pace="月2回",
            complexity_level="medium",
        )

        template = service.generate_optimized_template(
            WorkflowStageType.MASTER_PLOT,
            romance_characteristics,
            project_context,
        )

        # 恋愛固有要素の確認
        assert "relationship_development" in template
        relationship = template["relationship_development"]
        assert "meeting" in relationship
        assert "attraction" in relationship
        assert "obstacles" in relationship
        assert "resolution" in relationship

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-PLACEHOLDER_REPLACEM")
    def test_placeholder_replacement(
        self, service: object, fantasy_characteristics: object, project_context: object
    ) -> None:
        """プレースホルダー置換のテスト"""
        template = service.generate_optimized_template(
            WorkflowStageType.MASTER_PLOT,
            fantasy_characteristics,
            project_context,
        )

        # プレースホルダーが適切に置換されているか確認
        template_str = str(template)
        assert "異世界魔法学院物語" in template_str
        assert "ファンタジー" in template_str
        assert "中高生" in template_str

        # 残っているプレースホルダーの確認
        assert "[プロジェクトタイトル]" not in template_str
        assert "[ジャンル]" not in template_str
        assert "[ターゲット読者]" not in template_str

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-TEMPLATE_METADATA")
    def test_template_metadata(self, service: object, fantasy_characteristics: object, project_context: object) -> None:
        """テンプレートメタデータのテスト"""
        template = service.generate_optimized_template(
            WorkflowStageType.MASTER_PLOT,
            fantasy_characteristics,
            project_context,
        )

        # メタデータの存在確認
        assert "template_metadata" in template
        metadata = template["template_metadata"]

        # 必要な情報が含まれているか
        assert metadata["generated_for_genre"] == "ファンタジー"
        assert metadata["target_length"] == 50
        assert metadata["optimization_level"] == "smart_template_v1.0"
        assert "generation_timestamp" in metadata

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-USAGE_NOTES")
    def test_usage_notes(self, service: object, fantasy_characteristics: object, project_context: object) -> None:
        """使用説明のテスト"""
        template = service.generate_optimized_template(
            WorkflowStageType.MASTER_PLOT,
            fantasy_characteristics,
            project_context,
        )

        # 使用説明の存在確認
        assert "usage_notes" in template
        notes = template["usage_notes"]

        assert "customization" in notes
        assert "modification" in notes
        assert "reference" in notes
        assert "ファンタジー" in notes["customization"]

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-GET_BASE_TEMPLATE_MA")
    def test_get_base_template_master_plot(self, service: object) -> None:
        """マスタープロットベーステンプレート取得テスト"""
        base = service._get_base_template(WorkflowStageType.MASTER_PLOT)

        assert "project_info" in base
        assert "story_structure" in base
        assert "character_arcs" in base
        assert "plot_progression" in base
        assert "world_building" in base
        assert "themes_and_messages" in base

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-GET_BASE_TEMPLATE_CH")
    def test_get_base_template_chapter_plot(self, service: object) -> None:
        """章別プロットベーステンプレート取得テスト"""
        base = service._get_base_template(WorkflowStageType.CHAPTER_PLOT)

        assert "chapter_info" in base
        assert "chapter_arc" in base
        assert "character_focus" in base
        assert "plot_threads" in base
        assert "foreshadowing" in base

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-GET_BASE_TEMPLATE_EP")
    def test_get_base_template_episode_plot(self, service: object) -> None:
        """話別プロットベーステンプレート取得テスト"""
        base = service._get_base_template(WorkflowStageType.EPISODE_PLOT)

        assert "episode_info" in base
        assert "episode_structure" in base
        assert "scenes" in base
        assert "character_interactions" in base
        assert "advancement" in base

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-GENRE_TEMPLATES_INIT")
    def test_genre_templates_initialization(self, service: object) -> None:
        """ジャンルテンプレート初期化のテスト"""
        genre_templates = service.genre_templates

        # ファンタジーテンプレートの確認
        assert GenreType.FANTASY in genre_templates
        fantasy_template = genre_templates[GenreType.FANTASY]
        assert "required_elements" in fantasy_template
        assert "magic_system" in fantasy_template["required_elements"]

        # SFテンプレートの確認
        assert GenreType.SF in genre_templates
        sf_template = genre_templates[GenreType.SF]
        assert "required_elements" in sf_template
        assert "technology_system" in sf_template["required_elements"]

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-LENGTH_ADJUSTMENTS_I")
    def test_length_adjustments_initialization(self, service: object) -> None:
        """長さ調整初期化のテスト"""
        length_adjustments = service.length_adjustments

        assert "short" in length_adjustments
        assert "medium" in length_adjustments
        assert "long" in length_adjustments

        # 各調整項目の確認
        for key in ["short", "medium", "long"]:
            assert "chapters" in length_adjustments[key]
            assert "episodes_per_chapter" in length_adjustments[key]

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-COMPLEX_PLACEHOLDER_")
    def test_complex_placeholder_replacement(self, service: object) -> None:
        """複雑なプレースホルダー置換のテスト"""
        # 深い階層構造でのテスト
        test_template = {
            "level1": {
                "level2": {
                    "level3": "[プロジェクトタイトル] - ch01",
                    "list": ["[プロジェクトタイトル]の登場人物", "他の要素"],
                }
            }
        }

        service._replace_placeholder(test_template, "[プロジェクトタイトル]", "テスト作品")

        assert test_template["level1"]["level2"]["level3"] == "テスト作品 - ch01"
        assert test_template["level1"]["level2"]["list"][0] == "テスト作品の登場人物"
        assert test_template["level1"]["level2"]["list"][1] == "他の要素"  # 変更されない

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-MULTIPLE_GENRE_CHARA")
    def test_multiple_genre_characteristics(self, service: object, project_context: object) -> None:
        """複数ジャンルの特性テスト"""
        genres_to_test = [
            GenreType.FANTASY,
            GenreType.SF,
            GenreType.ROMANCE,
            GenreType.MYSTERY,
            GenreType.SCHOOL,
            GenreType.ISEKAI,
            GenreType.SLICE_OF_LIFE,
            GenreType.ACTION,
        ]

        for genre in genres_to_test:
            characteristics = ProjectCharacteristics(
                genre=genre,
                target_length=30,
                target_audience="一般",
                serialization_pace="週1回",
                complexity_level="medium",
            )

            template = service.generate_optimized_template(
                WorkflowStageType.MASTER_PLOT,
                characteristics,
                project_context,
            )

            # 基本構造は全ジャンルで保持
            assert "project_info" in template
            assert "story_structure" in template
            assert "template_metadata" in template
            assert template["template_metadata"]["generated_for_genre"] == genre.value

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-EDGE_CASE_EMPTY_CONT")
    def test_edge_case_empty_context(self, service: object, fantasy_characteristics: object) -> None:
        """空のコンテキストでのテスト"""
        template = service.generate_optimized_template(
            WorkflowStageType.MASTER_PLOT,
            fantasy_characteristics,
            {},  # 空のコンテキスト
        )

        # 基本構造は維持される
        assert "project_info" in template
        assert "magic_system" in template
        assert "template_metadata" in template

    @pytest.mark.spec("SPEC-SMART_TEMPLATE_SERVICE-BOUNDARY_VALUES_TARG")
    def test_boundary_values_target_length(self, service: object, project_context: object) -> None:
        """目標長さ境界値のテスト"""
        # 境界値: 20話(短編/中編の境界)
        characteristics_20 = ProjectCharacteristics(
            genre=GenreType.ROMANCE,
            target_length=20,
            target_audience="一般",
            serialization_pace="週1回",
            complexity_level="medium",
        )

        template_20 = service.generate_optimized_template(
            WorkflowStageType.MASTER_PLOT,
            characteristics_20,
            project_context,
        )

        # 境界値: 100話(中編/長編の境界)
        characteristics_100 = ProjectCharacteristics(
            genre=GenreType.FANTASY,
            target_length=100,
            target_audience="一般",
            serialization_pace="週1回",
            complexity_level="medium",
        )

        template_100 = service.generate_optimized_template(
            WorkflowStageType.MASTER_PLOT,
            characteristics_100,
            project_context,
        )

        # ペーシングタイプの確認
        assert template_20["pacing"]["type"] == "compressed"
        assert template_100["pacing"]["type"] == "balanced"
