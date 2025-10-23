"""伏線抽出サービスのテスト

DDD準拠テスト:
    - ビジネスロジックのテスト
- 伏線抽出アルゴリズムの検証
- 値オブジェクトの生成確認
"""

import pytest

from noveler.domain.services.foreshadowing_extractor import ForeshadowingExtractor
from noveler.domain.value_objects.foreshadowing import (
    Foreshadowing,
    ForeshadowingCategory,
    ForeshadowingId,
    ForeshadowingStatus,
    ReaderReaction,
    SubtletyLevel,
)


class TestForeshadowingExtractor:
    """ForeshadowingExtractorのテスト"""

    @pytest.fixture
    def extractor(self):
        """抽出器インスタンス"""
        return ForeshadowingExtractor()

    @pytest.fixture
    def master_plot_data_full(self):
        """完全なマスタープロットデータ"""
        return {
            "story_structure": {
                "opening": "主人公は記憶を失った状態で目覚める。謎の声が聞こえる。",
                "development": {
                    "major_revelations": [
                        "実は主人公は選ばれし者だった",
                        "敵の正体は主人公の兄だった",
                        "世界の真実が明かされる",
                    ],
                    "turning_points": ["力の覚醒", "仲間の裏切り"],
                },
                "total_chapters": 3,
            },
            "chapter_outlines": [
                {
                    "chapter_number": 1,
                    "key_events": ["謎の紋章が現れる", "隠された部屋の発見", "伏線となる夢"],
                }
            ],
            "characters": {
                "主人公": {
                    "hidden_aspects": ["実は王族の血統"],
                    "secrets": ["幼少期の記憶が封印されている"],
                },
                "ヒロイン": {"hidden_aspects": ["黒幕と繋がりがある"]},
            },
            "themes": {"main": "真実と正体の探求"},
        }

    @pytest.fixture
    def chapter_plot_data(self):
        """章別プロットデータ"""
        return {
            "metadata": {"chapter_number": 2},
            "episodes": [
                {
                    "number": 11,
                    "title": "隠された真相への手がかり",
                    "scenes": ["謎の人物との遭遇", "秘密の文書を発見"],
                }
            ],
            "key_events": ["過去の記憶がフラッシュバック"],
        }

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_init(self, extractor: object) -> None:
        """初期化のテスト"""
        assert extractor._foreshadowing_counter == 0
        assert hasattr(extractor, "FORESHADOWING_KEYWORDS")
        assert isinstance(extractor.FORESHADOWING_KEYWORDS, dict)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_extract_from_master_plot_empty(self, extractor: object) -> None:
        """空のマスタープロットからの抽出テスト"""
        result = extractor.extract_from_master_plot({})
        assert result == []

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_extract_from_master_plot_full(self, extractor: object, master_plot_data_full: object) -> None:
        """完全なマスタープロットからの抽出テスト"""
        result = extractor.extract_from_master_plot(master_plot_data_full)

        assert len(result) > 0
        assert all(isinstance(f, Foreshadowing) for f in result)

        # カテゴリの多様性を確認
        categories = {f.category for f in result}
        assert ForeshadowingCategory.MYSTERY in categories
        assert ForeshadowingCategory.CHARACTER in categories
        assert ForeshadowingCategory.THEMATIC in categories

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_extract_from_story_structure(self, extractor: object) -> None:
        """ストーリー構造からの抽出テスト"""
        story_structure = {
            "opening": "主人公の正体には秘密が隠されていた",
            "development": {
                "major_revelations": ["真実が明かされる"],
                "turning_points": ["力の覚醒"],
            },
            "total_chapters": 3,
        }

        result = extractor._extract_from_story_structure(story_structure)

        assert len(result) >= 3  # opening, revelation, turning point
        assert any(f.category == ForeshadowingCategory.MYSTERY for f in result)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_extract_from_chapter_outlines(self, extractor: object) -> None:
        """章別概要からの抽出テスト"""
        chapter_outlines = [
            {"chapter_number": 1, "key_events": ["謎の手紙が届く", "秘密の扉を発見"]},
            {"chapter_number": 2, "key_events": ["普通の出来事", "伏線となる会話"]},
        ]

        result = extractor._extract_from_chapter_outlines(chapter_outlines)

        assert len(result) >= 2
        assert all(f.planting.chapter in [1, 2] for f in result)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_extract_from_characters(self, extractor: object) -> None:
        """キャラクター設定からの抽出テスト"""
        characters = {
            "主人公": {
                "hidden_aspects": ["実は魔王の子供", "記憶喪失"],
                "secrets": ["過去に大罪を犯した"],
            },
            "味方A": {"secrets": ["敵のスパイ"]},
        }

        result = extractor._extract_from_characters(characters)

        assert len(result) == 4  # 2 hidden + 2 secrets
        assert all(f.category == ForeshadowingCategory.CHARACTER for f in result)
        assert any("主人公" in f.title for f in result)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_extract_from_themes(self, extractor: object) -> None:
        """テーマからの抽出テスト"""
        themes = {"main": "真実と虚構の境界", "sub": ["成長", "友情"]}

        result = extractor._extract_from_themes(themes)

        assert len(result) == 1
        assert result[0].category == ForeshadowingCategory.THEMATIC
        assert "真実" in result[0].title

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_extract_from_themes_no_keywords(self, extractor: object) -> None:
        """キーワードを含まないテーマのテスト"""
        themes = {"main": "友情と努力"}

        result = extractor._extract_from_themes(themes)

        assert len(result) == 0

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_contains_mystery_keywords(self, extractor: object) -> None:
        """謎キーワード判定のテスト"""
        assert extractor._contains_mystery_keywords("この謎を解明する")
        assert extractor._contains_mystery_keywords("隠された真実")
        assert extractor._contains_mystery_keywords("本当の正体は")
        assert not extractor._contains_mystery_keywords("普通の日常")

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_is_foreshadowing_event(self, extractor: object) -> None:
        """伏線イベント判定のテスト"""
        assert extractor._is_foreshadowing_event("謎の人物が現れる")
        assert extractor._is_foreshadowing_event("伏線となる出来事")
        assert not extractor._is_foreshadowing_event("朝食を食べる")

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_extract_description(self, extractor: object) -> None:
        """説明文抽出のテスト"""
        # 文字列の場合
        assert extractor._extract_description("テスト文字列") == "テスト文字列"

        # 辞書の場合
        assert extractor._extract_description({"description": "説明文"}) == "説明文"
        assert extractor._extract_description({"content": "内容文"}) == "内容文"

        # その他の場合
        assert extractor._extract_description(123) == "123"

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_extract_foreshadowing_title(self, extractor: object) -> None:
        """タイトル生成のテスト"""
        # 短いテキスト
        title1 = extractor._extract_foreshadowing_title("短いタイトル")
        assert title1 == "短いタイトル"

        # 長いテキスト
        long_text = "とても長いタイトルで30文字を超えています実際に30文字を超えるテキストにします"
        title2 = extractor._extract_foreshadowing_title(long_text)
        assert len(title2) == 30
        assert title2 == long_text[:30]

        # 改行を含むテキスト
        title3 = extractor._extract_foreshadowing_title("タイトル\n改行あり")
        assert "\n" not in title3
        assert title3 == "タイトル 改行あり"

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_create_mystery_foreshadowing(self, extractor: object) -> None:
        """謎系伏線作成のテスト"""
        foreshadowing = extractor._create_mystery_foreshadowing(
            title="失われた記憶",
            description="主人公の過去の記憶が封印されている",
            planting_chapter=1,
            resolution_chapter=3,
        )

        assert foreshadowing is not None
        assert foreshadowing.category == ForeshadowingCategory.MYSTERY
        assert foreshadowing.importance == 5
        assert foreshadowing.planting.subtlety_level == SubtletyLevel.HIGH
        assert foreshadowing.status == ForeshadowingStatus.PLANNED
        assert isinstance(foreshadowing.expected_reader_reaction, ReaderReaction)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_create_revelation_foreshadowing(self, extractor: object) -> None:
        """啓示系伏線作成のテスト"""
        foreshadowing = extractor._create_revelation_foreshadowing(
            revelation="主人公の正体が明かされる", index=1, total_chapters=3
        )

        assert foreshadowing is not None
        assert foreshadowing.category == ForeshadowingCategory.MAIN
        assert foreshadowing.importance == 4
        assert foreshadowing.planting.subtlety_level == SubtletyLevel.MEDIUM

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_create_character_foreshadowing(self, extractor: object) -> None:
        """キャラクター伏線作成のテスト"""
        foreshadowing = extractor._create_character_foreshadowing(character_name="ヒロイン", hidden_aspect="実は敵の妹")

        assert foreshadowing is not None
        assert foreshadowing.category == ForeshadowingCategory.CHARACTER
        assert "ヒロイン" in foreshadowing.title
        assert foreshadowing.importance == 3

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_create_secret_foreshadowing(self, extractor: object) -> None:
        """秘密系伏線作成のテスト"""
        foreshadowing = extractor._create_secret_foreshadowing(character_name="味方A", secret="裏切り者")

        assert foreshadowing is not None
        assert foreshadowing.category == ForeshadowingCategory.CHARACTER
        assert "味方A" in foreshadowing.title
        assert foreshadowing.importance == 4

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_create_thematic_foreshadowing(self, extractor: object) -> None:
        """テーマ系伏線作成のテスト"""
        foreshadowing = extractor._create_thematic_foreshadowing(theme="真実の探求", _theme_type="main")

        assert foreshadowing is not None
        assert foreshadowing.category == ForeshadowingCategory.THEMATIC
        assert "真実の探求" in foreshadowing.title
        assert foreshadowing.importance == 5

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_create_turning_point_foreshadowing(self, extractor: object) -> None:
        """転換点伏線作成のテスト"""
        foreshadowing = extractor._create_turning_point_foreshadowing(turning_point="仲間の裏切り", index=0)

        assert foreshadowing is not None
        assert foreshadowing.category == ForeshadowingCategory.MAIN
        assert "転換点" in foreshadowing.title
        assert foreshadowing.importance == 4

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_extract_from_chapter_plot(self, extractor: object, chapter_plot_data: object) -> None:
        """章別プロットからの抽出テスト"""
        result = extractor.extract_from_chapter_plot(chapter_plot_data)

        assert len(result) >= 3  # title + 2 scenes + 1 key_event
        assert any(f.planting.chapter == 2 for f in result)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_create_episode_foreshadowing(self, extractor: object) -> None:
        """エピソード伏線作成のテスト"""
        foreshadowing = extractor._create_episode_foreshadowing(episode_title="謎の手紙", episode_num=5, chapter_num=1)

        assert foreshadowing is not None
        assert "第5話" in foreshadowing.title
        assert foreshadowing.importance == 2
        assert foreshadowing.planting.subtlety_level == SubtletyLevel.LOW

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_create_scene_foreshadowing(self, extractor: object) -> None:
        """シーン伏線作成のテスト"""
        foreshadowing = extractor._create_scene_foreshadowing(
            scene_description="意味深な視線を交わす", episode_num=3, chapter_num=1
        )

        assert foreshadowing is not None
        assert "シーン" in foreshadowing.title
        assert foreshadowing.importance == 1
        assert foreshadowing.planting.subtlety_level == SubtletyLevel.LOW

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_foreshadowing_counter_increment(self, extractor: object) -> None:
        """伏線カウンターの増加テスト"""
        initial_count = extractor._foreshadowing_counter

        # 複数の伏線を作成
        extractor._create_mystery_foreshadowing("テスト", "説明", 1, 2)
        assert extractor._foreshadowing_counter == initial_count + 1

        extractor._create_character_foreshadowing("キャラ", "秘密")
        assert extractor._foreshadowing_counter == initial_count + 2

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_foreshadowing_id_format(self, extractor: object) -> None:
        """伏線IDのフォーマットテスト"""
        foreshadowing = extractor._create_mystery_foreshadowing("テスト", "説明", 1, 2)

        assert foreshadowing is not None
        assert isinstance(foreshadowing.id, ForeshadowingId)
        assert foreshadowing.id.value.startswith("F")
        assert len(foreshadowing.id.value) == 4  # F + 3桁の数字

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_episode_number_formatting(self, extractor: object) -> None:
        """エピソード番号のフォーマットテスト"""
        foreshadowing = extractor._create_mystery_foreshadowing("テスト", "説明", 1, 3)

        assert foreshadowing is not None
        assert foreshadowing.planting.episode == "第001話"
        assert foreshadowing.resolution.episode == "第025話"  # (3-1)*10+5

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_complex_master_plot_extraction(self, extractor: object) -> None:
        """複雑なマスタープロットからの抽出統合テスト"""
        complex_data = {
            "story_structure": {
                "opening": "謎の組織に追われる主人公",
                "development": {
                    "major_revelations": ["組織の正体", "主人公の過去"],
                    "turning_points": ["記憶の覚醒"],
                },
            },
            "characters": {
                "主人公": {"secrets": ["元組織のメンバー"]},
                "敵": {"hidden_aspects": ["主人公の恩人"]},
            },
            "themes": {"main": "正体と真実"},
        }

        result = extractor.extract_from_master_plot(complex_data)

        # 各カテゴリから少なくとも1つは抽出されている
        categories = {f.category for f in result}
        assert len(categories) >= 3

        # 重要度の高い伏線が含まれている
        high_importance = [f for f in result if f.importance >= 4]
        assert len(high_importance) > 0

        # 適切なサブトレティレベルが設定されている
        subtlety_levels = {f.planting.subtlety_level for f in result}
        assert SubtletyLevel.HIGH in subtlety_levels or SubtletyLevel.MEDIUM in subtlety_levels
