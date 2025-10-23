#!/usr/bin/env python3
"""品質チェックセッションのテスト(TDD - RED段階)

品質チェックドメインのルートアグリゲートをテスト駆動で開発する。


仕様書: SPEC-DOMAIN-ENTITIES
"""

import uuid
from datetime import datetime

import pytest

from noveler.domain.entities.quality_check_session import (
    CheckType,
    QualityCheckResult,
    QualityCheckSession,
    QualityGrade,
    QualityIssue,
    QualityScore,
    Severity,
)
from noveler.domain.value_objects.file_content import FileContent
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestQualityCheckSession:
    """品質チェックセッションのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECK_SESSION-CREATE_SESSION")
    def test_create_session(self) -> None:
        """セッションを作成できる"""
        # Given
        session_id = str(uuid.uuid4())
        project_id = "test_project"
        content = FileContent(
            filepath="第001話_テスト.md",
            content="これはテストコンテンツです。",
            encoding="utf-8",
        )

        # When
        session = QualityCheckSession(
            session_id=session_id,
            project_id=project_id,
            target_content=content,
        )

        # Then
        assert session.session_id == session_id
        assert session.project_id == project_id
        assert session.target_content == content
        assert session.status == "pending"
        assert isinstance(session.created_at, datetime)
        assert len(session.check_results) == 0

    @pytest.mark.spec("SPEC-QUALITY_CHECK_SESSION-ADD_CHECK_RESULT")
    def test_add_check_result(self) -> None:
        """チェック結果を追加できる"""
        # Given
        session = self._create_test_session()
        result = QualityCheckResult(
            check_type=CheckType.BASIC_STYLE,
            score=QualityScore(85.0),
            issues=[
                QualityIssue(
                    type="punctuation",
                    message="句読点の重複があります",
                    severity=Severity.ERROR,
                    line_number=10,
                    position=15,
                )
            ],
            metadata={"checked_at": project_now().datetime.isoformat()},
        )

        # When
        session.add_check_result(result)

        # Then
        assert len(session.check_results) == 1
        assert session.check_results[0] == result
        assert session.has_check_type(CheckType.BASIC_STYLE)

    @pytest.mark.spec("SPEC-QUALITY_CHECK_SESSION-CALCULATE_TOTAL_SCOR")
    def test_calculate_total_score(self) -> None:
        """総合スコアを計算できる"""
        # Given
        session = self._create_test_session()

        # 各チェック結果を追加
        session.add_check_result(
            QualityCheckResult(
                check_type=CheckType.BASIC_STYLE,
                score=QualityScore(80.0),
                issues=[],
            )
        )

        session.add_check_result(
            QualityCheckResult(
                check_type=CheckType.COMPOSITION,
                score=QualityScore(90.0),
                issues=[],
            )
        )

        session.add_check_result(
            QualityCheckResult(
                check_type=CheckType.CHARACTER_CONSISTENCY,
                score=QualityScore(85.0),
                issues=[],
            )
        )

        # When
        total_score = session.calculate_total_score()

        # Then
        assert isinstance(total_score, QualityScore)
        assert 80.0 <= total_score.value <= 90.0  # 重み付け平均の範囲

    @pytest.mark.spec("SPEC-QUALITY_CHECK_SESSION-DETERMINE_GRADE")
    def test_determine_grade(self) -> None:
        """品質グレードを判定できる"""
        # Given
        session = self._create_test_session()

        # S級のスコアを設定
        session.add_check_result(
            QualityCheckResult(
                check_type=CheckType.BASIC_STYLE,
                score=QualityScore(95.0),
                issues=[],
            )
        )

        # When
        grade = session.determine_grade()

        # Then
        assert grade == QualityGrade.S

    @pytest.mark.spec("SPEC-QUALITY_CHECK_SESSION-GET_ALL_ISSUES")
    def test_get_all_issues(self) -> None:
        """全ての問題を取得できる"""
        # Given
        session = self._create_test_session()

        issue1 = QualityIssue(
            type="punctuation",
            message="句読点エラー",
            severity=Severity.ERROR,
        )

        issue2 = QualityIssue(
            type="length",
            message="文章が短すぎます",
            severity=Severity.WARNING,
        )

        session.add_check_result(
            QualityCheckResult(
                check_type=CheckType.BASIC_STYLE,
                score=QualityScore(70.0),
                issues=[issue1],
            )
        )

        session.add_check_result(
            QualityCheckResult(
                check_type=CheckType.COMPOSITION,
                score=QualityScore(60.0),
                issues=[issue2],
            )
        )

        # When
        all_issues = session.get_all_issues()

        # Then
        assert len(all_issues) == 2
        assert issue1 in all_issues
        assert issue2 in all_issues

    @pytest.mark.spec("SPEC-QUALITY_CHECK_SESSION-GET_ISSUES_BY_SEVERI")
    def test_get_issues_by_severity(self) -> None:
        """重要度別に問題を取得できる"""
        # Given
        session = self._create_test_session()

        error_issue = QualityIssue(
            type="punctuation",
            message="エラー",
            severity=Severity.ERROR,
        )

        warning_issue = QualityIssue(
            type="length",
            message="警告",
            severity=Severity.WARNING,
        )

        session.add_check_result(
            QualityCheckResult(
                check_type=CheckType.BASIC_STYLE,
                score=QualityScore(70.0),
                issues=[error_issue, warning_issue],
            )
        )

        # When
        errors = session.get_issues_by_severity(Severity.ERROR)
        warnings = session.get_issues_by_severity(Severity.WARNING)

        # Then
        assert len(errors) == 1
        assert errors[0] == error_issue
        assert len(warnings) == 1
        assert warnings[0] == warning_issue

    @pytest.mark.spec("SPEC-QUALITY_CHECK_SESSION-COMPLETE_SESSION")
    def test_complete_session(self) -> None:
        """セッションを完了できる"""
        # Given
        session = self._create_test_session()
        session.add_check_result(
            QualityCheckResult(
                check_type=CheckType.BASIC_STYLE,
                score=QualityScore(80.0),
                issues=[],
            )
        )

        # When
        session.complete()

        # Then
        assert session.status == "completed"
        assert session.completed_at is not None
        assert isinstance(session.completed_at, datetime)

    @pytest.mark.spec("SPEC-QUALITY_CHECK_SESSION-CANNOT_ADD_RESULT_AF")
    def test_cannot_add_result_after_completion(self) -> None:
        """完了後は結果を追加できない"""
        # Given
        session = self._create_test_session()
        session.complete()

        # When/Then
        with pytest.raises(ValueError, match="完了したセッションには結果を追加できません"):
            session.add_check_result(
                QualityCheckResult(
                    check_type=CheckType.BASIC_STYLE,
                    score=QualityScore(80.0),
                    issues=[],
                )
            )

    @pytest.mark.spec("SPEC-QUALITY_CHECK_SESSION-EXPORT_SUMMARY")
    def test_export_summary(self) -> None:
        """サマリーをエクスポートできる"""
        # Given
        session = self._create_test_session()
        session.add_check_result(
            QualityCheckResult(
                check_type=CheckType.BASIC_STYLE,
                score=QualityScore(85.0),
                issues=[
                    QualityIssue(
                        type="punctuation",
                        message="句読点エラー",
                        severity=Severity.ERROR,
                    )
                ],
            )
        )

        session.complete()

        # When
        summary = session.export_summary()

        # Then
        assert summary["session_id"] == session.session_id
        assert summary["project_id"] == session.project_id
        assert summary["status"] == "completed"
        assert "total_score" in summary
        assert "grade" in summary
        assert "check_results" in summary
        assert len(summary["check_results"]) == 1
        assert summary["error_count"] == 1
        assert summary["warning_count"] == 0

    def _create_test_session(self) -> QualityCheckSession:
        """テスト用セッションを作成"""
        return QualityCheckSession(
            session_id=str(uuid.uuid4()),
            project_id="test_project",
            target_content=FileContent(
                filepath="test.md",
                content="テストコンテンツ",
                encoding="utf-8",
            ),
        )


class TestQualityScore:
    """品質スコアのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECK_SESSION-CREATE_VALID_SCORE")
    def test_create_valid_score(self) -> None:
        """有効なスコアを作成できる"""
        score = QualityScore(85.5)
        assert score.value == 85.5

    @pytest.mark.spec("SPEC-QUALITY_CHECK_SESSION-SCORE_MUST_BE_IN_RAN")
    def test_score_must_be_in_range(self) -> None:
        """スコアは0-100の範囲内である必要がある"""
        with pytest.raises(ValueError, match="スコアは0-100の範囲内である必要があります"):
            QualityScore(-1)

        with pytest.raises(ValueError, match="スコアは0-100の範囲内である必要があります"):
            QualityScore(101)

    @pytest.mark.spec("SPEC-QUALITY_CHECK_SESSION-SCORE_COMPARISON")
    def test_score_comparison(self) -> None:
        """スコアを比較できる"""
        score1 = QualityScore(80.0)
        score2 = QualityScore(90.0)

        assert score1 < score2
        assert score2 > score1
        assert score1 != score2

    @pytest.mark.spec("SPEC-QUALITY_CHECK_SESSION-SCORE_TO_GRADE")
    def test_score_to_grade(self) -> None:
        """スコアからグレードを判定できる"""
        assert QualityScore(95.0).to_grade() == QualityGrade.S
        assert QualityScore(85.0).to_grade() == QualityGrade.A
        assert QualityScore(75.0).to_grade() == QualityGrade.B
        assert QualityScore(65.0).to_grade() == QualityGrade.C
        assert QualityScore(45.0).to_grade() == QualityGrade.D


class TestQualityGrade:
    """品質グレードのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECK_SESSION-GRADE_ORDERING")
    def test_grade_ordering(self) -> None:
        """グレードを順序付けできる"""
        assert QualityGrade.S > QualityGrade.A
        assert QualityGrade.A > QualityGrade.B
        assert QualityGrade.B > QualityGrade.C
        assert QualityGrade.C > QualityGrade.D

    @pytest.mark.spec("SPEC-QUALITY_CHECK_SESSION-GRADE_DISPLAY_NAME")
    def test_grade_display_name(self) -> None:
        """グレードの表示名を取得できる"""
        assert QualityGrade.S.display_name == "S級(秀逸)"
        assert QualityGrade.A.display_name == "A級(優良)"
        assert QualityGrade.B.display_name == "B級(標準)"
        assert QualityGrade.C.display_name == "C級(要改善)"
        assert QualityGrade.D.display_name == "D級(要大幅改善)"
