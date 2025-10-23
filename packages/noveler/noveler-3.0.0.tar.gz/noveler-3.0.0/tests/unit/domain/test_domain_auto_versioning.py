#!/usr/bin/env python3
"""自動バージョニングドメインのテストスイート
TDDアプローチ: 失敗するテストを先に作成


仕様書: SPEC-UNIT-TEST
"""

import sys
import unittest
from pathlib import Path

import pytest

from noveler.domain.exceptions import InvalidVersionError
from noveler.domain.versioning.entities import ChangeScope, FileChangeAnalyzer, VersionDeterminer, VersionSuggestion
from noveler.domain.versioning.services import AutoVersioningService
from noveler.domain.versioning.value_objects import VersionCalculator

# PathManager統一パス管理システムを使用(事前にパスを設定)
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/を追加
from noveler.infrastructure.utils.path_manager import ensure_imports

ensure_imports()


class TestVersionDeterminer(unittest.TestCase):
    """バージョン判定器のテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_AUTO_VERSIONING-MAJOR_VERSION_FOR_MA")
    def test_major_version_for_master_plot_changes(self) -> None:
        """全体構成変更でメジャーバージョンアップ"""

        determiner = VersionDeterminer()
        changed_files = [
            "20_プロット/全体構成.yaml",
            "20_プロット/章別プロット/chapter03.yaml",
        ]

        version_type = determiner.determine_version_type(changed_files)

        assert version_type == "major"

    @pytest.mark.spec("SPEC-DOMAIN_AUTO_VERSIONING-MINOR_VERSION_FOR_CH")
    def test_minor_version_for_chapter_changes(self) -> None:
        """章別プロット変更でマイナーバージョンアップ"""

        determiner = VersionDeterminer()
        changed_files = [
            "20_プロット/章別プロット/chapter03.yaml",
            "20_プロット/章別プロット/chapter04.yaml",
        ]

        version_type = determiner.determine_version_type(changed_files)

        assert version_type == "minor"

    @pytest.mark.spec("SPEC-DOMAIN_AUTO_VERSIONING-PATCH_VERSION_FOR_MI")
    def test_patch_version_for_minor_changes(self) -> None:
        """細かい修正でパッチバージョンアップ"""

        determiner = VersionDeterminer()
        changed_files = [
            "30_設定集/用語集.yaml",
            "30_設定集/キャラクター.yaml",
        ]

        version_type = determiner.determine_version_type(changed_files)

        assert version_type == "patch"

    @pytest.mark.spec("SPEC-DOMAIN_AUTO_VERSIONING-PRIORITY_RULE_MAJOR_")
    def test_priority_rule_major_over_minor(self) -> None:
        """優先順位: メジャー > マイナー"""

        determiner = VersionDeterminer()
        changed_files = [
            "20_プロット/全体構成.yaml",  # major
            "20_プロット/章別プロット/chapter03.yaml",  # minor
            "30_設定集/用語集.yaml",  # patch
        ]

        version_type = determiner.determine_version_type(changed_files)

        assert version_type == "major"

    @pytest.mark.spec("SPEC-DOMAIN_AUTO_VERSIONING-RESOURCE_ALLOCATION_")
    def test_resource_allocation_triggers_major(self) -> None:
        """リソース配分変更もメジャーバージョンアップ"""

        determiner = VersionDeterminer()
        changed_files = ["20_プロット/リソース配分.yaml"]

        version_type = determiner.determine_version_type(changed_files)

        assert version_type == "major"


class TestFileChangeAnalyzer(unittest.TestCase):
    """ファイル変更分析器のテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_AUTO_VERSIONING-ANALYZE_PLOT_FILE_CH")
    def test_analyze_plot_file_changes(self) -> None:
        """プロット関連ファイルの変更を分析"""

        analyzer = FileChangeAnalyzer()
        all_changed_files = [
            "20_プロット/全体構成.yaml",
            "40_原稿/第15話_決戦前夜.md",
            "README.md",
        ]

        plot_changes = analyzer.extract_plot_changes(all_changed_files)

        assert len(plot_changes) == 1
        assert "20_プロット/全体構成.yaml" in plot_changes
        assert "40_原稿/第15話_決戦前夜.md" not in plot_changes

    @pytest.mark.spec("SPEC-DOMAIN_AUTO_VERSIONING-CATEGORIZE_CHANGES_B")
    def test_categorize_changes_by_scope(self) -> None:
        """変更をスコープ別に分類"""

        analyzer = FileChangeAnalyzer()
        changed_files = [
            "20_プロット/全体構成.yaml",
            "20_プロット/章別プロット/chapter03.yaml",
            "30_設定集/用語集.yaml",
        ]

        categorized = analyzer.categorize_by_scope(changed_files)

        assert categorized[ChangeScope.MAJOR] == ["20_プロット/全体構成.yaml"]
        assert categorized[ChangeScope.MINOR] == ["20_プロット/章別プロット/chapter03.yaml"]
        assert categorized[ChangeScope.PATCH] == ["30_設定集/用語集.yaml"]


class TestVersionSuggestion(unittest.TestCase):
    """バージョン提案のテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_AUTO_VERSIONING-SUGGEST_MAJOR_VERSIO")
    def test_suggest_major_version_bump(self) -> None:
        """メジャーバージョンアップの提案"""

        suggestion = VersionSuggestion.create_major_bump(
            current_version="v1.5.3",
            changed_files=["20_プロット/全体構成.yaml"],
            description="エンディング全面見直し",
        )

        assert suggestion.suggested_version == "v2.0.0"
        assert suggestion.version_type == "major"
        assert "全体構成" in suggestion.explanation

    @pytest.mark.spec("SPEC-DOMAIN_AUTO_VERSIONING-SUGGEST_MINOR_VERSIO")
    def test_suggest_minor_version_bump(self) -> None:
        """マイナーバージョンアップの提案"""

        suggestion = VersionSuggestion.create_minor_bump(
            current_version="v2.1.0",
            changed_files=["20_プロット/章別プロット/chapter03.yaml"],
            description="ch03クライマックス変更",
        )

        assert suggestion.suggested_version == "v2.2.0"
        assert suggestion.version_type == "minor"
        assert "章別プロット" in suggestion.explanation

    @pytest.mark.spec("SPEC-DOMAIN_AUTO_VERSIONING-SUGGEST_PATCH_VERSIO")
    def test_suggest_patch_version_bump(self) -> None:
        """パッチバージョンアップの提案"""

        suggestion = VersionSuggestion.create_patch_bump(
            current_version="v2.1.0",
            changed_files=["30_設定集/用語集.yaml"],
            description="用語の微調整",
        )

        assert suggestion.suggested_version == "v2.1.1"
        assert suggestion.version_type == "patch"


class TestVersionCalculator(unittest.TestCase):
    """バージョン計算のテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_AUTO_VERSIONING-CALCULATE_NEXT_MAJOR")
    def test_calculate_next_major_version(self) -> None:
        """次のメジャーバージョンを計算"""

        calculator = VersionCalculator()

        next_version = calculator.calculate_next_version("v1.5.3", "major")
        assert next_version == "v2.0.0"

        next_version = calculator.calculate_next_version("v2.0.0", "major")
        assert next_version == "v3.0.0"

    @pytest.mark.spec("SPEC-DOMAIN_AUTO_VERSIONING-CALCULATE_NEXT_MINOR")
    def test_calculate_next_minor_version(self) -> None:
        """次のマイナーバージョンを計算"""

        calculator = VersionCalculator()

        next_version = calculator.calculate_next_version("v1.5.3", "minor")
        assert next_version == "v1.6.0"

        next_version = calculator.calculate_next_version("v2.0.0", "minor")
        assert next_version == "v2.1.0"

    @pytest.mark.spec("SPEC-DOMAIN_AUTO_VERSIONING-CALCULATE_NEXT_PATCH")
    def test_calculate_next_patch_version(self) -> None:
        """次のパッチバージョンを計算"""

        calculator = VersionCalculator()

        next_version = calculator.calculate_next_version("v1.5.3", "patch")
        assert next_version == "v1.5.4"

        next_version = calculator.calculate_next_version("v2.1.0", "patch")
        assert next_version == "v2.1.1"

    @pytest.mark.spec("SPEC-DOMAIN_AUTO_VERSIONING-INVALID_VERSION_FORM")
    def test_invalid_version_format(self) -> None:
        """不正なバージョン形式のエラーハンドリング"""

        calculator = VersionCalculator()

        with pytest.raises(InvalidVersionError, match=".*"):
            calculator.calculate_next_version("invalid", "major")


class TestAutoVersioningService(unittest.TestCase):
    """自動バージョニングサービスのテスト(ドメインサービス)"""

    @pytest.mark.spec("SPEC-DOMAIN_AUTO_VERSIONING-FULL_AUTO_VERSIONING")
    def test_full_auto_versioning_workflow(self) -> None:
        """自動バージョニングの全体ワークフロー"""

        service = AutoVersioningService()
        changed_files = [
            "20_プロット/全体構成.yaml",
            "20_プロット/章別プロット/chapter03.yaml",
            "30_設定集/用語集.yaml",
        ]

        suggestion = service.suggest_version_update(
            current_version="v1.5.3",
            changed_files=changed_files,
            description="エンディング全面見直し",
        )

        assert suggestion.suggested_version == "v2.0.0"
        assert suggestion.version_type == "major"
        assert "全体構成" in suggestion.explanation

    @pytest.mark.spec("SPEC-DOMAIN_AUTO_VERSIONING-NO_PLOT_CHANGES_RETU")
    def test_no_plot_changes_returns_none(self) -> None:
        """プロット変更がない場合はNoneを返す"""

        service = AutoVersioningService()
        changed_files = [
            "40_原稿/第15話_決戦前夜.md",
            "README.md",
        ]

        suggestion = service.suggest_version_update(
            current_version="v1.5.3",
            changed_files=changed_files,
            description="原稿更新のみ",
        )

        assert suggestion is None


if __name__ == "__main__":
    unittest.main()
