#!/usr/bin/env python3
"""
伏線検証セッションエンティティのテスト
SPEC-FORESHADOWING-001準拠
"""

from unittest.mock import Mock

import pytest
pytestmark = pytest.mark.quality_domain

from noveler.domain.entities.foreshadowing_validation_session import ForeshadowingValidationSession
from noveler.domain.value_objects.foreshadowing_issue import (
    ForeshadowingIssueType,
    ForeshadowingSeverity,
    ForeshadowingValidationConfig,
)


@pytest.mark.spec("SPEC-FORESHADOWING-001")
class TestForeshadowingValidationSession:
    """伏線検証セッションエンティティのテスト"""

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SESSION-VALID_SESSION_CREATI")
    def test_valid_session_creation(self):
        """正常なセッション作成"""
        session = ForeshadowingValidationSession(
            project_id="test_project",
            episode_number=5,
            manuscript_content="テスト原稿内容",
            foreshadowing_list=[],
            config=ForeshadowingValidationConfig(),
        )

        assert session.project_id == "test_project"
        assert session.episode_number == 5
        assert session.manuscript_content == "テスト原稿内容"
        assert session.session_id is not None
        assert not session.is_completed()

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SESSION-INVALID_EPISODE_NUMB")
    def test_invalid_episode_number(self):
        """無効なエピソード番号"""
        with pytest.raises(ValueError, match="エピソード番号は1以上である必要があります"):
            ForeshadowingValidationSession(project_id="test_project", episode_number=0, manuscript_content="テスト原稿")

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SESSION-VALIDATE_FORESHADOWI")
    def test_validate_foreshadowing_planting_issue(self):
        """仕込み漏れ検知テスト"""
        # モック伏線作成(仕込み予定だが未実装)
        mock_foreshadowing = Mock()
        mock_foreshadowing.id = "F001"
        mock_foreshadowing.title = "テスト伏線"
        mock_foreshadowing.importance = 5
        mock_foreshadowing.status.value = "planned"

        # 仕込み情報をモック
        mock_planting = Mock()
        mock_planting.episode = "第005話"
        mock_planting.content = "森の動物が騒がしい"
        mock_planting.method = "環境描写"
        mock_foreshadowing.planting = mock_planting

        session = ForeshadowingValidationSession(
            project_id="test_project",
            episode_number=5,
            manuscript_content="平和な森の風景が広がっていた",  # 伏線なし
            foreshadowing_list=[mock_foreshadowing],
        )

        result = session.validate_foreshadowing()

        assert result.has_issues()
        assert len(result.issues) == 1
        assert result.issues[0].issue_type == ForeshadowingIssueType.MISSING_PLANTING
        assert result.issues[0].severity == ForeshadowingSeverity.HIGH  # importance=5
        assert result.issues[0].foreshadowing_id == "F001"

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SESSION-VALIDATE_FORESHADOWI")
    def test_validate_foreshadowing_resolution_issue(self):
        """回収漏れ検知テスト"""
        # モック伏線作成(回収予定だが未実装)
        mock_foreshadowing = Mock()
        mock_foreshadowing.id = "F002"
        mock_foreshadowing.title = "テスト回収伏線"
        mock_foreshadowing.importance = 3
        mock_foreshadowing.status.value = "planted"

        # 回収情報をモック
        mock_resolution = Mock()
        mock_resolution.episode = "第005話"
        mock_resolution.content = "あの時の異変の正体が判明した"
        mock_resolution.method = "真実の暴露"
        mock_foreshadowing.resolution = mock_resolution

        session = ForeshadowingValidationSession(
            project_id="test_project",
            episode_number=5,
            manuscript_content="普通の日常が続いていた",  # 回収なし
            foreshadowing_list=[mock_foreshadowing],
        )

        result = session.validate_foreshadowing()

        assert result.has_issues()
        assert result.has_critical_issues()
        assert len(result.issues) == 1
        assert result.issues[0].issue_type == ForeshadowingIssueType.MISSING_RESOLUTION
        assert result.issues[0].severity == ForeshadowingSeverity.CRITICAL
        assert result.issues[0].foreshadowing_id == "F002"

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SESSION-VALIDATE_FORESHADOWI")
    def test_validate_foreshadowing_no_issues(self):
        """問題なしの検証"""
        mock_foreshadowing = Mock()
        mock_foreshadowing.id = "F003"
        mock_foreshadowing.title = "無関係伏線"
        mock_foreshadowing.status.value = "planned"

        mock_planting = Mock()
        mock_planting.episode = "第010話"  # 別エピソード
        mock_foreshadowing.planting = mock_planting

        session = ForeshadowingValidationSession(
            project_id="test_project",
            episode_number=5,
            manuscript_content="テスト原稿",
            foreshadowing_list=[mock_foreshadowing],
        )

        result = session.validate_foreshadowing()

        assert not result.has_issues()
        assert len(result.issues) == 0
        assert result.total_foreshadowing_checked == 1

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SESSION-SEVERITY_DETERMINATI")
    def test_severity_determination_by_importance(self):
        """重要度による深刻度判定"""
        config = ForeshadowingValidationConfig(min_importance_for_high_severity=4)

        # 重要度5(HIGH)
        mock_high_importance = Mock()
        mock_high_importance.id = "F001"
        mock_high_importance.title = "高重要度伏線"
        mock_high_importance.importance = 5
        mock_high_importance.status.value = "planned"

        mock_planting_high = Mock()
        mock_planting_high.episode = "第005話"
        mock_planting_high.content = "重要な手がかり"
        mock_planting_high.method = "台詞"
        mock_high_importance.planting = mock_planting_high

        # 重要度2(MEDIUM)
        mock_medium_importance = Mock()
        mock_medium_importance.id = "F002"
        mock_medium_importance.title = "低重要度伏線"
        mock_medium_importance.importance = 2
        mock_medium_importance.status.value = "planned"

        mock_planting_medium = Mock()
        mock_planting_medium.episode = "第005話"
        mock_planting_medium.content = "ちょっとした言及"
        mock_planting_medium.method = "描写"
        mock_medium_importance.planting = mock_planting_medium

        session = ForeshadowingValidationSession(
            project_id="test_project",
            episode_number=5,
            manuscript_content="何もない原稿",
            foreshadowing_list=[mock_high_importance, mock_medium_importance],
            config=config,
        )

        result = session.validate_foreshadowing()

        assert len(result.issues) == 2

        # 重要度による深刻度の確認
        high_severity_issues = result.get_issues_by_severity(ForeshadowingSeverity.HIGH)
        medium_severity_issues = result.get_issues_by_severity(ForeshadowingSeverity.MEDIUM)

        assert len(high_severity_issues) == 1
        assert len(medium_severity_issues) == 1
        assert high_severity_issues[0].foreshadowing_id == "F001"
        assert medium_severity_issues[0].foreshadowing_id == "F002"

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SESSION-EXTRACT_EPISODE_NUMB")
    def test_extract_episode_number(self):
        """エピソード番号抽出テスト"""
        session = ForeshadowingValidationSession(project_id="test_project", episode_number=1, manuscript_content="test")

        assert session._extract_episode_number("第005話") == 5
        assert session._extract_episode_number("第001話") == 1
        assert session._extract_episode_number("第100話") == 100
        assert session._extract_episode_number("無効な形式") == 0

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SESSION-SESSION_COMPLETION_S")
    def test_session_completion_state(self):
        """セッション完了状態管理"""
        session = ForeshadowingValidationSession(
            project_id="test_project", episode_number=5, manuscript_content="テスト原稿", foreshadowing_list=[]
        )

        # 初期状態は未完了
        assert not session.is_completed()
        assert session.completed_at is None

        # 検証実行で完了状態になる
        result = session.validate_foreshadowing()

        assert session.is_completed()
        assert session.completed_at is not None
        assert session.validation_result == result

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SESSION-DUPLICATE_VALIDATION")
    def test_duplicate_validation_error(self):
        """重複検証エラー"""
        session = ForeshadowingValidationSession(
            project_id="test_project", episode_number=5, manuscript_content="テスト原稿", foreshadowing_list=[]
        )

        # 一度検証実行
        session.validate_foreshadowing()

        # 再実行でエラー
        with pytest.raises(ValueError, match="既に完了したセッションです"):
            session.validate_foreshadowing()

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SESSION-GET_VALIDATION_SUMMA")
    def test_get_validation_summary(self):
        """検証サマリー取得"""
        session = ForeshadowingValidationSession(
            project_id="test_project", episode_number=5, manuscript_content="テスト原稿", foreshadowing_list=[]
        )

        # 検証前
        assert session.get_validation_summary() == "検証未実行"

        # 検証後
        session.validate_foreshadowing()
        summary = session.get_validation_summary()

        assert "エピソード5" in summary
        assert "問題なし" in summary
