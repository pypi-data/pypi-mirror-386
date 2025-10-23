#!/usr/bin/env python3
"""章別プロット変更時の整合性管理テスト

マイナーバージョンアップでの詳細な影響分析


仕様書: SPEC-UNIT-TEST
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

import pytest

from noveler.application.use_cases.chapter_consistency_interactive_confirmation import (
    ChapterConsistencyInteractiveConfirmation,
)
from noveler.application.use_cases.chapter_plot_consistency_orchestrator import (
    ChapterPlotConsistencyOrchestrator,
)
from noveler.domain.versioning.entities import (
    ChapterForeshadowingAnalyzer,
    ChapterPlotImpactAnalyzer,
    ChapterSpecificEpisodeUpdater,
)

# PathManager統一パス管理システムを使用(事前にパスを設定)
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/を追加
from noveler.infrastructure.utils.path_manager import ensure_imports

ensure_imports()


class TestChapterPlotImpactAnalyzer(unittest.TestCase):
    """章別プロット影響分析器のテスト"""

    @pytest.mark.spec("SPEC-CHAPTER_PLOT_CONSISTENCY-ANALYZE_SINGLE_CHAPT")
    def test_analyze_single_chapter_impact(self) -> None:
        """単一章変更時の影響分析"""
        # Arrange
        analyzer = ChapterPlotImpactAnalyzer()
        changed_file = "20_プロット/章別プロット/chapter03.yaml"

        # Act
        impact = analyzer.analyze_chapter_impact(changed_file)

        # Assert
        assert impact.affected_chapter == 3
        assert impact.chapter_name == "ch03"
        assert impact.requires_episode_review
        assert impact.requires_foreshadowing_review
        assert "chapter_specific" in impact.impact_scope

    @pytest.mark.spec("SPEC-CHAPTER_PLOT_CONSISTENCY-ANALYZE_MULTIPLE_CHA")
    def test_analyze_multiple_chapters_impact(self) -> None:
        """複数章変更時の影響分析"""
        # Arrange
        analyzer = ChapterPlotImpactAnalyzer()
        changed_files = [
            "20_プロット/章別プロット/chapter03.yaml",
            "20_プロット/章別プロット/chapter04.yaml",
        ]

        # Act
        impact = analyzer.analyze_multiple_chapters_impact(changed_files)

        # Assert
        assert impact.affected_chapters == [3, 4]
        assert len(impact.chapter_impacts) == 2
        assert "multi_chapter" in impact.impact_scope


class TestChapterSpecificEpisodeUpdater(unittest.TestCase):
    """章固有の話数更新器のテスト"""

    @pytest.mark.spec("SPEC-CHAPTER_PLOT_CONSISTENCY-UPDATE_CHAPTER_SPECI")
    def test_update_chapter_specific_episodes(self) -> None:
        """特定章の話数のみ更新"""
        # Arrange
        updater = ChapterSpecificEpisodeUpdater()
        episodes_data = {
            "010": {"status": "PUBLISHED", "chapter": 2},
            "011": {"status": "PUBLISHED", "chapter": 3},
            "012": {"status": "PUBLISHED", "chapter": 3},
            "013": {"status": "PUBLISHED", "chapter": 4},
        }
        affected_chapter = 3

        # Act
        updated_data = updater.update_chapter_episodes(
            episodes_data,
            affected_chapter,
            "v1.1.0",
            "ch03プロット変更",
        )

        # Assert
        # ch03のみ更新される
        assert updated_data["010"]["status"] == "PUBLISHED"  # ch02は変更なし
        assert updated_data["011"]["status"] == "REVISION_NEEDED"  # ch03は更新
        assert updated_data["012"]["status"] == "REVISION_NEEDED"  # ch03は更新
        assert updated_data["013"]["status"] == "PUBLISHED"  # ch04は変更なし

        # バージョン情報が記録される
        assert updated_data["011"]["plot_version_at_revision"] == "v1.1.0"
        assert updated_data["012"]["plot_version_at_revision"] == "v1.1.0"


class TestChapterForeshadowingAnalyzer(unittest.TestCase):
    """章別伏線分析器のテスト"""

    @pytest.mark.spec("SPEC-CHAPTER_PLOT_CONSISTENCY-ANALYZE_CHAPTER_SPEC")
    def test_analyze_chapter_specific_foreshadowing(self) -> None:
        """特定章に関連する伏線の分析"""
        # Arrange
        analyzer = ChapterForeshadowingAnalyzer()
        foreshadowing_data = {
            "foreshadow_001": {
                "target_chapter": 3,
                "resolution_chapter": 5,
                "status": "ACTIVE",
            },
            "foreshadow_002": {
                "target_chapter": 2,
                "resolution_chapter": 3,
                "status": "RESOLVED",
            },
            "foreshadow_003": {
                "target_chapter": 4,
                "resolution_chapter": 6,
                "status": "ACTIVE",
            },
        }
        affected_chapter = 3

        # Act
        impact = analyzer.analyze_chapter_foreshadowing(
            foreshadowing_data,
            affected_chapter,
        )

        # Assert
        # ch03に関連する伏線(target or resolution)を特定
        assert len(impact.affected_foreshadowing) == 2
        assert "foreshadow_001" in impact.affected_foreshadowing  # target_chapter: 3
        assert "foreshadow_002" in impact.affected_foreshadowing  # resolution_chapter: 3
        assert "foreshadow_003" not in impact.affected_foreshadowing  # ch03と無関係

        # 推奨アクションが生成される
        assert "ch03" in impact.review_recommendation


class TestChapterPlotConsistencyOrchestrator(unittest.TestCase):
    """章別プロット整合性オーケストレータのテスト"""

    def setUp(self) -> None:
        """テストセットアップ"""
        # ChapterPlotConsistencyOrchestrator is imported at top-level

        self.mock_chapter_analyzer = Mock()
        self.mock_episode_updater = Mock()
        self.mock_foreshadow_analyzer = Mock()
        self.mock_file_manager = Mock()

        self.orchestrator = ChapterPlotConsistencyOrchestrator(
            self.mock_chapter_analyzer,
            self.mock_episode_updater,
        )

        # 依存性注入
        self.orchestrator.file_manager = self.mock_file_manager
        self.orchestrator.foreshadow_analyzer = self.mock_foreshadow_analyzer

    @pytest.mark.spec("SPEC-CHAPTER_PLOT_CONSISTENCY-EXECUTE_SINGLE_CHAPT")
    def test_execute_single_chapter_consistency_update(self) -> None:
        """単一章の整合性更新実行"""
        # Arrange
        version_change = {
            "type": "minor",
            "to": "v1.1.0",
            "changed_files": ["20_プロット/章別プロット/chapter03.yaml"],
        }

        mock_impact = Mock()
        mock_impact.affected_chapter = 3
        mock_impact.requires_episode_review = True
        mock_impact.requires_foreshadowing_review = True

        self.mock_chapter_analyzer.analyze_chapter_impact.return_value = mock_impact
        self.mock_file_manager.load_episodes_data.return_value = {}
        self.mock_file_manager.load_foreshadowing_data.return_value = {}

        # Act
        result = self.orchestrator.execute_chapter_consistency_update(version_change)

        # Assert
        assert result.success
        self.mock_chapter_analyzer.analyze_chapter_impact.assert_called_once()
        self.mock_episode_updater.update_chapter_episodes.assert_called_once()
        self.mock_foreshadow_analyzer.analyze_chapter_foreshadowing.assert_called_once()

        # 更新サマリーが生成される(複数の文字列にわたって検証)
        update_summary_text = " ".join(result.update_summary)
        assert "ch03" in update_summary_text

    @pytest.mark.spec("SPEC-CHAPTER_PLOT_CONSISTENCY-EXECUTE_MULTIPLE_CHA")
    def test_execute_multiple_chapters_consistency_update(self) -> None:
        """複数章の整合性更新実行"""
        # Arrange
        version_change = {
            "type": "minor",
            "to": "v1.2.0",
            "changed_files": [
                "20_プロット/章別プロット/chapter03.yaml",
                "20_プロット/章別プロット/chapter04.yaml",
            ],
        }

        mock_impact = Mock()
        mock_impact.affected_chapters = [3, 4]
        mock_impact.chapter_impacts = [Mock(), Mock()]

        self.mock_chapter_analyzer.analyze_multiple_chapters_impact.return_value = mock_impact
        self.mock_file_manager.load_episodes_data.return_value = {}
        self.mock_file_manager.load_foreshadowing_data.return_value = {}

        # Act
        result = self.orchestrator.execute_chapter_consistency_update(version_change)

        # Assert
        assert result.success
        self.mock_chapter_analyzer.analyze_multiple_chapters_impact.assert_called_once()
        # 複数章の場合は各章ごとに更新処理が呼ばれる
        assert self.mock_episode_updater.update_chapter_episodes.call_count == 2


class TestChapterConsistencyInteractiveConfirmation(unittest.TestCase):
    """章別整合性インタラクティブ確認のテスト"""

    @pytest.mark.spec("SPEC-CHAPTER_PLOT_CONSISTENCY-CONFIRM_SINGLE_CHAPT")
    def test_confirm_single_chapter_updates(self) -> None:
        """単一章更新の確認"""
        # Arrange
        confirmation = ChapterConsistencyInteractiveConfirmation()
        chapter_impact = {
            "affected_chapter": 3,
            "affected_episodes": 5,
            "affected_foreshadowing": 2,
            "chapter_name": "ch03",
        }

        def mock_input_handler(prompt) -> str:
            if "ch03の整合性更新を実行しますか" in prompt:
                return "Y"
            return "Y"

        # Act
        result = confirmation.confirm_chapter_updates(
            chapter_impact,
            mock_input_handler,
        )

        # Assert
        assert result.approved
        assert "ch03" in result.message

    @pytest.mark.spec("SPEC-CHAPTER_PLOT_CONSISTENCY-CONFIRM_MULTIPLE_CHA")
    def test_confirm_multiple_chapters_updates(self) -> None:
        """複数章更新の確認"""
        # Arrange
        confirmation = ChapterConsistencyInteractiveConfirmation()
        chapters_impact = {
            "affected_chapters": [3, 4],
            "total_affected_episodes": 8,
            "total_affected_foreshadowing": 3,
        }

        def mock_input_handler(prompt) -> str:
            if "複数章の整合性更新を実行しますか" in prompt:
                return "Y"
            return "Y"

        # Act
        result = confirmation.confirm_multiple_chapters_updates(
            chapters_impact,
            mock_input_handler,
        )

        # Assert
        assert result.approved
        assert "第3-4章" in result.message


if __name__ == "__main__":
    unittest.main()
