"""伏線・章別影響分析機能のテスト

TDD準拠テスト - Group 3: 伏線・章別影響分析機能
- ForeshadowingImpactAnalyzer
- ChapterPlotImpactAnalyzer


仕様書: SPEC-UNIT-TEST
"""

import pytest

from noveler.domain.versioning.entities import (
    ChapterPlotImpactAnalyzer,
    ForeshadowingImpactAnalyzer,
)


class TestForeshadowingImpactAnalyzer:
    """ForeshadowingImpactAnalyzerのテストクラス"""

    @pytest.fixture
    def foreshadowing_analyzer(self) -> ForeshadowingImpactAnalyzer:
        """伏線影響分析器"""
        return ForeshadowingImpactAnalyzer()

    @pytest.fixture
    def foreshadowing_data(self) -> dict:
        """伏線データサンプル"""
        return {
            "foreshadow_001": {"target_chapter": 1, "resolution_chapter": 3, "description": "主人公の能力覚醒"},
            "foreshadow_002": {"target_chapter": 2, "resolution_chapter": 4, "description": "敵の正体"},
            "foreshadow_003": {"target_chapter": 5, "resolution_chapter": 6, "description": "隠された真実"},
        }

    def test_analyze_foreshadowing_validity_target_chapter_affected(
        self, foreshadowing_analyzer: ForeshadowingImpactAnalyzer, foreshadowing_data: dict
    ) -> None:
        """対象章が影響を受ける場合の伏線有効性分析テスト"""
        affected_chapters = [1]

        impact = foreshadowing_analyzer.analyze_foreshadowing_validity(foreshadowing_data, affected_chapters)

        assert len(impact.potentially_invalidated) == 1
        assert "foreshadow_001" in impact.potentially_invalidated
        assert any("第1-3章の構成変更により伏線の見直しが必要" in rec for rec in impact.review_recommendations)

    def test_analyze_foreshadowing_validity_resolution_chapter_affected(
        self, foreshadowing_analyzer: ForeshadowingImpactAnalyzer, foreshadowing_data: dict
    ) -> None:
        """解決章が影響を受ける場合の伏線有効性分析テスト"""
        affected_chapters = [4]

        impact = foreshadowing_analyzer.analyze_foreshadowing_validity(foreshadowing_data, affected_chapters)

        assert len(impact.potentially_invalidated) == 1
        assert "foreshadow_002" in impact.potentially_invalidated
        assert any("第2-4章の構成変更により伏線の見直しが必要" in rec for rec in impact.review_recommendations)

    def test_analyze_foreshadowing_validity_multiple_chapters_affected(
        self, foreshadowing_analyzer: ForeshadowingImpactAnalyzer, foreshadowing_data: dict
    ) -> None:
        """複数章が影響を受ける場合の伏線有効性分析テスト"""
        affected_chapters = [1, 2, 3]

        impact = foreshadowing_analyzer.analyze_foreshadowing_validity(foreshadowing_data, affected_chapters)

        assert len(impact.potentially_invalidated) == 2
        assert "foreshadow_001" in impact.potentially_invalidated
        assert "foreshadow_002" in impact.potentially_invalidated
        assert "foreshadow_003" not in impact.potentially_invalidated

    def test_analyze_foreshadowing_validity_no_affected_foreshadowing(
        self, foreshadowing_analyzer: ForeshadowingImpactAnalyzer, foreshadowing_data: dict
    ) -> None:
        """影響を受ける伏線がない場合のテスト"""
        affected_chapters = [10]  # 存在しない章

        impact = foreshadowing_analyzer.analyze_foreshadowing_validity(foreshadowing_data, affected_chapters)

        assert len(impact.potentially_invalidated) == 0
        assert len(impact.review_recommendations) == 0

    def test_analyze_foreshadowing_validity_empty_data(
        self, foreshadowing_analyzer: ForeshadowingImpactAnalyzer
    ) -> None:
        """空の伏線データでのテスト"""
        foreshadowing_data = {}
        affected_chapters = [1, 2]

        impact = foreshadowing_analyzer.analyze_foreshadowing_validity(foreshadowing_data, affected_chapters)

        assert len(impact.potentially_invalidated) == 0
        assert len(impact.review_recommendations) == 0

    def test_analyze_foreshadowing_validity_comprehensive_recommendation(
        self, foreshadowing_analyzer: ForeshadowingImpactAnalyzer, foreshadowing_data: dict
    ) -> None:
        """包括的推奨アクション生成テスト"""
        affected_chapters = [1, 3, 4]

        impact = foreshadowing_analyzer.analyze_foreshadowing_validity(foreshadowing_data, affected_chapters)

        # 影響を受ける伏線の個別推奨に加えて、包括的推奨も生成される
        assert len(impact.potentially_invalidated) == 2
        assert any("第1-4章の構成変更により伏線の見直しが必要" in rec for rec in impact.review_recommendations)


class TestChapterPlotImpactAnalyzer:
    """ChapterPlotImpactAnalyzerのテストクラス"""

    @pytest.fixture
    def chapter_analyzer(self) -> ChapterPlotImpactAnalyzer:
        """章別プロット影響分析器"""
        return ChapterPlotImpactAnalyzer()

    def test_analyze_chapter_impact_single_chapter(self, chapter_analyzer: ChapterPlotImpactAnalyzer) -> None:
        """単一章影響分析テスト"""
        changed_file = "20_プロット/章別プロット/chapter03.yaml"

        impact = chapter_analyzer.analyze_chapter_impact(changed_file)

        assert impact.affected_chapter == 3

    def test_analyze_multiple_chapters_impact(self, chapter_analyzer: ChapterPlotImpactAnalyzer) -> None:
        """複数章影響分析テスト"""
        changed_files = [
            "20_プロット/章別プロット/chapter01.yaml",
            "20_プロット/章別プロット/chapter05.yaml",
            "40_原稿/第001話.md",  # これは章別プロットではない
        ]

        impact = chapter_analyzer.analyze_multiple_chapters_impact(changed_files)

        assert set(impact.chapter_numbers) == {1, 5}

    def test_analyze_multiple_chapters_impact_no_chapters(self, chapter_analyzer: ChapterPlotImpactAnalyzer) -> None:
        """章別プロットファイル変更なしの影響分析テスト"""
        changed_files = ["40_原稿/第001話.md", "README.md"]

        # 章別プロットファイルがない場合は例外が発生する
        with pytest.raises(Exception, match=".*"):  # DomainException: 少なくとも1つの章番号が必要です
            chapter_analyzer.analyze_multiple_chapters_impact(changed_files)

    def test_extract_chapter_number_standard_format(self, chapter_analyzer: ChapterPlotImpactAnalyzer) -> None:
        """標準フォーマットからの章番号抽出テスト"""
        test_cases = [
            ("20_プロット/章別プロット/chapter01.yaml", 1),
            ("20_プロット/章別プロット/chapter10.yaml", 10),
            ("20_プロット/章別プロット/chapter99.yaml", 99),
            ("20_プロット/全体構成.yaml", 1),  # マッチしない場合はデフォルト1
            ("40_原稿/第001話.md", 1),  # マッチしない場合はデフォルト1
        ]

        for file_path, expected_chapter in test_cases:
            result = chapter_analyzer._extract_chapter_number(file_path)
            assert result == expected_chapter, f"Failed for {file_path}: expected {expected_chapter}, got {result}"

    def test_analyze_chapter_impact_edge_cases(self, chapter_analyzer: ChapterPlotImpactAnalyzer) -> None:
        """章影響分析のエッジケーステスト"""
        # 章番号が含まれていないファイル
        changed_file = "20_プロット/全体構成.yaml"

        impact = chapter_analyzer.analyze_chapter_impact(changed_file)

        # マッチしない場合はデフォルト1が返される
        assert impact.affected_chapter == 1
