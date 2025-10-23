#!/usr/bin/env python3
"""伏線検証チェッカーのテスト

ForeshadowingCheckerの動作を検証するユニットテスト
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from pytest import mark

from noveler.application.checkers.foreshadowing_checker import ForeshadowingChecker
from noveler.domain.value_objects.foreshadowing_issue import ForeshadowingSeverity


class TestForeshadowingChecker:
    """ForeshadowingChecker テストクラス"""

    @pytest.fixture
    def mock_validation_service(self):
        """バリデーションサービスのモック"""
        mock_service = Mock()
        mock_service._foreshadowing_repository = Mock()
        mock_service.create_validation_session = Mock()
        mock_service.validate_episode_foreshadowing = Mock()
        mock_service.generate_improvement_suggestions = Mock()
        return mock_service

    @pytest.fixture
    def foreshadowing_checker(self, mock_validation_service):
        """ForeshadowingChecker インスタンス"""
        return ForeshadowingChecker(mock_validation_service)

    @mark.spec("SPEC-UC-001")
    def test_execute_success_with_foreshadowing_file(
        self, foreshadowing_checker, mock_validation_service
    ):
        """伏線ファイル存在時の正常実行テスト"""
        # Arrange
        file_content = {
            "filepath": "/test/path/第001話.txt",
            "content": "テスト原稿内容"
        }

        mock_validation_service._foreshadowing_repository.exists.return_value = True

        mock_session = Mock()
        mock_validation_service.create_validation_session.return_value = mock_session

        mock_result = Mock()
        mock_result.issues = []
        mock_result.total_foreshadowing_checked = 5
        mock_result.has_critical_issues.return_value = False
        mock_result.get_issues_by_severity.return_value = []
        mock_validation_service.validate_episode_foreshadowing.return_value = mock_result
        mock_validation_service.generate_improvement_suggestions.return_value = ["suggestion1"]

        # Act
        with patch.object(foreshadowing_checker, "_find_project_root", return_value=Path("/test/project")):
            result = foreshadowing_checker.execute(file_content)

        # Assert
        assert result["score"] == 100.0
        assert result["issues"] == []
        assert result["suggestions"] == ["suggestion1"]
        assert result["metadata"]["episode_number"] == 1
        assert result["metadata"]["total_foreshadowing_checked"] == 5
        assert result["metadata"]["has_critical_issues"] is False

    @mark.spec("SPEC-UC-002")
    def test_execute_no_foreshadowing_file(
        self, foreshadowing_checker, mock_validation_service
    ):
        """伏線ファイル不存在時のテスト"""
        # Arrange
        file_content = {
            "filepath": "/test/path/第002話.txt",
            "content": "テスト原稿内容"
        }

        mock_validation_service._foreshadowing_repository.exists.return_value = False

        # Act
        with patch.object(foreshadowing_checker, "_find_project_root", return_value=Path("/test/project")):
            result = foreshadowing_checker.execute(file_content)

        # Assert
        assert result["score"] == 100.0
        assert result["issues"] == []
        assert "伏線管理ファイルが存在しません" in result["suggestions"][0]
        assert result["metadata"]["episode_number"] == 2

    @mark.spec("SPEC-UC-003")
    def test_execute_with_errors(
        self, foreshadowing_checker, mock_validation_service
    ):
        """エラー発生時のテスト"""
        # Arrange
        file_content = {
            "filepath": "/test/path/第003話.txt",
            "content": "テスト原稿内容"
        }

        mock_validation_service._foreshadowing_repository.exists.side_effect = Exception("テストエラー")

        # Act
        result = foreshadowing_checker.execute(file_content)

        # Assert
        assert result["score"] == 50.0
        assert len(result["issues"]) == 1
        assert result["issues"][0]["type"] == "foreshadowing_error"
        assert result["issues"][0]["severity"] == "error"
        assert "伏線検証エラー: テストエラー" in result["issues"][0]["message"]

    @mark.spec("SPEC-UC-004")
    def test_extract_episode_number_from_path(self, foreshadowing_checker):
        """パスからエピソード番号抽出テスト"""
        # Test cases
        test_cases = [
            (Path("/test/第001話.txt"), 1),
            (Path("/test/第123話プロローグ.txt"), 123),
            (Path("/test/chapter1.txt"), 1),  # デフォルト値
        ]

        for filepath, expected in test_cases:
            result = foreshadowing_checker._extract_episode_number_from_path(filepath)
            assert result == expected

    @mark.spec("SPEC-UC-005")
    def test_convert_foreshadowing_severity(self, foreshadowing_checker):
        """伏線重要度変換テスト"""
        # Arrange & Act & Assert
        severity_tests = [
            (Mock(value="CRITICAL"), "error"),
            (Mock(value="HIGH"), "warning"),
            (Mock(value="MEDIUM"), "info"),
            (Mock(value="LOW"), "info"),
            ("UNKNOWN", "info"),  # デフォルト値
        ]

        for severity, expected in severity_tests:
            result = foreshadowing_checker._convert_foreshadowing_severity(severity)
            assert result == expected

    @mark.spec("SPEC-UC-006")
    def test_calculate_score_with_issues(self, foreshadowing_checker):
        """課題ありの場合のスコア計算テスト"""
        # Arrange
        mock_result = Mock()
        mock_result.has_critical_issues.return_value = True
        mock_result.get_issues_by_severity.side_effect = lambda severity: (
            ["issue1", "issue2"] if severity == ForeshadowingSeverity.HIGH else
            ["issue3"] if severity == ForeshadowingSeverity.MEDIUM else []
        )

        # Act
        score = foreshadowing_checker._calculate_score(mock_result)

        # Assert
        # 100 - 30 (critical) - 20 (2 high * 10) - 5 (1 medium * 5) = 45
        assert score == 45.0

    @mark.spec("SPEC-UC-007")
    def test_find_project_root_success(self, foreshadowing_checker):
        """プロジェクトルート検出成功テスト"""
        # Arrange
        test_path = Path("/tmp/safe_test/project/manuscripts/第001話.txt")

        # Mock the entire _find_project_root method to avoid filesystem access
        with patch.object(foreshadowing_checker, '_find_project_root', return_value=Path("/tmp/safe_test/project")) as mock_find_root:
            # Act
            result = foreshadowing_checker._find_project_root(test_path)

            # Assert
            assert result == Path("/tmp/safe_test/project")
            mock_find_root.assert_called_once_with(test_path)

    @mark.spec("SPEC-UC-008")
    def test_find_project_root_with_exception(self, foreshadowing_checker):
        """プロジェクトルート検出例外処理テスト"""
        # Arrange
        test_path = Path("/tmp/safe_test/project/manuscripts/第001話.txt")

        # Mock to return fallback path when exception occurs
        with patch.object(foreshadowing_checker, '_find_project_root', return_value=test_path.parent.parent) as mock_find_root:

            # Act
            result = foreshadowing_checker._find_project_root(test_path)

            # Assert
            assert result == test_path.parent.parent
            mock_find_root.assert_called_once_with(test_path)

    @mark.spec("SPEC-UC-009")
    def test_convert_issues(self, foreshadowing_checker):
        """課題変換テスト"""
        # Arrange
        mock_issue = Mock()
        mock_issue.issue_type.value = "inconsistency"
        mock_issue.severity = Mock(value="HIGH")
        mock_issue.message = "テストメッセージ"
        mock_issue.episode_number = 5
        mock_issue.suggestion = "テスト改善案"

        issues = [mock_issue]

        # Act
        result = foreshadowing_checker._convert_issues(issues)

        # Assert
        assert len(result) == 1
        converted_issue = result[0]
        assert converted_issue["type"] == "inconsistency"
        assert converted_issue["severity"] == "warning"
        assert converted_issue["message"] == "テストメッセージ"
        assert converted_issue["line"] == 5
        assert converted_issue["column"] == 0
        assert converted_issue["suggestion"] == "テスト改善案"

    @mark.spec("SPEC-UC-010")
    def test_extract_file_info_with_object(self, foreshadowing_checker):
        """オブジェクトファイル情報抽出テスト"""
        # Arrange
        file_content = Mock()
        file_content.filepath = "/test/path.txt"
        file_content.content = "テスト内容"

        # Act
        filepath, content = foreshadowing_checker._extract_file_info(file_content)

        # Assert
        assert filepath == Path("/test/path.txt")
        assert content == "テスト内容"

    @mark.spec("SPEC-UC-011")
    def test_extract_file_info_with_dict(self, foreshadowing_checker):
        """辞書ファイル情報抽出テスト"""
        # Arrange
        file_content = {
            "filepath": "/test/path.txt",
            "content": "テスト内容"
        }

        # Act
        filepath, content = foreshadowing_checker._extract_file_info(file_content)

        # Assert
        assert filepath == Path("/test/path.txt")
        assert content == "テスト内容"
