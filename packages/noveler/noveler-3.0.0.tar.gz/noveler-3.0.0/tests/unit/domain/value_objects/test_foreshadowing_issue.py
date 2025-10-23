#!/usr/bin/env python3
"""
伏線問題値オブジェクトのテスト
SPEC-FORESHADOWING-001準拠
"""

from datetime import datetime, timezone

import pytest

from noveler.domain.value_objects.foreshadowing_issue import (
    ForeshadowingDetectionResult,
    ForeshadowingIssue,
    ForeshadowingIssueType,
    ForeshadowingSeverity,
    ForeshadowingValidationConfig,
)

pytestmark = pytest.mark.vo_smoke


@pytest.mark.spec("SPEC-FORESHADOWING-001")
class TestForeshadowingIssue:
    """伏線問題値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-FORESHADOWING_ISSUE-VALID_FORESHADOWING_")
    def test_valid_foreshadowing_issue_creation(self):
        """正常な伏線問題作成"""
        issue = ForeshadowingIssue(
            foreshadowing_id="F001",
            issue_type=ForeshadowingIssueType.MISSING_PLANTING,
            severity=ForeshadowingSeverity.HIGH,
            episode_number=5,
            message="伏線が仕込まれていません",
            expected_content="森の動物たちが騒がしい",
            suggestion="環境描写で仕込んでください",
        )

        assert issue.foreshadowing_id == "F001"
        assert issue.issue_type == ForeshadowingIssueType.MISSING_PLANTING
        assert issue.severity == ForeshadowingSeverity.HIGH
        assert issue.episode_number == 5
        assert issue.message == "伏線が仕込まれていません"

    @pytest.mark.spec("SPEC-FORESHADOWING_ISSUE-INVALID_FORESHADOWIN")
    def test_invalid_foreshadowing_id_empty(self):
        """伏線ID空文字エラー"""
        with pytest.raises(ValueError, match="伏線IDは必須です"):
            ForeshadowingIssue(
                foreshadowing_id="",
                issue_type=ForeshadowingIssueType.MISSING_PLANTING,
                severity=ForeshadowingSeverity.HIGH,
                episode_number=5,
                message="テストメッセージ",
            )

    @pytest.mark.spec("SPEC-FORESHADOWING_ISSUE-INVALID_FORESHADOWIN")
    def test_invalid_foreshadowing_id_format(self):
        """伏線ID形式エラー"""
        with pytest.raises(ValueError, match="伏線IDは'F'で始まる必要があります"):
            ForeshadowingIssue(
                foreshadowing_id="A001",
                issue_type=ForeshadowingIssueType.MISSING_PLANTING,
                severity=ForeshadowingSeverity.HIGH,
                episode_number=5,
                message="テストメッセージ",
            )

    @pytest.mark.spec("SPEC-FORESHADOWING_ISSUE-INVALID_EPISODE_NUMB")
    def test_invalid_episode_number(self):
        """エピソード番号エラー"""
        with pytest.raises(ValueError, match="エピソード番号は1以上である必要があります"):
            ForeshadowingIssue(
                foreshadowing_id="F001",
                issue_type=ForeshadowingIssueType.MISSING_PLANTING,
                severity=ForeshadowingSeverity.HIGH,
                episode_number=0,
                message="テストメッセージ",
            )

    @pytest.mark.spec("SPEC-FORESHADOWING_ISSUE-EMPTY_MESSAGE")
    def test_empty_message(self):
        """メッセージ空文字エラー"""
        with pytest.raises(ValueError, match="メッセージは必須です"):
            ForeshadowingIssue(
                foreshadowing_id="F001",
                issue_type=ForeshadowingIssueType.MISSING_PLANTING,
                severity=ForeshadowingSeverity.HIGH,
                episode_number=5,
                message="",
            )

    @pytest.mark.spec("SPEC-FORESHADOWING_ISSUE-IS_CRITICAL_METHOD")
    def test_is_critical_method(self):
        """クリティカル判定メソッド"""
        critical_issue = ForeshadowingIssue(
            foreshadowing_id="F001",
            issue_type=ForeshadowingIssueType.MISSING_RESOLUTION,
            severity=ForeshadowingSeverity.CRITICAL,
            episode_number=5,
            message="回収漏れ",
        )

        non_critical_issue = ForeshadowingIssue(
            foreshadowing_id="F002",
            issue_type=ForeshadowingIssueType.MISSING_PLANTING,
            severity=ForeshadowingSeverity.HIGH,
            episode_number=5,
            message="仕込み漏れ",
        )

        assert critical_issue.is_critical()
        assert not non_critical_issue.is_critical()

    @pytest.mark.spec("SPEC-FORESHADOWING_ISSUE-IS_PLANTING_ISSUE_ME")
    def test_is_planting_issue_method(self):
        """仕込み問題判定メソッド"""
        planting_issue = ForeshadowingIssue(
            foreshadowing_id="F001",
            issue_type=ForeshadowingIssueType.MISSING_PLANTING,
            severity=ForeshadowingSeverity.HIGH,
            episode_number=5,
            message="仕込み漏れ",
        )

        resolution_issue = ForeshadowingIssue(
            foreshadowing_id="F002",
            issue_type=ForeshadowingIssueType.MISSING_RESOLUTION,
            severity=ForeshadowingSeverity.CRITICAL,
            episode_number=5,
            message="回収漏れ",
        )

        assert planting_issue.is_planting_issue()
        assert not resolution_issue.is_planting_issue()

    @pytest.mark.spec("SPEC-FORESHADOWING_ISSUE-FORMAT_FOR_DISPLAY")
    def test_format_for_display(self):
        """表示用フォーマット"""
        issue = ForeshadowingIssue(
            foreshadowing_id="F001",
            issue_type=ForeshadowingIssueType.MISSING_PLANTING,
            severity=ForeshadowingSeverity.HIGH,
            episode_number=5,
            message="伏線が仕込まれていません",
        )

        formatted = issue.format_for_display()
        assert "⚠️" in formatted  # HIGH severity icon
        assert "🔍" in formatted  # MISSING_PLANTING icon
        assert "F001" in formatted
        assert "伏線が仕込まれていません" in formatted


@pytest.mark.spec("SPEC-FORESHADOWING-001")
class TestForeshadowingDetectionResult:
    """伏線検知結果のテスト"""

    @pytest.mark.spec("SPEC-FORESHADOWING_ISSUE-VALID_DETECTION_RESU")
    def test_valid_detection_result_creation(self):
        """正常な検知結果作成"""
        issues = [
            ForeshadowingIssue(
                foreshadowing_id="F001",
                issue_type=ForeshadowingIssueType.MISSING_PLANTING,
                severity=ForeshadowingSeverity.HIGH,
                episode_number=5,
                message="仕込み漏れ",
            )
        ]

        result = ForeshadowingDetectionResult(
            episode_number=5,
            issues=issues,
            total_foreshadowing_checked=3,
            detection_timestamp=datetime.now(timezone.utc),
        )

        assert result.episode_number == 5
        assert len(result.issues) == 1
        assert result.total_foreshadowing_checked == 3
        assert result.has_issues()

    @pytest.mark.spec("SPEC-FORESHADOWING_ISSUE-NO_ISSUES_DETECTION_")
    def test_no_issues_detection_result(self):
        """問題なしの検知結果"""
        result = ForeshadowingDetectionResult(
            episode_number=5, issues=[], total_foreshadowing_checked=3, detection_timestamp=datetime.now(timezone.utc)
        )

        assert not result.has_issues()
        assert not result.has_critical_issues()

    @pytest.mark.spec("SPEC-FORESHADOWING_ISSUE-HAS_CRITICAL_ISSUES")
    def test_has_critical_issues(self):
        """クリティカル問題の存在判定"""
        critical_issue = ForeshadowingIssue(
            foreshadowing_id="F001",
            issue_type=ForeshadowingIssueType.MISSING_RESOLUTION,
            severity=ForeshadowingSeverity.CRITICAL,
            episode_number=5,
            message="回収漏れ",
        )

        high_issue = ForeshadowingIssue(
            foreshadowing_id="F002",
            issue_type=ForeshadowingIssueType.MISSING_PLANTING,
            severity=ForeshadowingSeverity.HIGH,
            episode_number=5,
            message="仕込み漏れ",
        )

        result_with_critical = ForeshadowingDetectionResult(
            episode_number=5,
            issues=[critical_issue, high_issue],
            total_foreshadowing_checked=2,
            detection_timestamp=datetime.now(timezone.utc),
        )

        result_without_critical = ForeshadowingDetectionResult(
            episode_number=5,
            issues=[high_issue],
            total_foreshadowing_checked=2,
            detection_timestamp=datetime.now(timezone.utc),
        )

        assert result_with_critical.has_critical_issues()
        assert not result_without_critical.has_critical_issues()

    @pytest.mark.spec("SPEC-FORESHADOWING_ISSUE-GET_ISSUES_BY_SEVERI")
    def test_get_issues_by_severity(self):
        """重要度別問題取得"""
        critical_issue = ForeshadowingIssue(
            foreshadowing_id="F001",
            issue_type=ForeshadowingIssueType.MISSING_RESOLUTION,
            severity=ForeshadowingSeverity.CRITICAL,
            episode_number=5,
            message="回収漏れ",
        )

        high_issue = ForeshadowingIssue(
            foreshadowing_id="F002",
            issue_type=ForeshadowingIssueType.MISSING_PLANTING,
            severity=ForeshadowingSeverity.HIGH,
            episode_number=5,
            message="仕込み漏れ",
        )

        result = ForeshadowingDetectionResult(
            episode_number=5,
            issues=[critical_issue, high_issue],
            total_foreshadowing_checked=2,
            detection_timestamp=datetime.now(timezone.utc),
        )

        critical_issues = result.get_issues_by_severity(ForeshadowingSeverity.CRITICAL)
        high_issues = result.get_issues_by_severity(ForeshadowingSeverity.HIGH)

        assert len(critical_issues) == 1
        assert len(high_issues) == 1
        assert critical_issues[0].foreshadowing_id == "F001"
        assert high_issues[0].foreshadowing_id == "F002"


@pytest.mark.spec("SPEC-FORESHADOWING-001")
class TestForeshadowingValidationConfig:
    """伏線検証設定のテスト"""

    @pytest.mark.spec("SPEC-FORESHADOWING_ISSUE-DEFAULT_CONFIG")
    def test_default_config(self):
        """デフォルト設定"""
        config = ForeshadowingValidationConfig()

        assert config.enable_planting_check
        assert config.enable_resolution_check
        assert config.enable_interactive_confirmation
        assert not config.auto_update_status
        assert config.min_importance_for_high_severity == 4

    @pytest.mark.spec("SPEC-FORESHADOWING_ISSUE-CUSTOM_CONFIG")
    def test_custom_config(self):
        """カスタム設定"""
        config = ForeshadowingValidationConfig(
            enable_planting_check=False,
            enable_resolution_check=True,
            enable_interactive_confirmation=False,
            auto_update_status=True,
            min_importance_for_high_severity=3,
        )

        assert not config.enable_planting_check
        assert config.enable_resolution_check
        assert not config.enable_interactive_confirmation
        assert config.auto_update_status
        assert config.min_importance_for_high_severity == 3

    @pytest.mark.spec("SPEC-FORESHADOWING_ISSUE-INVALID_MIN_IMPORTAN")
    def test_invalid_min_importance(self):
        """最小重要度範囲外エラー"""
        with pytest.raises(ValueError, match="最小重要度は1-5の範囲である必要があります"):
            ForeshadowingValidationConfig(min_importance_for_high_severity=0)

        with pytest.raises(ValueError, match="最小重要度は1-5の範囲である必要があります"):
            ForeshadowingValidationConfig(min_importance_for_high_severity=6)
