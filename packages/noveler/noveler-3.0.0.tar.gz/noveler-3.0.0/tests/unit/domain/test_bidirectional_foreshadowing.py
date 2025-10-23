#!/usr/bin/env python3
"""双方向伏線管理のテスト

TDD: RED段階 - 失敗するテストを先に作成


仕様書: SPEC-UNIT-TEST
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

import pytest

from noveler.application.use_cases.bidirectional_interactive_confirmation import (
    BidirectionalInteractiveConfirmation,
)
from noveler.application.use_cases.enhanced_chapter_consistency_orchestrator import (
    EnhancedChapterConsistencyOrchestrator,
)
from noveler.domain.versioning.entities import (
    BidirectionalForeshadowingAnalyzer,
    ForeshadowingStatusUpdater,
)
from noveler.domain.versioning.value_objects import BidirectionalForeshadowingImpact

# PathManager統一パス管理システムを使用(事前にパスを設定)
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/を追加
from noveler.infrastructure.utils.path_manager import ensure_imports

ensure_imports()


class TestBidirectionalForeshadowingAnalyzer(unittest.TestCase):
    """双方向伏線分析器のテスト"""

    @pytest.mark.spec("SPEC-BIDIRECTIONAL_FORESHADOWING-ANALYZE_SETUP_CHAPTE")
    def test_analyze_setup_chapter_modification(self) -> None:
        """仕込み章変更時の影響分析"""
        # Arrange
        analyzer = BidirectionalForeshadowingAnalyzer()
        foreshadowing_data = {
            "foreshadow_001": {
                "description": "主人公の秘密",
                "target_chapter": 3,  # 仕込み章
                "resolution_chapter": 7,  # 回収章
                "status": "ACTIVE",
            },
            "foreshadow_002": {
                "description": "謎のアイテム",
                "target_chapter": 3,  # 仕込み章
                "resolution_chapter": 9,  # 回収章
                "status": "ACTIVE",
            },
            "foreshadow_003": {
                "description": "別の伏線",
                "target_chapter": 5,
                "resolution_chapter": 8,
                "status": "ACTIVE",
            },
        }
        affected_chapter = 3  # ch03を変更

        # Act
        impact = analyzer.analyze_bidirectional_impact(foreshadowing_data, affected_chapter)

        # Assert
        # ch03が仕込み章の伏線を検出
        assert len(impact.setup_modified) == 2
        assert ("foreshadow_001", 7) in impact.setup_modified
        assert ("foreshadow_002", 9) in impact.setup_modified

        # ch03が回収章の伏線はなし
        assert len(impact.resolution_modified) == 0

        # 双方向影響あり
        assert impact.has_bidirectional_impact

    @pytest.mark.spec("SPEC-BIDIRECTIONAL_FORESHADOWING-ANALYZE_RESOLUTION_C")
    def test_analyze_resolution_chapter_modification(self) -> None:
        """回収章変更時の影響分析"""
        # Arrange
        analyzer = BidirectionalForeshadowingAnalyzer()
        foreshadowing_data = {
            "foreshadow_001": {
                "description": "主人公の秘密",
                "target_chapter": 3,
                "resolution_chapter": 7,  # 回収章
                "status": "ACTIVE",
            },
            "foreshadow_002": {
                "description": "別の秘密",
                "target_chapter": 5,
                "resolution_chapter": 7,  # 回収章
                "status": "ACTIVE",
            },
        }
        affected_chapter = 7  # ch07を変更

        # Act
        impact = analyzer.analyze_bidirectional_impact(foreshadowing_data, affected_chapter)

        # Assert
        # ch07が回収章の伏線を検出
        assert len(impact.resolution_modified) == 2
        assert ("foreshadow_001", 3) in impact.resolution_modified
        assert ("foreshadow_002", 5) in impact.resolution_modified

        # ch07が仕込み章の伏線はなし
        assert len(impact.setup_modified) == 0

    @pytest.mark.spec("SPEC-BIDIRECTIONAL_FORESHADOWING-GET_REVERSE_CHECK_CH")
    def test_get_reverse_check_chapters(self) -> None:
        """逆方向チェックが必要な章の取得"""
        # Arrange
        analyzer = BidirectionalForeshadowingAnalyzer()
        impact = BidirectionalForeshadowingImpact(3)
        impact.add_setup_modified("foreshadow_001", 7)
        impact.add_setup_modified("foreshadow_002", 9)

        # Act
        chapters_to_check = analyzer.get_reverse_check_chapters(impact)

        # Assert
        # 仕込み(ch03)が変更されたので、回収章(7,9)をチェック
        assert chapters_to_check == {7, 9}
        # 変更された章自体(3)は含まない
        assert 3 not in chapters_to_check


class TestForeshadowingStatusUpdater(unittest.TestCase):
    """伏線ステータス更新器のテスト"""

    @pytest.mark.spec("SPEC-BIDIRECTIONAL_FORESHADOWING-UPDATE_STATUS_FOR_SE")
    def test_update_status_for_setup_modification(self) -> None:
        """仕込み章変更時のステータス更新"""
        # Arrange
        updater = ForeshadowingStatusUpdater()
        foreshadowing_data = {
            "foreshadow_001": {
                "description": "主人公の秘密",
                "target_chapter": 3,
                "resolution_chapter": 7,
                "status": "ACTIVE",
            },
        }

        impact = BidirectionalForeshadowingImpact(3)
        impact.add_setup_modified("foreshadow_001", 7)

        # Act
        updated_data = updater.update_foreshadowing_status(
            foreshadowing_data,
            impact,
            "v1.2.0",
        )

        # Assert
        # ステータスがREVIEW_REQUIREDに変更
        assert updated_data["foreshadow_001"]["status"] == "REVIEW_REQUIRED"

        # 章別影響履歴が追加
        impacts = updated_data["foreshadow_001"]["chapter_impacts"]
        assert len(impacts) == 1
        assert impacts[0]["version"] == "v1.2.0"
        assert impacts[0]["affected_chapter"] == 3
        assert impacts[0]["impact_type"] == "setup_modified"
        assert impacts[0]["severity"] == "minor"  # 仕込み変更はminor

        # ステータス履歴が追加
        history = updated_data["foreshadow_001"]["status_history"]
        assert len(history) == 1
        assert history[0]["status"] == "REVIEW_REQUIRED"
        assert "第3章の伏線仕込みの変更" in history[0]["reason"]

    @pytest.mark.spec("SPEC-BIDIRECTIONAL_FORESHADOWING-UPDATE_STATUS_FOR_RE")
    def test_update_status_for_resolution_modification(self) -> None:
        """回収章変更時のステータス更新(重要度高)"""
        # Arrange
        updater = ForeshadowingStatusUpdater()
        foreshadowing_data = {
            "foreshadow_001": {
                "description": "主人公の秘密",
                "target_chapter": 3,
                "resolution_chapter": 7,
                "status": "ACTIVE",
            },
        }

        impact = BidirectionalForeshadowingImpact(7)
        impact.add_resolution_modified("foreshadow_001", 3)

        # Act
        updated_data = updater.update_foreshadowing_status(
            foreshadowing_data,
            impact,
            "v1.2.0",
        )

        # Assert
        # 章別影響履歴の重要度がmajor
        impacts = updated_data["foreshadow_001"]["chapter_impacts"]
        assert impacts[0]["severity"] == "major"  # 回収変更はmajor
        assert impacts[0]["impact_type"] == "resolution_modified"

    @pytest.mark.spec("SPEC-BIDIRECTIONAL_FORESHADOWING-PRESERVE_EXISTING_IM")
    def test_preserve_existing_impacts(self) -> None:
        """既存の影響履歴を保持"""
        # Arrange
        updater = ForeshadowingStatusUpdater()
        foreshadowing_data = {
            "foreshadow_001": {
                "description": "主人公の秘密",
                "target_chapter": 3,
                "resolution_chapter": 7,
                "status": "REVIEW_REQUIRED",
                "chapter_impacts": [
                    {
                        "version": "v1.1.0",
                        "affected_chapter": 5,
                        "impact_type": "setup_modified",
                        "severity": "minor",
                    },
                ],
            },
        }

        impact = BidirectionalForeshadowingImpact(7)
        impact.add_resolution_modified("foreshadow_001", 3)

        # Act
        updated_data = updater.update_foreshadowing_status(
            foreshadowing_data,
            impact,
            "v1.2.0",
        )

        # Assert
        # 既存の影響履歴が保持され、新しい履歴が追加
        impacts = updated_data["foreshadow_001"]["chapter_impacts"]
        assert len(impacts) == 2
        assert impacts[0]["version"] == "v1.1.0"  # 既存
        assert impacts[1]["version"] == "v1.2.0"  # 新規


class TestEnhancedChapterConsistencyOrchestrator(unittest.TestCase):
    """拡張された章別整合性オーケストレータのテスト"""

    @pytest.mark.spec("SPEC-BIDIRECTIONAL_FORESHADOWING-EXECUTE_WITH_BIDIREC")
    def test_execute_with_bidirectional_analysis(self) -> None:
        """双方向分析を含む整合性更新実行"""
        # Arrange
        mock_chapter_analyzer = Mock()
        mock_episode_updater = Mock()
        mock_bidirectional_analyzer = Mock()
        mock_status_updater = Mock()
        mock_file_manager = Mock()

        orchestrator = EnhancedChapterConsistencyOrchestrator(
            mock_chapter_analyzer,
            mock_episode_updater,
            mock_bidirectional_analyzer,
            mock_status_updater,
            mock_file_manager,
        )

        version_change = {
            "type": "minor",
            "to": "v1.2.0",
            "changed_files": ["20_プロット/章別プロット/chapter03.yaml"],
        }

        # モックの設定
        mock_impact = Mock()
        mock_impact.affected_chapter = 3
        mock_impact.requires_episode_review = True
        mock_impact.requires_foreshadowing_review = True

        mock_chapter_analyzer.analyze_chapter_impact.return_value = mock_impact

        mock_bidirectional_impact = Mock()
        mock_bidirectional_impact.has_bidirectional_impact = True
        mock_bidirectional_impact.impact_summary = "ch03 - 仕込み変更: 2件"

        mock_bidirectional_analyzer.analyze_bidirectional_impact.return_value = mock_bidirectional_impact
        mock_bidirectional_analyzer.get_reverse_check_chapters.return_value = {7, 9}

        mock_file_manager.load_episodes_data.return_value = {}
        mock_file_manager.load_foreshadowing_data.return_value = {}

        # Act
        result = orchestrator.execute_chapter_consistency_update(version_change)

        # Assert
        assert result.success

        # 双方向分析が実行された
        mock_bidirectional_analyzer.analyze_bidirectional_impact.assert_called_once()

        # ステータス更新が実行された
        mock_status_updater.update_foreshadowing_status.assert_called_once()

        # 逆方向チェックが推奨に含まれる
        update_summary_text = " ".join(result.update_summary)
        assert "第7章, 第9章の確認も推奨" in update_summary_text

    @pytest.mark.spec("SPEC-BIDIRECTIONAL_FORESHADOWING-HANDLE_BOTH_SETUP_AN")
    def test_handle_both_setup_and_resolution_changes(self) -> None:
        """仕込みと回収の両方が影響する場合"""
        # Arrange
        orchestrator = EnhancedChapterConsistencyOrchestrator(
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            Mock(),
        )

        bidirectional_impact = Mock()
        bidirectional_impact.setup_modified = [("foreshadow_001", 7)]
        bidirectional_impact.resolution_modified = [("foreshadow_002", 3)]
        bidirectional_impact.impact_summary = "ch05 - 仕込み変更: 1件, 回収変更: 1件"

        # Act
        summary = orchestrator._create_bidirectional_summary(bidirectional_impact)

        # Assert
        assert "仕込み変更" in summary
        assert "回収変更" in summary
        assert "双方向" in summary


class TestBidirectionalInteractiveConfirmation(unittest.TestCase):
    """双方向伏線確認のインタラクティブテスト"""

    @pytest.mark.spec("SPEC-BIDIRECTIONAL_FORESHADOWING-CONFIRM_BIDIRECTIONA")
    def test_confirm_bidirectional_updates(self) -> None:
        """双方向更新の確認"""
        # Arrange
        confirmation = BidirectionalInteractiveConfirmation()
        impact_data = {
            "affected_chapter": 3,
            "setup_modified_count": 2,
            "resolution_modified_count": 0,
            "reverse_check_chapters": [7, 9],
            "impact_summary": "ch03 - 仕込み変更: 2件",
        }

        def mock_input_handler(prompt) -> str:
            if "逆方向チェックも実行しますか" in prompt:
                return "Y"
            return "Y"

        # Act
        result = confirmation.confirm_bidirectional_updates(
            impact_data,
            mock_input_handler,
        )

        # Assert
        assert result.approved
        assert result.include_reverse_check
        assert "第7章, 第9章" in result.message


if __name__ == "__main__":
    unittest.main()
