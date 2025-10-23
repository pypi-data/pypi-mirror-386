#!/usr/bin/env python3
"""
伏線検証ドメインサービスのテスト
SPEC-FORESHADOWING-001準拠
"""

from unittest.mock import Mock

import pytest

from noveler.domain.services.foreshadowing_validation_service import ForeshadowingValidationService


@pytest.mark.spec("SPEC-FORESHADOWING-001")
class TestForeshadowingValidationService:
    """伏線検証ドメインサービスのテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.mock_repository = Mock()
        self.service = ForeshadowingValidationService(self.mock_repository)

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SERVICE-CREATE_VALIDATION_SE")
    def test_create_validation_session(self):
        """検証セッション作成テスト"""
        # モック伏線作成
        mock_foreshadowing = Mock()
        mock_foreshadowing.id = "F001"
        mock_foreshadowing.title = "テスト伏線"

        mock_planting = Mock()
        mock_planting.episode = "第005話"
        mock_foreshadowing.planting = mock_planting
        mock_foreshadowing.hints = []  # hintsが存在しない場合もテストするため空リスト

        self.mock_repository.load_all.return_value = [mock_foreshadowing]

        # セッション作成
        session = self.service.create_validation_session(
            project_id="test_project", episode_number=5, manuscript_content="テスト原稿", config=None
        )

        # 検証
        self.mock_repository.load_all.assert_called_once_with("test_project")
        assert session.project_id == "test_project"
        assert session.episode_number == 5
        assert session.manuscript_content == "テスト原稿"
        assert len(session.foreshadowing_list) == 1  # 該当エピソードの伏線のみ

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SERVICE-FILTER_RELEVANT_FORE")
    def test_filter_relevant_foreshadowing_planting(self):
        """仕込み予定伏線の抽出"""
        # エピソード5仕込み予定の伏線
        relevant_foreshadowing = Mock()
        relevant_foreshadowing.id = "F001"
        relevant_planting = Mock()
        relevant_planting.episode = "第005話"
        relevant_foreshadowing.planting = relevant_planting
        relevant_foreshadowing.hints = []  # hintsが存在しない場合もテストするため空リスト

        # 他エピソードの伏線
        irrelevant_foreshadowing = Mock()
        irrelevant_foreshadowing.id = "F002"
        irrelevant_planting = Mock()
        irrelevant_planting.episode = "第010話"
        irrelevant_foreshadowing.planting = irrelevant_planting
        irrelevant_foreshadowing.hints = []  # hintsが存在しない場合もテストするため空リスト

        all_foreshadowing = [relevant_foreshadowing, irrelevant_foreshadowing]
        self.mock_repository.load_all.return_value = all_foreshadowing

        session = self.service.create_validation_session(
            project_id="test_project", episode_number=5, manuscript_content="テスト原稿"
        )

        # エピソード5関連の伏線のみ抽出されること
        assert len(session.foreshadowing_list) == 1
        assert session.foreshadowing_list[0].id == "F001"

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SERVICE-FILTER_RELEVANT_FORE")
    def test_filter_relevant_foreshadowing_resolution(self):
        """回収予定伏線の抽出"""
        # エピソード5回収予定の伏線
        relevant_foreshadowing = Mock()
        relevant_foreshadowing.id = "F003"
        relevant_resolution = Mock()
        relevant_resolution.episode = "第005話"
        relevant_foreshadowing.resolution = relevant_resolution
        relevant_foreshadowing.hints = []  # hintsが存在しない場合もテストするため空リスト

        all_foreshadowing = [relevant_foreshadowing]
        self.mock_repository.load_all.return_value = all_foreshadowing

        session = self.service.create_validation_session(
            project_id="test_project", episode_number=5, manuscript_content="テスト原稿"
        )

        assert len(session.foreshadowing_list) == 1
        assert session.foreshadowing_list[0].id == "F003"

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SERVICE-FILTER_RELEVANT_FORE")
    def test_filter_relevant_foreshadowing_hints(self):
        """ヒント予定伏線の抽出"""
        # エピソード5でヒント予定の伏線
        relevant_foreshadowing = Mock()
        relevant_foreshadowing.id = "F004"
        relevant_foreshadowing.hints = [
            {"episode": "第005話", "content": "小さなヒント"},
            {"episode": "第010話", "content": "別のヒント"},
        ]

        all_foreshadowing = [relevant_foreshadowing]
        self.mock_repository.load_all.return_value = all_foreshadowing

        session = self.service.create_validation_session(
            project_id="test_project", episode_number=5, manuscript_content="テスト原稿"
        )

        assert len(session.foreshadowing_list) == 1
        assert session.foreshadowing_list[0].id == "F004"

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SERVICE-VALIDATE_EPISODE_FOR")
    def test_validate_episode_foreshadowing(self):
        """エピソード伏線検証テスト"""
        # 完了済みセッションの場合
        completed_session = Mock()
        completed_session.is_completed.return_value = True
        completed_session.validation_result = "既存結果"

        result = self.service.validate_episode_foreshadowing(completed_session)
        assert result == "既存結果"

        # 未完了セッションの場合
        incomplete_session = Mock()
        incomplete_session.is_completed.return_value = False
        mock_result = Mock()
        incomplete_session.validate_foreshadowing.return_value = mock_result

        result = self.service.validate_episode_foreshadowing(incomplete_session)
        incomplete_session.validate_foreshadowing.assert_called_once()
        assert result == mock_result

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SERVICE-UPDATE_FORESHADOWING")
    def test_update_foreshadowing_implementation_status_valid_transition(self):
        """有効なステータス遷移での更新"""
        # 存在する伏線をモック
        mock_foreshadowing = Mock()
        mock_foreshadowing.status.value = "planned"
        self.mock_repository.find_by_id.return_value = mock_foreshadowing

        result = self.service.update_foreshadowing_implementation_status(
            project_id="test_project", foreshadowing_id="F001", new_status="planted", _implementation_note="実装しました"
        )

        self.mock_repository.find_by_id.assert_called_once_with("F001", "test_project")
        assert result

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SERVICE-UPDATE_FORESHADOWING")
    def test_update_foreshadowing_implementation_status_invalid_transition(self):
        """無効なステータス遷移での更新"""
        # resolved状態の伏線
        mock_foreshadowing = Mock()
        mock_foreshadowing.status.value = "resolved"
        self.mock_repository.find_by_id.return_value = mock_foreshadowing

        result = self.service.update_foreshadowing_implementation_status(
            project_id="test_project",
            foreshadowing_id="F001",
            new_status="planted",  # resolved → planted は無効
            _implementation_note="実装しました",
        )

        assert not result

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SERVICE-UPDATE_FORESHADOWING")
    def test_update_foreshadowing_implementation_status_not_found(self):
        """存在しない伏線の更新"""
        self.mock_repository.find_by_id.return_value = None

        result = self.service.update_foreshadowing_implementation_status(
            project_id="test_project", foreshadowing_id="F999", new_status="planted"
        )

        assert not result

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SERVICE-VALIDATE_STATUS_TRAN")
    def test_validate_status_transition_valid_cases(self):
        """有効なステータス遷移パターン"""
        service = self.service

        # planned → planted
        assert service._validate_status_transition("planned", "planted")

        # planted → resolved
        assert service._validate_status_transition("planted", "resolved")

        # planted → ready_to_resolve
        assert service._validate_status_transition("planted", "ready_to_resolve")

        # ready_to_resolve → resolved
        assert service._validate_status_transition("ready_to_resolve", "resolved")

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SERVICE-VALIDATE_STATUS_TRAN")
    def test_validate_status_transition_invalid_cases(self):
        """無効なステータス遷移パターン"""
        service = self.service

        # planned → resolved (planted をスキップ)
        assert not service._validate_status_transition("planned", "resolved")

        # resolved → planted (逆方向)
        assert not service._validate_status_transition("resolved", "planted")

        # resolved → any (完了後は変更不可)
        assert not service._validate_status_transition("resolved", "ready_to_resolve")

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SERVICE-GENERATE_IMPROVEMENT")
    def test_generate_improvement_suggestions_planting(self):
        """仕込み改善提案生成"""
        # 仕込み漏れ問題を作成
        planting_issue = Mock()
        planting_issue.foreshadowing_id = "F001"
        planting_issue.expected_content = "森の動物が騒がしい"
        planting_issue.suggestion = "環境描写で表現してください"

        mock_result = Mock()
        mock_result.get_planting_issues.return_value = [planting_issue]
        mock_result.get_resolution_issues.return_value = []

        suggestions = self.service.generate_improvement_suggestions(mock_result)

        assert len(suggestions) == 2
        assert "💡 F001: 森の動物が騒がしい を仕込んでください" in suggestions
        assert "   環境描写で表現してください" in suggestions

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SERVICE-GENERATE_IMPROVEMENT")
    def test_generate_improvement_suggestions_resolution(self):
        """回収改善提案生成"""
        # 回収漏れ問題を作成
        resolution_issue = Mock()
        resolution_issue.foreshadowing_id = "F002"
        resolution_issue.expected_content = "あの時の異変の正体が判明"
        resolution_issue.suggestion = "衝撃的な真実の暴露で"

        mock_result = Mock()
        mock_result.get_planting_issues.return_value = []
        mock_result.get_resolution_issues.return_value = [resolution_issue]

        suggestions = self.service.generate_improvement_suggestions(mock_result)

        assert len(suggestions) == 2
        assert "🎯 F002: あの時の異変の正体が判明 で回収してください" in suggestions
        assert "   衝撃的な真実の暴露で" in suggestions

    @pytest.mark.spec("SPEC-FORESHADOWING_VALIDATION_SERVICE-EXTRACT_EPISODE_NUMB")
    def test_extract_episode_number_method(self):
        """エピソード番号抽出メソッドテスト"""
        service = self.service

        assert service._extract_episode_number("第001話") == 1
        assert service._extract_episode_number("第005話") == 5
        assert service._extract_episode_number("第100話") == 100
        assert service._extract_episode_number("無効な形式") == 0
        assert service._extract_episode_number("") == 0
