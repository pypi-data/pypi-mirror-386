"""分析関連エンティティのテスト

TDD準拠テスト:
    - FileChangeAnalyzer
- CommitAnalysis
- PlotCommitAnalyzer
- PlotVersionConsistencyAnalyzer


仕様書: SPEC-UNIT-TEST
"""

from unittest.mock import patch

import pytest

from noveler.domain.versioning.entities import (
    CommitAnalysis,
    FileChangeAnalyzer,
    PlotCommitAnalyzer,
    PlotVersionConsistencyAnalyzer,
)
from noveler.domain.versioning.value_objects import (
    ChangeScope,
    ChangeSignificance,
)


class TestFileChangeAnalyzer:
    """FileChangeAnalyzerのテストクラス"""

    @pytest.fixture
    def file_analyzer(self) -> FileChangeAnalyzer:
        """ファイル変更分析器"""
        return FileChangeAnalyzer()

    def test_extract_plot_changes(self, file_analyzer: FileChangeAnalyzer) -> None:
        """プロット関連ファイル抽出テスト"""
        changed_files = [
            "20_プロット/全体構成.yaml",
            "30_設定集/キャラクター.yaml",
            "40_原稿/第001話.md",
            "50_管理資料/話数管理.yaml",
        ]

        plot_changes = file_analyzer.extract_plot_changes(changed_files)

        expected_plot_changes = ["20_プロット/全体構成.yaml", "30_設定集/キャラクター.yaml"]
        assert plot_changes == expected_plot_changes

    def test_extract_plot_changes_empty_input(self, file_analyzer: FileChangeAnalyzer) -> None:
        """空入力でのプロット関連ファイル抽出テスト"""
        changed_files = []

        plot_changes = file_analyzer.extract_plot_changes(changed_files)

        assert plot_changes == []

    def test_extract_plot_changes_no_plot_files(self, file_analyzer: FileChangeAnalyzer) -> None:
        """プロット関連ファイルなしの抽出テスト"""
        changed_files = ["40_原稿/第001話.md", "50_管理資料/話数管理.yaml", "README.md"]

        plot_changes = file_analyzer.extract_plot_changes(changed_files)

        assert plot_changes == []

    def test_categorize_by_scope_all_categories(self, file_analyzer: FileChangeAnalyzer) -> None:
        """全カテゴリ分類テスト"""
        changed_files = [
            "20_プロット/全体構成.yaml",  # MAJOR
            "20_プロット/章別プロット/chapter01.yaml",  # MINOR
            "40_原稿/第001話.md",  # PATCH
            "30_設定集/キャラクター.yaml",  # PATCH
        ]

        categorized = file_analyzer.categorize_by_scope(changed_files)

        assert categorized[ChangeScope.MAJOR] == ["20_プロット/全体構成.yaml"]
        assert categorized[ChangeScope.MINOR] == ["20_プロット/章別プロット/chapter01.yaml"]
        assert set(categorized[ChangeScope.PATCH]) == {"40_原稿/第001話.md", "30_設定集/キャラクター.yaml"}

    def test_categorize_by_scope_major_pattern_matching(self, file_analyzer: FileChangeAnalyzer) -> None:
        """メジャーパターンマッチングテスト"""
        changed_files = [
            "20_プロット/全体構成.yaml",  # 完全一致
            "20_プロット/リソース配分.yaml",  # 完全一致
            "20_プロット/全体構成.yaml.bak",  # 前方一致(startswith)
        ]

        categorized = file_analyzer.categorize_by_scope(changed_files)

        assert len(categorized[ChangeScope.MAJOR]) == 3
        assert "20_プロット/全体構成.yaml" in categorized[ChangeScope.MAJOR]
        assert "20_プロット/リソース配分.yaml" in categorized[ChangeScope.MAJOR]
        assert "20_プロット/全体構成.yaml.bak" in categorized[ChangeScope.MAJOR]

    def test_categorize_by_scope_empty_input(self, file_analyzer: FileChangeAnalyzer) -> None:
        """空入力での分類テスト"""
        changed_files = []

        categorized = file_analyzer.categorize_by_scope(changed_files)

        assert categorized[ChangeScope.MAJOR] == []
        assert categorized[ChangeScope.MINOR] == []
        assert categorized[ChangeScope.PATCH] == []


class TestCommitAnalysis:
    """CommitAnalysisのテストクラス"""

    def test_create_analysis_success(self) -> None:
        """分析作成成功テスト"""
        changed_files = ["20_プロット/全体構成.yaml", "40_原稿/第001話.md"]

        analysis = CommitAnalysis.create_analysis(changed_files)

        assert analysis is not None
        assert analysis.changed_files == changed_files
        assert analysis.plot_files == ["20_プロット/全体構成.yaml"]
        assert ChangeScope.MAJOR in analysis.scope_categories
        assert ChangeScope.PATCH in analysis.scope_categories

    def test_create_analysis_empty_files(self) -> None:
        """空ファイルリストでの分析作成テスト"""
        changed_files = []

        analysis = CommitAnalysis.create_analysis(changed_files)

        assert analysis is not None
        assert analysis.changed_files == []
        assert analysis.plot_files == []

    def test_get_significance_major_changes(self) -> None:
        """メジャー変更での重要度取得テスト"""
        changed_files = ["20_プロット/全体構成.yaml"]
        analysis = CommitAnalysis.create_analysis(changed_files)

        significance = analysis.get_significance()

        assert significance == ChangeSignificance.HIGH

    def test_get_significance_minor_changes(self) -> None:
        """マイナー変更での重要度取得テスト"""
        changed_files = ["20_プロット/章別プロット/chapter01.yaml"]
        analysis = CommitAnalysis.create_analysis(changed_files)

        significance = analysis.get_significance()

        assert significance == ChangeSignificance.MEDIUM

    def test_get_significance_patch_changes(self) -> None:
        """パッチ変更での重要度取得テスト"""
        changed_files = ["40_原稿/第001話.md"]
        analysis = CommitAnalysis.create_analysis(changed_files)

        significance = analysis.get_significance()

        assert significance == ChangeSignificance.LOW


class TestPlotCommitAnalyzer:
    """PlotCommitAnalyzerのテストクラス"""

    @pytest.fixture
    def plot_analyzer(self) -> PlotCommitAnalyzer:
        """プロットコミット分析器"""
        return PlotCommitAnalyzer()

    @patch("noveler.domain.versioning.entities.PlotCommitAnalyzer._git_service")
    def test_analyze_commit_impact_success(self, mock_git_service, plot_analyzer: PlotCommitAnalyzer) -> None:
        """コミット影響分析成功テスト"""
        # モックセットアップ
        mock_git_service.get_changed_files.return_value = [
            "20_プロット/全体構成.yaml",
            "20_プロット/章別プロット/chapter01.yaml",
        ]

        commit_hash = "abc123"
        impact = plot_analyzer.analyze_commit_impact(commit_hash)

        assert impact is not None
        assert impact.commit_hash == commit_hash
        assert impact.version_type == "major"  # 全体構成変更のため
        assert len(impact.affected_chapters) > 0

    @patch("noveler.domain.versioning.entities.PlotCommitAnalyzer._git_service")
    def test_analyze_commit_impact_no_plot_changes(self, mock_git_service, plot_analyzer: PlotCommitAnalyzer) -> None:
        """プロット変更なしでのコミット影響分析テスト"""
        # モックセットアップ
        mock_git_service.get_changed_files.return_value = [
            "40_原稿/第001話.md",
            "README.md",
        ]

        commit_hash = "abc123"
        impact = plot_analyzer.analyze_commit_impact(commit_hash)

        assert impact is not None
        assert impact.version_type == "patch"
        assert len(impact.affected_chapters) == 0

    def test_analyze_plot_consistency_success(self, plot_analyzer: PlotCommitAnalyzer) -> None:
        """プロット整合性分析成功テスト"""
        mock_plot_data = {
            "basic_info": {
                "title": "サンプル小説",
                "target_episodes": 50,
            },
            "metadata": {
                "version": "1.0.0",
            },
        }

        consistency = plot_analyzer.analyze_plot_consistency(mock_plot_data)

        assert consistency is not None
        assert consistency.is_consistent is True or False  # いずれかの値
        assert isinstance(consistency.consistency_score, float)
        assert 0.0 <= consistency.consistency_score <= 1.0


class TestPlotVersionConsistencyAnalyzer:
    """PlotVersionConsistencyAnalyzerのテストクラス"""

    @pytest.fixture
    def consistency_analyzer(self) -> PlotVersionConsistencyAnalyzer:
        """プロットバージョン整合性分析器"""
        return PlotVersionConsistencyAnalyzer()

    def test_check_version_consistency_consistent(self, consistency_analyzer: PlotVersionConsistencyAnalyzer) -> None:
        """整合性ありでのバージョン整合性チェックテスト"""
        mock_data = {
            "basic_info": {
                "title": "サンプル小説",
                "target_episodes": 50,
            },
            "structure": {
                "chapters": [
                    {"chapter_number": 1, "episodes": list(range(1, 11))},
                    {"chapter_number": 2, "episodes": list(range(11, 21))},
                ],
            },
            "metadata": {
                "version": "1.0.0",
                "last_modified": "2023-07-01",
            },
        }

        result = consistency_analyzer.check_version_consistency(mock_data)

        assert result is not None
        assert isinstance(result.is_consistent, bool)
        assert isinstance(result.consistency_score, float)
        assert 0.0 <= result.consistency_score <= 1.0

    def test_check_version_consistency_missing_metadata(
        self, consistency_analyzer: PlotVersionConsistencyAnalyzer
    ) -> None:
        """メタデータ欠損でのバージョン整合性チェックテスト"""
        mock_data = {
            "basic_info": {
                "title": "サンプル小説",
            },
            # metadata が欠損
        }

        result = consistency_analyzer.check_version_consistency(mock_data)

        assert result is not None
        assert result.is_consistent is False
        assert result.consistency_score < 1.0

    def test_calculate_impact_significance_high(self, consistency_analyzer: PlotVersionConsistencyAnalyzer) -> None:
        """高影響度計算テスト"""
        impact_data = {
            "affected_chapters": [1, 2, 3, 4, 5],  # 多数章影響
            "affected_episodes": 25,  # 多数エピソード影響
        }

        significance = consistency_analyzer.calculate_impact_significance(impact_data)

        assert significance == ChangeSignificance.HIGH

    def test_calculate_impact_significance_medium(self, consistency_analyzer: PlotVersionConsistencyAnalyzer) -> None:
        """中影響度計算テスト"""
        impact_data = {
            "affected_chapters": [1, 2],  # 中程度章影響
            "affected_episodes": 10,  # 中程度エピソード影響
        }

        significance = consistency_analyzer.calculate_impact_significance(impact_data)

        assert significance == ChangeSignificance.MEDIUM

    def test_calculate_impact_significance_low(self, consistency_analyzer: PlotVersionConsistencyAnalyzer) -> None:
        """低影響度計算テスト"""
        impact_data = {
            "affected_chapters": [1],  # 少数章影響
            "affected_episodes": 3,  # 少数エピソード影響
        }

        significance = consistency_analyzer.calculate_impact_significance(impact_data)

        assert significance == ChangeSignificance.LOW
