#!/usr/bin/env python3
"""Claude Code連携評価サービス単体テスト(TDD実装)

Claude Code連携評価サービスのビジネスロジックをテスト。
モックを使用してClaude Code連携部分を分離したテスト。
"""

from unittest.mock import MagicMock, Mock as mock_Path, patch

import pytest


from noveler.domain.entities.a31_checklist_item import A31ChecklistItem, ChecklistItemType
from noveler.domain.services.claude_code_evaluation_service import (
    ClaudeCodeEvaluationRequest,
    ClaudeCodeEvaluationResponse,
    ClaudeCodeEvaluationService,
)
from noveler.domain.interfaces.claude_session_interface import (
    ClaudeSessionExecutorInterface,
    EnvironmentDetectorInterface,
)
from noveler.domain.value_objects.a31_threshold import Threshold, ThresholdType
from noveler.domain.value_objects.file_path import FilePath


@pytest.fixture
def sample_checklist_item() -> A31ChecklistItem:
    """テスト用チェックリスト項目"""
    from noveler.domain.value_objects.a31_auto_fix_strategy import AutoFixStrategy

    return A31ChecklistItem(
        item_id="A31-001",
        title="A30_原稿執筆ガイド.mdの内容を確認",
        item_type=ChecklistItemType.DOCUMENT_REVIEW,
        required=True,
        threshold=Threshold(ThresholdType.BOOLEAN, 1.0),
        auto_fix_strategy=AutoFixStrategy.create_manual_strategy(),
    )


@pytest.fixture
def sample_evaluation_request(sample_checklist_item: A31ChecklistItem) -> ClaudeCodeEvaluationRequest:
    """テスト用評価リクエスト"""
    return ClaudeCodeEvaluationRequest(
        item=sample_checklist_item,
        episode_file_path=FilePath("test_episode.md"),
        context_files=[FilePath("A30_原稿執筆ガイド.md")],
        metadata={"project_name": "test_project", "episode_number": 1},
    )


@pytest.fixture
def claude_code_evaluation_service() -> ClaudeCodeEvaluationService:
    """テスト用Claude Code評価サービス"""
    session_executor = MagicMock(spec=ClaudeSessionExecutorInterface)
    session_executor.is_available.return_value = True
    session_executor.execute_prompt.return_value = {"success": True, "data": {}}

    environment_detector = MagicMock(spec=EnvironmentDetectorInterface)
    environment_detector.is_claude_code_environment.return_value = True
    environment_detector.get_current_project_name.return_value = "テストプロジェクト"

    return ClaudeCodeEvaluationService(
        session_executor=session_executor,
        environment_detector=environment_detector,
    )


class TestClaudeCodeEvaluationService:
    """Claude Code連携評価サービステスト"""

    @pytest.mark.spec("SPEC-A31-002")
    def test_evaluate_item_success(
        self,
        claude_code_evaluation_service: ClaudeCodeEvaluationService,
        sample_evaluation_request: ClaudeCodeEvaluationRequest,
    ) -> None:
        """正常評価のテスト"""
        # Given: 正常なファイル読み込みとClaude Codeレスポンス
        episode_content = "これはテストエピソードです。\n良い冒頭が書かれています。"
        # guide_content = "冒頭の技法について説明..."  # 未使用のため削除

        with patch("builtins.open", mock_Path(read_data=episode_content).open()):
            with patch.object(claude_code_evaluation_service, "_query_claude_code") as mock_query:
                # Claude Codeの正常レスポンス
                mock_query.return_value = {
                    "id": "A31-001",
                    "title": "A30_原稿執筆ガイド.mdの内容を確認",
                    "status": True,
                    "required": True,
                    "type": "document_review",
                    "auto_fix_supported": False,
                    "auto_fix_applied": False,
                    "fix_details": [],
                    "claude_evaluation": {
                        "evaluated_at": "2025-08-03T10:35:00",
                        "result": "PASS",
                        "score": 85.0,
                        "confidence": 0.9,
                        "primary_reason": "ガイド内容が適切に理解・適用されている",
                        "evidence_points": [
                            {
                                "content": "冒頭で読者を引き込む工夫が確認できる",
                                "line_range": [1, 2],
                                "file": "test_episode.md",
                            }
                        ],
                        "improvement_suggestions": [],
                        "issues_found": [],
                        "references_validated": [
                            {
                                "guide": "A30_原稿執筆ガイド.md",
                                "section": "冒頭の技法",
                                "applied_at_lines": [1, 2],
                                "compliance_score": 90,
                            }
                        ],
                    },
                }

                # When: 評価実行
                result = claude_code_evaluation_service.evaluate_item(sample_evaluation_request)

                # Then: 正常な評価結果が返される
                assert result.item_id == "A31-001"
                assert result.current_score == 85.0
                assert result.passed is True
                assert result.details["evaluation_method"] == "claude_code_auto"
                assert result.details["confidence"] == 0.9
                assert result.details["evidence_count"] == 1

                # プロンプトが正しく構築されている
                mock_query.assert_called_once()
                prompt_arg = mock_query.call_args[0][0]
                assert "A31-001" in prompt_arg
                assert "A30_原稿執筆ガイド.mdの内容を確認" in prompt_arg
                assert "yaml" in prompt_arg.lower()

    @pytest.mark.spec("SPEC-A31-002")
    def test_evaluate_item_file_not_found(
        self,
        claude_code_evaluation_service: ClaudeCodeEvaluationService,
        sample_evaluation_request: ClaudeCodeEvaluationRequest,
    ) -> None:
        """ファイル未発見時のテスト"""
        # Given: ファイルが存在しない
        with patch("builtins.open", side_effect=FileNotFoundError):
            with patch.object(claude_code_evaluation_service, "_query_claude_code") as mock_query:
                mock_query.return_value = {
                    "id": "A31-001",
                    "status": False,
                    "claude_evaluation": {
                        "result": "FAIL",
                        "score": 0.0,
                        "confidence": 1.0,
                        "primary_reason": "エピソードファイルが見つからない",
                    },
                }

                # When: 評価実行
                result = claude_code_evaluation_service.evaluate_item(sample_evaluation_request)

                # Then: ファイル未発見でも適切に処理される
                assert result.item_id == "A31-001"
                assert result.current_score == 0.0
                assert result.passed is False

    @pytest.mark.spec("SPEC-A31-002")
    def test_build_evaluation_prompt_structure(
        self,
        claude_code_evaluation_service: ClaudeCodeEvaluationService,
        sample_checklist_item: A31ChecklistItem,
    ) -> None:
        """評価プロンプト構築のテスト"""
        # Given: コンテキストデータ
        context_data = {
            "episode_file": "test_episode.md",
            "episode_content": "これはテスト内容です。",
            "related_content": {"A30_原稿執筆ガイド.md": "ガイドの内容..."},
        }

        # When: プロンプト構築
        prompt = claude_code_evaluation_service._build_evaluation_prompt(
            sample_checklist_item,
            context_data,
        )

        # Then: 適切なプロンプトが構築される
        assert "A31-001" in prompt
        assert "A30_原稿執筆ガイド.mdの内容を確認" in prompt
        assert "yaml" in prompt.lower()
        assert "行数" in prompt
        assert "evidence_points" in prompt
        assert "improvement_suggestions" in prompt
        assert "issues_found" in prompt
        assert "これはテスト内容です。" in prompt

    @pytest.mark.spec("SPEC-A31-002")
    def test_get_item_specific_prompt(
        self,
        claude_code_evaluation_service: ClaudeCodeEvaluationService,
    ) -> None:
        """項目別詳細プロンプト取得のテスト"""
        # When: 既知項目の詳細プロンプト取得
        prompt_a31_001 = claude_code_evaluation_service._get_item_specific_prompt("A31-001")
        prompt_a31_012 = claude_code_evaluation_service._get_item_specific_prompt("A31-012")
        prompt_unknown = claude_code_evaluation_service._get_item_specific_prompt("A31-999")

        # Then: 項目別の詳細指針が取得される
        assert "冒頭3行" in prompt_a31_001
        assert "A30_原稿執筆ガイド.md" in prompt_a31_001

        assert "前話からの" in prompt_a31_012
        assert "連続性" in prompt_a31_012

        assert prompt_unknown == ""  # 未知項目は空文字列

    @pytest.mark.spec("SPEC-A31-002")
    def test_format_related_files(
        self,
        claude_code_evaluation_service: ClaudeCodeEvaluationService,
    ) -> None:
        """関連ファイル情報フォーマットのテスト"""
        # Given: 関連ファイル内容
        related_content = {
            "file1.md": "短いコンテンツ",
            "file2.md": "長い" * 300 + "コンテンツ",  # 500文字超過
        }

        # When: フォーマット実行
        formatted = claude_code_evaluation_service._format_related_files(related_content)

        # Then: 適切にフォーマットされる
        assert "file1.md" in formatted
        assert "短いコンテンツ" in formatted
        assert "file2.md" in formatted
        assert "..." in formatted  # 長いコンテンツは省略される

        # 空の場合のテスト
        empty_formatted = claude_code_evaluation_service._format_related_files({})
        assert empty_formatted == "関連ファイルなし"


class TestClaudeCodeEvaluationResponse:
    """Claude Code評価レスポンステスト"""

    @pytest.mark.spec("SPEC-A31-002")
    def test_from_yaml_response(self) -> None:
        """YAMLレスポンスからの作成テスト"""
        # Given: YAMLレスポンスデータ
        yaml_data = {
            "id": "A31-001",
            "status": True,
            "claude_evaluation": {
                "result": "PASS",
                "score": 85.0,
                "confidence": 0.9,
            },
        }

        # When: レスポンス作成
        response = ClaudeCodeEvaluationResponse.from_yaml_response(yaml_data)

        # Then: 適切にレスポンスが作成される
        assert response.item_id == "A31-001"
        assert response.status is True
        assert response.claude_evaluation["result"] == "PASS"
        assert response.claude_evaluation["score"] == 85.0
        assert response.claude_evaluation["confidence"] == 0.9


class TestClaudeCodeEvaluationRequest:
    """Claude Code評価リクエストテスト"""

    @pytest.mark.spec("SPEC-A31-002")
    def test_request_creation(self, sample_checklist_item: A31ChecklistItem) -> None:
        """リクエスト作成のテスト"""
        # Given: リクエストパラメータ
        episode_file = FilePath("test.md")
        context_files = [FilePath("guide.md"), FilePath("plot.yaml")]
        metadata = {"key": "value"}

        # When: リクエスト作成
        request = ClaudeCodeEvaluationRequest(
            item=sample_checklist_item,
            episode_file_path=episode_file,
            context_files=context_files,
            metadata=metadata,
        )

        # Then: 適切にリクエストが作成される
        assert request.item == sample_checklist_item
        assert request.episode_file_path == episode_file
        assert request.context_files == context_files
        assert request.metadata == metadata

    @pytest.mark.spec("SPEC-A31-002")
    def test_request_with_optional_metadata(self, sample_checklist_item: A31ChecklistItem) -> None:
        """メタデータ省略時のリクエスト作成テスト"""
        # When: メタデータなしでリクエスト作成
        request = ClaudeCodeEvaluationRequest(
            item=sample_checklist_item,
            episode_file_path=FilePath("test.md"),
            context_files=[],
        )

        # Then: メタデータがNoneになる
        assert request.metadata is None
