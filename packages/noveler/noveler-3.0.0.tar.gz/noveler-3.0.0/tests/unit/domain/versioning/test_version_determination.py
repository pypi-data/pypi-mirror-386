"""バージョン判定関連のテスト

TDD準拠テスト:
    - VersionDeterminer
- VersionSuggestion


仕様書: SPEC-UNIT-TEST
"""

import pytest

from noveler.domain.versioning.entities import (
    VersionDeterminer,
    VersionSuggestion,
)


class TestVersionDeterminer:
    """VersionDeterminerのテストクラス"""

    @pytest.fixture
    def version_determiner(self) -> VersionDeterminer:
        """バージョン判定器"""
        return VersionDeterminer()

    def test_determine_version_type_major(self, version_determiner: VersionDeterminer) -> None:
        """全体構成変更でのメジャーバージョン判定テスト"""
        changed_files = ["20_プロット/全体構成.yaml", "other_file.txt"]

        version_type = version_determiner.determine_version_type(changed_files)

        assert version_type == "major"

    def test_determine_version_type_minor(self, version_determiner: VersionDeterminer) -> None:
        """章別プロット変更でのマイナーバージョン判定テスト"""
        changed_files = ["20_プロット/章別プロット/chapter01.yaml", "other_file.txt"]

        version_type = version_determiner.determine_version_type(changed_files)

        assert version_type == "minor"

    def test_determine_version_type_patch(self, version_determiner: VersionDeterminer) -> None:
        """その他変更でのパッチバージョン判定テスト"""
        changed_files = ["30_設定集/キャラクター.yaml", "40_原稿/第001話.md"]

        version_type = version_determiner.determine_version_type(changed_files)

        assert version_type == "patch"

    def test_determine_version_type_major_over_minor(self, version_determiner: VersionDeterminer) -> None:
        """メジャー・マイナー混在時の優先順位テスト"""
        changed_files = [
            "20_プロット/章別プロット/chapter01.yaml",  # minor
            "20_プロット/全体構成.yaml",  # major
        ]

        version_type = version_determiner.determine_version_type(changed_files)

        assert version_type == "major"

    def test_determine_version_type_minor_over_patch(self, version_determiner: VersionDeterminer) -> None:
        """マイナー・パッチ混在時の優先順位テスト"""
        changed_files = [
            "40_原稿/第001話.md",  # patch
            "20_プロット/章別プロット/chapter02.yaml",  # minor
        ]

        version_type = version_determiner.determine_version_type(changed_files)

        assert version_type == "minor"

    def test_determine_version_type_empty_files(self, version_determiner: VersionDeterminer) -> None:
        """ファイル変更なしでのパッチ判定テスト"""
        changed_files = []

        version_type = version_determiner.determine_version_type(changed_files)

        assert version_type == "patch"


class TestVersionSuggestion:
    """VersionSuggestionのテストクラス"""

    @pytest.fixture
    def mock_plot_data(self) -> dict:
        """モック全体構成データ"""
        return {
            "basic_info": {
                "title": "サンプル小説",
                "target_episodes": 50,
                "genre": "ファンタジー",
            },
            "metadata": {
                "version": "1.0.0",
                "last_modified": "2023-07-01",
            },
        }

    def test_create_suggestion_success_major(self, mock_plot_data: dict) -> None:
        """メジャーバージョン提案成功テスト"""
        version_data = {
            "current_version": "1.0.0",
            "version_type": "major",
            "plot_data": mock_plot_data,
        }

        suggestion = VersionSuggestion.create_suggestion(version_data)

        assert suggestion is not None
        assert suggestion.current_version == "1.0.0"
        assert suggestion.suggested_version == "2.0.0"
        assert suggestion.version_type == "major"
        assert suggestion.justification != ""

    def test_create_suggestion_success_minor(self, mock_plot_data: dict) -> None:
        """マイナーバージョン提案成功テスト"""
        version_data = {
            "current_version": "1.0.0",
            "version_type": "minor",
            "plot_data": mock_plot_data,
        }

        suggestion = VersionSuggestion.create_suggestion(version_data)

        assert suggestion is not None
        assert suggestion.current_version == "1.0.0"
        assert suggestion.suggested_version == "1.1.0"
        assert suggestion.version_type == "minor"

    def test_create_suggestion_success_patch(self, mock_plot_data: dict) -> None:
        """パッチバージョン提案成功テスト"""
        version_data = {
            "current_version": "1.2.3",
            "version_type": "patch",
            "plot_data": mock_plot_data,
        }

        suggestion = VersionSuggestion.create_suggestion(version_data)

        assert suggestion is not None
        assert suggestion.current_version == "1.2.3"
        assert suggestion.suggested_version == "1.2.4"
        assert suggestion.version_type == "patch"

    def test_create_suggestion_invalid_version_format(self, mock_plot_data: dict) -> None:
        """無効なバージョン形式でのテスト"""
        version_data = {
            "current_version": "invalid_version",
            "version_type": "major",
            "plot_data": mock_plot_data,
        }

        suggestion = VersionSuggestion.create_suggestion(version_data)

        assert suggestion is None

    def test_get_formatted_message_with_impact(self) -> None:
        """影響情報付きメッセージ生成テスト"""
        suggestion = VersionSuggestion(
            current_version="1.0.0",
            suggested_version="2.0.0",
            version_type="major",
            changed_files=[],
            explanation="全体構成の大幅変更",
        )

        impact_info = {
            "affected_chapters": [1, 2, 3],
            "affected_episodes": 15,
        }

        formatted_message = suggestion.get_formatted_message(impact_info)

        assert "1.0.0 → 2.0.0" in formatted_message
        assert "全体構成の大幅変更" in formatted_message
        assert "影響: 章数 3, エピソード数 15" in formatted_message

    def test_get_formatted_message_without_impact(self) -> None:
        """影響情報なしメッセージ生成テスト"""
        suggestion = VersionSuggestion(
            current_version="1.0.0",
            suggested_version="1.0.1",
            version_type="patch",
            justification="誤字修正",
        )

        formatted_message = suggestion.get_formatted_message()

        assert "1.0.0 → 1.0.1" in formatted_message
        assert "誤字修正" in formatted_message
        assert "影響:" not in formatted_message
