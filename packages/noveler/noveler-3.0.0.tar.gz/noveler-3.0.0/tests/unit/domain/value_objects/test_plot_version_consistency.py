#!/usr/bin/env python3
"""プロットバージョン整合性管理のテスト

メジャーバージョンアップ時の関連ファイル整合性チェック


仕様書: SPEC-DOMAIN-VALUE-OBJECTS
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

from noveler.application.use_cases.consistency_update_orchestrator import ConsistencyUpdateOrchestrator
from noveler.application.use_cases.interactive_consistency_confirmation import InteractiveConsistencyConfirmation
from noveler.domain.versioning.entities import (
    EpisodeStatusUpdater,
    ForeshadowingImpactAnalyzer,
    PlotVersionConsistencyAnalyzer,
)

# PathManager統一パス管理システムを使用(事前にパスを設定)
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/を追加
from noveler.infrastructure.utils.path_manager import ensure_imports

ensure_imports()


class TestPlotVersionConsistencyAnalyzer(unittest.TestCase):
    """プロットバージョン整合性分析器のテスト"""

    def test_major_version_impact_analysis(self) -> None:
        """メジャーバージョンアップの影響分析"""
        # Arrange
        analyzer = PlotVersionConsistencyAnalyzer()
        version_change = {
            "type": "major",
            "from": "v1.0.0",
            "to": "v2.0.0",
            "changes": ["エンディング全面変更", "キャラクター削除"],
            "affected_chapters": [4, 5],
        }

        # Act
        impact = analyzer.analyze_consistency_impact(version_change)

        # Assert
        assert impact.requires_episode_status_update
        assert impact.requires_foreshadowing_review
        assert impact.requires_character_growth_review
        assert len(impact.affected_management_files) == 4
        assert "話数管理.yaml" in impact.affected_management_files
        assert "伏線管理.yaml" in impact.affected_management_files
        assert "キャラ成長.yaml" in impact.affected_management_files
        assert "重要シーン.yaml" in impact.affected_management_files

    def test_minor_version_impact_analysis(self) -> None:
        """マイナーバージョンアップの影響分析"""
        # Arrange
        analyzer = PlotVersionConsistencyAnalyzer()
        version_change = {
            "type": "minor",
            "from": "v1.0.0",
            "to": "v1.1.0",
            "changes": ["ch03の詳細調整"],
            "affected_chapters": [3],
        }

        # Act
        impact = analyzer.analyze_consistency_impact(version_change)

        # Assert
        assert impact.requires_episode_status_update
        assert not impact.requires_foreshadowing_review
        assert not impact.requires_character_growth_review
        assert len(impact.affected_management_files) == 1
        assert "話数管理.yaml" in impact.affected_management_files


class TestEpisodeStatusUpdater(unittest.TestCase):
    """話数管理ステータス更新器のテスト"""

    def test_mark_episodes_for_revision(self) -> None:
        """影響話数のリビジョン必要マーク"""

        # # Arrange # Moved to top-level
        updater = EpisodeStatusUpdater()
        affected_chapters = [3, 4]
        episodes_data = {
            "015": {"status": "PUBLISHED", "chapter": 3},
            "016": {"status": "PUBLISHED", "chapter": 3},
            "017": {"status": "PUBLISHED", "chapter": 4},
            "018": {"status": "DRAFT", "chapter": 5},
        }

        # Act
        updated_data = updater.mark_episodes_for_revision(
            episodes_data,
            affected_chapters,
            "v2.0.0",
        )

        # Assert
        # ch03・ch04の公開済み話数がリビジョン必要に
        assert updated_data["015"]["status"] == "REVISION_NEEDED"
        assert updated_data["016"]["status"] == "REVISION_NEEDED"
        assert updated_data["017"]["status"] == "REVISION_NEEDED"
        # ch05のドラフトは影響なし
        assert updated_data["018"]["status"] == "DRAFT"

        # バージョン情報が記録される
        assert updated_data["015"]["plot_version_at_revision"] == "v2.0.0"
        assert updated_data["016"]["plot_version_at_revision"] == "v2.0.0"


class TestForeshadowingImpactAnalyzer(unittest.TestCase):
    """伏線影響分析器のテスト"""

    def test_analyze_foreshadowing_validity(self) -> None:
        """伏線の有効性分析"""

        # # Arrange # Moved to top-level
        analyzer = ForeshadowingImpactAnalyzer()
        foreshadowing_data = {
            "foreshadow_001": {
                "target_chapter": 5,
                "resolution_chapter": 8,
                "status": "ACTIVE",
            },
            "foreshadow_002": {
                "target_chapter": 3,
                "resolution_chapter": 4,
                "status": "RESOLVED",
            },
        }
        affected_chapters = [4, 5]

        # Act
        impact = analyzer.analyze_foreshadowing_validity(
            foreshadowing_data,
            affected_chapters,
        )

        # Assert
        # 影響を受ける伏線を特定
        assert len(impact.potentially_invalidated) == 2
        assert "foreshadow_001" in impact.potentially_invalidated
        assert "foreshadow_002" in impact.potentially_invalidated

        # レビュー推奨アクション
        assert "第4-5章の構成変更により伏線の見直しが必要" in impact.review_recommendations


class TestConsistencyUpdateOrchestrator(unittest.TestCase):
    """整合性更新オーケストレータのテスト"""

    def setUp(self) -> None:
        """テストセットアップ"""

        self.mock_episode_updater = Mock()
        self.mock_foreshadow_analyzer = Mock()
        self.mock_file_manager = Mock()

        self.orchestrator = ConsistencyUpdateOrchestrator(
            self.mock_episode_updater,
            self.mock_foreshadow_analyzer,
            self.mock_file_manager,
        )

    def test_execute_major_version_consistency_update(self) -> None:
        """メジャーバージョン整合性更新の実行"""
        # Arrange
        version_change = {
            "type": "major",
            "to": "v2.0.0",
            "affected_chapters": [4, 5],
        }

        self.mock_file_manager.load_episodes_data.return_value = {}
        self.mock_file_manager.load_foreshadowing_data.return_value = {}
        impact_mock = Mock()
        impact_mock.potentially_invalidated = ['foreshadow_001']
        impact_mock.review_recommendations = ['伏線管理レビューを実施']
        self.mock_foreshadow_analyzer.analyze_foreshadowing_validity.return_value = impact_mock

        # Act
        result = self.orchestrator.execute_consistency_update(version_change)

        # Assert
        assert result.success
        self.mock_episode_updater.mark_episodes_for_revision.assert_called_once()
        self.mock_foreshadow_analyzer.analyze_foreshadowing_validity.assert_called_once()
        self.mock_file_manager.save_episodes_data.assert_called_once()

        # 更新サマリーが生成される
        assert "話数管理ステータスを更新" in result.update_summary
        assert "伏線管理にレビューノートを追加" in result.update_summary

    def test_execute_minor_version_consistency_update(self) -> None:
        """マイナーバージョン整合性更新の実行"""
        # Arrange
        version_change = {
            "type": "minor",
            "to": "v1.1.0",
            "affected_chapters": [3],
        }

        self.mock_file_manager.load_episodes_data.return_value = {}

        # Act
        result = self.orchestrator.execute_consistency_update(version_change)

        # Assert
        assert result.success
        self.mock_episode_updater.mark_episodes_for_revision.assert_called_once()
        # マイナーバージョンでは伏線分析はスキップ
        self.mock_foreshadow_analyzer.analyze_foreshadowing_validity.assert_not_called()


class TestInteractiveConsistencyConfirmation(unittest.TestCase):
    """インタラクティブ整合性確認のテスト"""

    def test_user_confirms_all_updates(self) -> None:
        """ユーザーが全更新を承認"""
        # InteractiveConsistencyConfirmation is imported at top-level

        # Arrange
        confirmation = InteractiveConsistencyConfirmation()
        impact_summary = {
            "affected_episodes": 5,
            "affected_foreshadowing": 2,
            "requires_review": ["話数管理", "伏線管理"],
        }

        def mock_input_handler(prompt) -> str:
            if (
                "整合性更新を実行しますか" in prompt
                or "話数管理を更新しますか" in prompt
                or "伏線管理レビューを記録しますか" in prompt
            ):
                return "Y"
            return "Y"

        # Act
        result = confirmation.confirm_consistency_updates(
            impact_summary,
            mock_input_handler,
        )

        # Assert
        assert result.approved
        assert result.update_episode_status
        assert result.update_foreshadowing_notes
        assert result.message == "すべての整合性更新が承認されました"

    def test_user_declines_updates(self) -> None:
        """ユーザーが更新を拒否"""
        # Arrange
        confirmation = InteractiveConsistencyConfirmation()
        impact_summary = {
            "affected_episodes": 5,
            "affected_foreshadowing": 2,
        }

        def mock_input_handler(prompt) -> str:
            return "N"

        # Act
        result = confirmation.confirm_consistency_updates(
            impact_summary,
            mock_input_handler,
        )

        # Assert
        assert not result.approved
        assert "整合性更新をスキップ" in result.message


if __name__ == "__main__":
    unittest.main()
