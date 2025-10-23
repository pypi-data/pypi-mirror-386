#!/usr/bin/env python3
"""IntegratedWritingRequest のシリアライズテスト

SPEC-MCP-001: MCP境界での型安全なシリアライズ保証
統合執筆リクエストが MCP 境界で安全にシリアライズできることを確認
"""

import json
from pathlib import Path

import pytest

from noveler.application.use_cases.integrated_writing_use_case import IntegratedWritingRequest


class TestIntegratedWritingRequestSerialization:
    """IntegratedWritingRequest のシリアライズテスト"""

    def test_to_dict_converts_project_root_to_str(self):
        """to_dict() が project_root の Path を str に変換することを確認"""
        test_path = Path("/test/project")
        req = IntegratedWritingRequest(
            episode_number=1,
            project_root=test_path,
        )

        result = req.to_dict()

        assert isinstance(result["project_root"], str)
        # Platform-independent comparison: both should normalize to string representation
        assert result["project_root"] == str(test_path)
        assert result["episode_number"] == 1

    def test_to_dict_preserves_all_fields(self):
        """to_dict() が全てのフィールドを保持することを確認"""
        test_path = Path("/test/project")
        req = IntegratedWritingRequest(
            episode_number=2,
            project_root=test_path,
            word_count_target="5000",
            genre="fantasy",
            viewpoint="三人称単元視点",
            viewpoint_character="主人公",
            custom_requirements=["要件1", "要件2"],
            direct_claude_execution=True,
        )

        result = req.to_dict()

        assert result["episode_number"] == 2
        assert result["project_root"] == str(test_path)
        assert result["word_count_target"] == "5000"
        assert result["genre"] == "fantasy"
        assert result["viewpoint"] == "三人称単元視点"
        assert result["viewpoint_character"] == "主人公"
        assert result["custom_requirements"] == ["要件1", "要件2"]
        assert result["direct_claude_execution"] is True

    def test_to_dict_result_is_json_serializable(self):
        """to_dict() の結果が JSON シリアライズ可能であることを確認"""
        test_path = Path("/test/project")
        req = IntegratedWritingRequest(
            episode_number=3,
            project_root=test_path,
            custom_requirements=["要件A"],
        )

        result = req.to_dict()

        # JSON シリアライズが成功することを確認（例外が発生しないこと）
        json_str = json.dumps(result, ensure_ascii=False)
        assert isinstance(json_str, str)

        # デシリアライズも成功することを確認
        deserialized = json.loads(json_str)
        assert deserialized["episode_number"] == 3
        assert deserialized["project_root"] == str(test_path)

    def test_to_dict_handles_windows_path(self):
        """to_dict() が Windows パスを適切に処理することを確認"""
        req = IntegratedWritingRequest(
            episode_number=4,
            project_root=Path(r"C:\Users\test\project"),
        )

        result = req.to_dict()

        # Windows パスも文字列に変換される
        assert isinstance(result["project_root"], str)
        # Path の str() は OS 依存だが、文字列であることは保証される
        assert len(result["project_root"]) > 0

    def test_to_dict_with_relative_path(self):
        """to_dict() が相対パスを適切に処理することを確認"""
        req = IntegratedWritingRequest(
            episode_number=5,
            project_root=Path("./test/project"),
        )

        result = req.to_dict()

        assert isinstance(result["project_root"], str)
        # 相対パスも文字列に変換される
        assert "test" in result["project_root"] and "project" in result["project_root"]


class TestIntegratedWritingRequestMCPIntegration:
    """IntegratedWritingRequest の MCP 統合テスト"""

    def test_mcp_error_response_serialization(self):
        """MCP エラーレスポンス時の arguments シリアライズを確認

        これは元の問題 (PosixPath JSON serialization error) を再現・検証するテスト
        """
        req = IntegratedWritingRequest(
            episode_number=1,
            project_root=Path("/test/project"),
        )

        # MCP エラーレスポンス形式をシミュレート
        error_result = {
            "error": "Test error",
            "tool": "noveler",
            "arguments": req.to_dict(),  # to_dict() を使用
        }

        # JSON シリアライズが成功することを確認
        json_str = json.dumps(error_result, ensure_ascii=False)
        assert isinstance(json_str, str)

        # Path が str に変換されていることを確認
        deserialized = json.loads(json_str)
        assert isinstance(deserialized["arguments"]["project_root"], str)

    def test_direct_request_object_fails_json_serialization(self):
        """リクエストオブジェクトを直接 JSON 化すると失敗することを確認

        これは元の問題を示すネガティブテスト。
        to_dict() を使わないと Path が JSON 化できないことを確認。
        """
        req = IntegratedWritingRequest(
            episode_number=1,
            project_root=Path("/test/project"),
        )

        # dataclass を直接 JSON 化しようとすると失敗する
        with pytest.raises(TypeError, match="not JSON serializable"):
            json.dumps({"request": req})

    def test_to_dict_enables_safe_mcp_serialization(self):
        """to_dict() を使用すれば MCP で安全にシリアライズできることを確認"""
        test_path = Path("/test/project")
        req = IntegratedWritingRequest(
            episode_number=1,
            project_root=test_path,
        )

        # to_dict() を使用すれば JSON 化できる
        safe_data = {"request": req.to_dict()}
        json_str = json.dumps(safe_data)

        # デシリアライズして検証
        deserialized = json.loads(json_str)
        assert deserialized["request"]["project_root"] == str(test_path)
