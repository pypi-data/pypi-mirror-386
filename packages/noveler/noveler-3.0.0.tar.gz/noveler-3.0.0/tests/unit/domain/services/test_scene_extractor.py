"""シーン抽出サービスのテスト

DDD準拠テスト:
    - ビジネスロジックのテスト
- シーン抽出アルゴリズムの検証
- マージ・重複排除のテスト


仕様書: SPEC-DOMAIN-SERVICES
"""

from unittest.mock import Mock

import pytest

from noveler.domain.entities.scene_management_entities import SceneCategory
from noveler.domain.services.scene_extractor import ExtractedScene, SceneExtractor, SceneImportance


class TestSceneExtractor:
    """SceneExtractorのテスト"""

    @pytest.fixture
    def extractor(self):
        """抽出器インスタンス"""
        return SceneExtractor()

    @pytest.fixture
    def master_plot_data(self):
        """マスタープロットデータ"""
        return {
            "metadata": {
                "total_episodes": 30,
                "total_chapters": 3,
            },
            "story_structure": {
                "opening": {
                    "description": "主人公が異世界に転生する",
                },
                "development": {
                    "turning_points": ["力の覚醒", "仲間との出会い"],
                    "major_revelations": ["真の敵の正体", "世界の秘密"],
                },
                "climax": {
                    "description": "最終決戦",
                    "resolution": "平和な世界の実現",
                },
            },
        }

    @pytest.fixture
    def foreshadowing_data(self):
        """伏線データのモック"""
        f1 = Mock()
        f1.id.value = "F001"
        f1.title = "主人公の秘密"
        f1.importance = 5
        f1.planting.content = "謎の紋章が光る"
        f1.planting.chapter = 1
        f1.planting.episode = "第003話"
        f1.resolution.impact = "主人公の正体が明かされる"
        f1.resolution.chapter = 3
        f1.resolution.episode = "第025話"

        f2 = Mock()
        f2.id.value = "F002"
        f2.title = "隠された力"
        f2.importance = 3  # 重要度が低い
        f2.planting.content = "違和感を覚える"
        f2.planting.chapter = 1
        f2.planting.episode = "第005話"
        f2.resolution.impact = "新たな能力に目覚める"
        f2.resolution.chapter = 2
        f2.resolution.episode = "第015話"

        return [f1, f2]

    @pytest.fixture
    def chapter_plot_data(self):
        """章別プロットデータ"""
        return {
            "metadata": {
                "chapter_number": 2,
            },
            "episodes": [
                {
                    "number": 11,
                    "scenes": ["戦闘シーン", "感動の再会", "新たな旅立ち"],
                },
                {
                    "number": 12,
                    "scenes": ["修行開始", "師匠との出会い"],
                },
            ],
        }

    @pytest.mark.spec("SPEC-SCENE_EXTRACTOR-EXTRACT_FROM_MASTER_")
    def test_extract_from_master_plot(self, extractor: object, master_plot_data: object) -> None:
        """マスタープロットからの抽出テスト"""
        scenes = extractor.extract_from_master_plot(master_plot_data)

        assert len(scenes) == 6  # opening + 2 turning_points + 2 revelations + climax

        # オープニングシーンの確認
        opening = next(s for s in scenes if s.category == SceneCategory.OPENING)
        assert opening.title == "物語の開幕"
        assert opening.importance == SceneImportance.CRITICAL
        assert opening.chapter == 1
        assert opening.episode_range == (1, 2)

        # 転換点の確認
        turning_points = [s for s in scenes if s.category == SceneCategory.TURNING_POINT]
        assert len(turning_points) == 2
        assert all(tp.importance == SceneImportance.HIGH for tp in turning_points)

        # クライマックスの確認
        climax = next(s for s in scenes if s.title == "クライマックス")
        assert climax.importance == SceneImportance.CRITICAL
        assert climax.chapter == 3
        assert climax.episode_range == (27, 29)  # total_episodes - 3 から total_episodes - 1

    @pytest.mark.spec("SPEC-SCENE_EXTRACTOR-EXTRACT_FROM_MASTER_")
    def test_extract_from_master_plot_partial_data(self, extractor: object) -> None:
        """部分的なマスタープロットデータからの抽出テスト"""
        partial_data = {
            "story_structure": {
                "opening": {"description": "始まり"},
                "development": {},  # 転換点なし
            }
        }

        scenes = extractor.extract_from_master_plot(partial_data)

        assert len(scenes) == 1  # openingのみ
        assert scenes[0].category == SceneCategory.OPENING

    @pytest.mark.spec("SPEC-SCENE_EXTRACTOR-EXTRACT_FROM_FORESHA")
    def test_extract_from_foreshadowing(self, extractor: object, foreshadowing_data: object) -> None:
        """伏線情報からの抽出テスト"""
        scenes = extractor.extract_from_foreshadowing(foreshadowing_data)

        # 重要度4以上の伏線のみ抽出される(f1のみ)
        assert len(scenes) == 2  # 仕込みと回収

        planting = next(s for s in scenes if "仕込み" in s.title)
        assert planting.category == SceneCategory.FORESHADOWING
        assert planting.importance == SceneImportance.MEDIUM
        assert planting.episode_range == (3, 3)

        resolution = next(s for s in scenes if "回収" in s.title)
        assert resolution.category == SceneCategory.CLIMAX
        assert resolution.importance == SceneImportance.HIGH
        assert resolution.episode_range == (25, 25)

    @pytest.mark.spec("SPEC-SCENE_EXTRACTOR-EXTRACT_FROM_CHAPTER")
    def test_extract_from_chapter_plot(self, extractor: object, chapter_plot_data: object) -> None:
        """章別プロットからの抽出テスト"""
        scenes = extractor.extract_from_chapter_plot(chapter_plot_data)

        assert len(scenes) == 5  # 3 + 2 scenes

        # 全てのシーンがch02のものであることを確認
        assert all(s.chapter == 2 for s in scenes)

        # 第11話のシーン
        ep11_scenes = [s for s in scenes if s.episode_range[0] == 11]
        assert len(ep11_scenes) == 3
        assert any("戦闘シーン" in s.title for s in ep11_scenes)

        # 第12話のシーン
        ep12_scenes = [s for s in scenes if s.episode_range[0] == 12]
        assert len(ep12_scenes) == 2
        assert any("修行開始" in s.title for s in ep12_scenes)

    @pytest.mark.spec("SPEC-SCENE_EXTRACTOR-EXTRACT_FROM_CHAPTER")
    def test_extract_from_chapter_plot_invalid_data(self, extractor: object) -> None:
        """無効な章別プロットデータの処理テスト"""
        # 辞書でないデータ
        scenes = extractor.extract_from_chapter_plot("invalid data")
        assert scenes == []

        # episodesがリストでない
        scenes = extractor.extract_from_chapter_plot({"episodes": "not a list"})
        assert scenes == []

        # 空のデータ
        scenes = extractor.extract_from_chapter_plot({})
        assert scenes == []

    @pytest.mark.spec("SPEC-SCENE_EXTRACTOR-EXTRACT_EPISODE_NUMB")
    def test_extract_episode_number(self, extractor: object) -> None:
        """エピソード番号抽出のテスト"""
        assert extractor._extract_episode_number("第001話") == 1
        assert extractor._extract_episode_number("第123話") == 123
        assert extractor._extract_episode_number("5話") == 5
        assert extractor._extract_episode_number("episode 42") == 42
        assert extractor._extract_episode_number("テキストのみ") == 1  # デフォルト値

    @pytest.mark.spec("SPEC-SCENE_EXTRACTOR-MERGE_AND_DEDUPLICAT")
    def test_merge_and_deduplicate_no_overlap(self, extractor: object) -> None:
        """重複のないシーンのマージテスト"""
        scenes = [
            ExtractedScene(
                scene_id="scene_001",
                title="シーン1",
                category=SceneCategory.NORMAL,
                description="説明1",
                importance=SceneImportance.MEDIUM,
                chapter=1,
                episode_range=(1, 1),
                source="test",
            ),
            ExtractedScene(
                scene_id="scene_002",
                title="シーン2",
                category=SceneCategory.CLIMAX,
                description="説明2",
                importance=SceneImportance.HIGH,
                chapter=1,
                episode_range=(2, 2),
                source="test",
            ),
        ]

        merged = extractor.merge_and_deduplicate(scenes)

        assert len(merged) == 2
        assert merged[0].episode_range == (1, 1)
        assert merged[1].episode_range == (2, 2)

    @pytest.mark.spec("SPEC-SCENE_EXTRACTOR-MERGE_AND_DEDUPLICAT")
    def test_merge_and_deduplicate_with_overlap(self, extractor: object) -> None:
        """重複するシーンのマージテスト"""
        scenes = [
            ExtractedScene(
                scene_id="scene_001",
                title="重要シーン",
                category=SceneCategory.CLIMAX,
                description="クライマックスの説明",
                importance=SceneImportance.CRITICAL,
                chapter=3,
                episode_range=(25, 25),
                source="master_plot",
            ),
            ExtractedScene(
                scene_id="scene_002",
                title="伏線回収",
                category=SceneCategory.NORMAL,
                description="伏線の回収",
                importance=SceneImportance.HIGH,
                chapter=3,
                episode_range=(25, 25),
                source="foreshadowing",
            ),
            ExtractedScene(
                scene_id="scene_003",
                title="通常シーン",
                category=SceneCategory.NORMAL,
                description="追加の説明",
                importance=SceneImportance.MEDIUM,
                chapter=3,
                episode_range=(25, 25),
                source="chapter_plot",
            ),
        ]

        merged = extractor.merge_and_deduplicate(scenes)

        assert len(merged) == 1
        merged_scene = merged[0]

        # 最も重要度の高いシーンが採用される
        assert merged_scene.title == "重要シーン"
        assert merged_scene.importance == SceneImportance.CRITICAL

        # 他のシーンの説明も統合される
        assert "クライマックスの説明" in merged_scene.description
        assert "伏線の回収" in merged_scene.description
        assert "追加の説明" in merged_scene.description
        assert "+2others" in merged_scene.source

    @pytest.mark.spec("SPEC-SCENE_EXTRACTOR-EXTRACTED_SCENE_TO_D")
    def test_extracted_scene_to_dict(self) -> None:
        """ExtractedSceneの辞書変換テスト"""
        scene = ExtractedScene(
            scene_id="scene_001",
            title="テストシーン",
            category=SceneCategory.OPENING,
            description="説明文",
            importance=SceneImportance.HIGH,
            chapter=1,
            episode_range=(1, 3),
            source="test",
        )

        result = scene.to_dict()

        assert result["scene_id"] == "scene_001"
        assert result["title"] == "テストシーン"
        assert result["category"] == "opening"
        assert result["importance"] == "high"
        assert result["episode_range"] == [1, 3]
        assert result["episodes"] == [1, 2, 3]  # rangeが展開される

    @pytest.mark.spec("SPEC-SCENE_EXTRACTOR-FULL_EXTRACTION_WORK")
    def test_full_extraction_workflow(
        self, extractor: object, master_plot_data: object, foreshadowing_data: object, chapter_plot_data: object
    ) -> None:
        """完全な抽出ワークフローのテスト"""
        # 各ソースから抽出
        scenes = []
        scenes.extend(extractor.extract_from_master_plot(master_plot_data))
        scenes.extend(extractor.extract_from_foreshadowing(foreshadowing_data))
        scenes.extend(extractor.extract_from_chapter_plot(chapter_plot_data))

        # 初期の総シーン数
        initial_count = len(scenes)
        assert initial_count > 0

        # マージと重複排除
        merged_scenes = extractor.merge_and_deduplicate(scenes)

        # マージ後のシーン数(重複があれば減る)
        assert len(merged_scenes) <= initial_count

        # 時系列順になっているか確認
        for i in range(1, len(merged_scenes)):
            assert merged_scenes[i - 1].episode_range[0] <= merged_scenes[i].episode_range[0]

    @pytest.mark.spec("SPEC-SCENE_EXTRACTOR-IMPORTANCE_ENUM_VALU")
    def test_importance_enum_values(self) -> None:
        """SceneImportance列挙型の値テスト"""
        assert SceneImportance.CRITICAL.value == "critical"
        assert SceneImportance.HIGH.value == "high"
        assert SceneImportance.MEDIUM.value == "medium"
        assert SceneImportance.LOW.value == "low"

    @pytest.mark.spec("SPEC-SCENE_EXTRACTOR-SCENE_CATEGORY_MAPPI")
    def test_scene_category_mapping(self) -> None:
        """SceneCategoryのマッピングテスト"""
        # SceneCategoryが正しくインポートされて使用できることを確認
        assert hasattr(SceneCategory, "OPENING")
        assert hasattr(SceneCategory, "CLIMAX")
        assert hasattr(SceneCategory, "TURNING_POINT")
        assert hasattr(SceneCategory, "FORESHADOWING")
        assert hasattr(SceneCategory, "ENDING")
        assert hasattr(SceneCategory, "NORMAL")
