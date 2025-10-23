"""プロット管理機能のテスト

TDD準拠テスト - Group 2: プロット管理機能
- PlotCommitAnalyzer
- PlotVersionConsistencyAnalyzer
- EpisodeStatusUpdater


仕様書: SPEC-UNIT-TEST
"""

import pytest
pytestmark = pytest.mark.plot_episode

from noveler.domain.versioning.entities import (
    EpisodeStatusUpdater,
    PlotCommitAnalyzer,
    PlotVersionConsistencyAnalyzer,
)


class TestPlotCommitAnalyzer:
    """PlotCommitAnalyzerのテストクラス"""

    @pytest.fixture
    def plot_analyzer(self) -> PlotCommitAnalyzer:
        """プロットコミット分析器"""
        return PlotCommitAnalyzer()

    def test_analyze_commit_no_plot_changes(self, plot_analyzer: PlotCommitAnalyzer) -> None:
        """プロット変更なしの分析テスト"""
        changed_files = ["40_原稿/第001話.md", "README.md"]
        git_diff_content = "some changes in manuscript"

        analysis = plot_analyzer.analyze_commit(changed_files, git_diff_content)

        assert analysis.significance.level == "patch"
        assert analysis.significance.reason == "プロット変更なし"
        assert analysis.requires_versioning is False
        assert analysis.changed_files == changed_files

    def test_analyze_commit_major_structural_changes(self, plot_analyzer: PlotCommitAnalyzer) -> None:
        """メジャーな構造的変更の分析テスト"""
        changed_files = ["20_プロット/全体構成.yaml"]
        git_diff_content = "changed ending_type from happy to tragic"

        analysis = plot_analyzer.analyze_commit(changed_files, git_diff_content)

        assert analysis.significance.level == "major"
        assert analysis.significance.reason == "構造的変更"
        assert analysis.requires_versioning is True

    def test_analyze_commit_major_chapter_structural_changes(self, plot_analyzer: PlotCommitAnalyzer) -> None:
        """章別での重要な構造的変更の分析テスト"""
        changed_files = ["20_プロット/章別プロット/chapter01.yaml"]
        git_diff_content = "major climax restructuring and character_arc changes"

        analysis = plot_analyzer.analyze_commit(changed_files, git_diff_content)

        assert analysis.significance.level == "major"
        assert analysis.significance.reason == "重要な章別変更"
        assert analysis.requires_versioning is True

    def test_analyze_commit_minor_changes(self, plot_analyzer: PlotCommitAnalyzer) -> None:
        """軽微な変更の分析テスト"""
        changed_files = ["20_プロット/章別プロット/chapter02.yaml"]
        git_diff_content = "fixed typo in description and updated comment"

        analysis = plot_analyzer.analyze_commit(changed_files, git_diff_content)

        assert analysis.significance.level == "minor"
        assert analysis.significance.reason == "軽微な修正"
        assert analysis.requires_versioning is False

    def test_analyze_commit_moderate_chapter_changes(self, plot_analyzer: PlotCommitAnalyzer) -> None:
        """中程度の章別変更の分析テスト"""
        changed_files = ["20_プロット/章別プロット/chapter03.yaml"]
        git_diff_content = "updated plot progression and scene ordering"

        analysis = plot_analyzer.analyze_commit(changed_files, git_diff_content)

        assert analysis.significance.level == "minor"
        assert analysis.significance.reason == "章別プロット更新"
        assert analysis.requires_versioning is True

    def test_extract_plot_files(self, plot_analyzer: PlotCommitAnalyzer) -> None:
        """プロットファイル抽出テスト"""
        changed_files = ["20_プロット/全体構成.yaml", "30_設定集/キャラクター.yaml", "40_原稿/第001話.md"]

        plot_files = plot_analyzer._extract_plot_files(changed_files)

        expected_plot_files = ["20_プロット/全体構成.yaml", "30_設定集/キャラクター.yaml"]
        assert plot_files == expected_plot_files

    def test_has_structural_changes_true(self, plot_analyzer: PlotCommitAnalyzer) -> None:
        """構造的変更検出(True)テスト"""
        diff_content = "changed the main_plot structure and climax resolution"

        has_structural = plot_analyzer._has_structural_changes(diff_content)

        assert has_structural is True

    def test_has_structural_changes_false(self, plot_analyzer: PlotCommitAnalyzer) -> None:
        """構造的変更検出(False)テスト"""
        diff_content = "updated character background and scene descriptions"

        has_structural = plot_analyzer._has_structural_changes(diff_content)

        assert has_structural is False

    def test_is_minor_change_true(self, plot_analyzer: PlotCommitAnalyzer) -> None:
        """軽微変更検出(True)テスト"""
        diff_content = "fixed typo in description and corrected minor note"

        is_minor = plot_analyzer._is_minor_change(diff_content)

        assert is_minor is True

    def test_is_minor_change_false(self, plot_analyzer: PlotCommitAnalyzer) -> None:
        """軽微変更検出(False)テスト"""
        diff_content = "restructured plot flow and changed character relationships"

        is_minor = plot_analyzer._is_minor_change(diff_content)

        assert is_minor is False

    def test_is_major_plot_file_true(self, plot_analyzer: PlotCommitAnalyzer) -> None:
        """メジャープロットファイル判定(True)テスト"""
        plot_files = ["20_プロット/全体構成.yaml", "other_file.yaml"]

        is_major = plot_analyzer._is_major_plot_file(plot_files)

        assert is_major is True

    def test_is_major_plot_file_false(self, plot_analyzer: PlotCommitAnalyzer) -> None:
        """メジャープロットファイル判定(False)テスト"""
        plot_files = ["20_プロット/章別プロット/chapter01.yaml", "30_設定集/キャラクター.yaml"]

        is_major = plot_analyzer._is_major_plot_file(plot_files)

        assert is_major is False

    def test_analyze_commit_case_insensitive_keywords(self, plot_analyzer: PlotCommitAnalyzer) -> None:
        """大文字小文字を区別しないキーワード検出テスト"""
        changed_files = ["20_プロット/全体構成.yaml"]
        git_diff_content = "Changed ENDING_TYPE and updated Theme significantly"

        analysis = plot_analyzer.analyze_commit(changed_files, git_diff_content)

        assert analysis.significance.level == "major"
        assert analysis.significance.reason == "構造的変更"


class TestPlotVersionConsistencyAnalyzer:
    """PlotVersionConsistencyAnalyzerのテストクラス"""

    @pytest.fixture
    def consistency_analyzer(self) -> PlotVersionConsistencyAnalyzer:
        """プロットバージョン整合性分析器"""
        return PlotVersionConsistencyAnalyzer()

    def test_analyze_consistency_impact_major(self, consistency_analyzer: PlotVersionConsistencyAnalyzer) -> None:
        """メジャーバージョン変更の整合性影響分析テスト"""
        version_change = {"type": "major"}

        impact = consistency_analyzer.analyze_consistency_impact(version_change)

        assert impact.version_type == "major"
        assert impact.requires_episode_status_update is True
        assert impact.requires_foreshadowing_review is True
        assert impact.requires_character_growth_review is True
        assert impact.requires_important_scenes_review is True

    def test_analyze_consistency_impact_minor(self, consistency_analyzer: PlotVersionConsistencyAnalyzer) -> None:
        """マイナーバージョン変更の整合性影響分析テスト"""
        version_change = {"type": "minor"}

        impact = consistency_analyzer.analyze_consistency_impact(version_change)

        assert impact.version_type == "minor"
        assert impact.requires_episode_status_update is True
        assert impact.requires_foreshadowing_review is False
        assert impact.requires_character_growth_review is False
        assert impact.requires_important_scenes_review is False

    def test_analyze_consistency_impact_patch(self, consistency_analyzer: PlotVersionConsistencyAnalyzer) -> None:
        """パッチバージョン変更の整合性影響分析テスト"""
        version_change = {"type": "patch"}

        impact = consistency_analyzer.analyze_consistency_impact(version_change)

        assert impact.version_type == "patch"
        assert impact.requires_episode_status_update is True
        assert impact.requires_foreshadowing_review is False
        assert impact.requires_character_growth_review is False
        assert impact.requires_important_scenes_review is False


class TestEpisodeStatusUpdater:
    """EpisodeStatusUpdaterのテストクラス"""

    @pytest.fixture
    def episode_updater(self) -> EpisodeStatusUpdater:
        """話数管理ステータス更新器"""
        return EpisodeStatusUpdater()

    @pytest.fixture
    def episodes_data(self) -> dict:
        """話数データサンプル"""
        return {
            "episode_001": {"chapter": 1, "status": "PUBLISHED", "title": "第1話"},
            "episode_002": {"chapter": 2, "status": "PUBLISHED", "title": "第2話"},
            "episode_003": {"chapter": 1, "status": "DRAFT", "title": "第3話"},
            "episode_004": {"chapter": 3, "status": "PUBLISHED", "title": "第4話"},
        }

    def test_mark_episodes_for_revision_single_chapter(
        self, episode_updater: EpisodeStatusUpdater, episodes_data: dict
    ) -> None:
        """単一章の話数リビジョンマークテスト"""
        affected_chapters = [1]
        new_version = "v2.0.0"

        updated_data = episode_updater.mark_episodes_for_revision(episodes_data, affected_chapters, new_version)

        # episode_001 (chapter=1, PUBLISHED) がリビジョン必要に変更
        assert updated_data["episode_001"]["status"] == "REVISION_NEEDED"
        assert updated_data["episode_001"]["plot_version_at_revision"] == "v2.0.0"
        assert "プロットv2.0.0の影響により要確認" in updated_data["episode_001"]["revision_reason"]

        # episode_002 (chapter=2) は変更されない
        assert updated_data["episode_002"]["status"] == "PUBLISHED"

        # episode_003 (chapter=1, DRAFT) は変更されない(公開済みではない)
        assert updated_data["episode_003"]["status"] == "DRAFT"

        # episode_004 (chapter=3) は変更されない
        assert updated_data["episode_004"]["status"] == "PUBLISHED"

    def test_mark_episodes_for_revision_multiple_chapters(
        self, episode_updater: EpisodeStatusUpdater, episodes_data: dict
    ) -> None:
        """複数章の話数リビジョンマークテスト"""
        affected_chapters = [1, 2]
        new_version = "v1.5.0"

        updated_data = episode_updater.mark_episodes_for_revision(episodes_data, affected_chapters, new_version)

        # episode_001 (chapter=1, PUBLISHED) がリビジョン必要に変更
        assert updated_data["episode_001"]["status"] == "REVISION_NEEDED"

        # episode_002 (chapter=2, PUBLISHED) がリビジョン必要に変更
        assert updated_data["episode_002"]["status"] == "REVISION_NEEDED"

        # その他は変更されない
        assert updated_data["episode_003"]["status"] == "DRAFT"
        assert updated_data["episode_004"]["status"] == "PUBLISHED"

    def test_mark_episodes_for_revision_no_affected_episodes(
        self, episode_updater: EpisodeStatusUpdater, episodes_data: dict
    ) -> None:
        """影響を受ける話数がない場合のテスト"""
        affected_chapters = [5]  # 存在しない章
        new_version = "v1.1.0"

        updated_data = episode_updater.mark_episodes_for_revision(episodes_data, affected_chapters, new_version)

        # 全ての話数が変更されない
        for episode_id, episode_info in updated_data.items():
            assert episode_info["status"] == episodes_data[episode_id]["status"]

    def test_mark_episodes_for_revision_empty_chapters(
        self, episode_updater: EpisodeStatusUpdater, episodes_data: dict
    ) -> None:
        """空の影響章リストでのテスト"""
        affected_chapters = []
        new_version = "v1.0.1"

        updated_data = episode_updater.mark_episodes_for_revision(episodes_data, affected_chapters, new_version)

        # 全ての話数が変更されない
        for episode_id, episode_info in updated_data.items():
            assert episode_info["status"] == episodes_data[episode_id]["status"]

    def test_mark_episodes_for_revision_preserves_original_data(
        self, episode_updater: EpisodeStatusUpdater, episodes_data: dict
    ) -> None:
        """元データが保持されることのテスト"""
        affected_chapters = [1]
        new_version = "v2.0.0"
        original_data = episodes_data.copy()

        updated_data = episode_updater.mark_episodes_for_revision(episodes_data, affected_chapters, new_version)

        # 元データは変更されない
        assert episodes_data == original_data

        # updated_dataは独立したコピー
        assert updated_data is not episodes_data
