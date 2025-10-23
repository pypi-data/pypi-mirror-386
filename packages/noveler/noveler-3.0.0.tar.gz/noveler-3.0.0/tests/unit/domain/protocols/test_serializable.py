#!/usr/bin/env python3
"""SerializableRequest/Response プロトコルのユニットテスト

SPEC-MCP-001: MCP境界での型安全なシリアライズ保証のテスト
"""

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from noveler.domain.protocols.serializable import SerializableRequest, SerializableResponse


@dataclass
class MockSerializableRequest(SerializableRequest):
    """テスト用のSerializableRequest実装"""

    episode_number: int
    project_root: Path
    optional_path: Path | None = None

    def to_dict(self) -> dict:
        """Path を str に変換してシリアライズ"""
        return {
            "episode_number": self.episode_number,
            "project_root": str(self.project_root),
            "optional_path": str(self.optional_path) if self.optional_path else None,
        }


@dataclass
class MockSerializableResponse(SerializableResponse):
    """テスト用のSerializableResponse実装"""

    success: bool
    output_path: Path | None = None

    def to_dict(self) -> dict:
        """Path を str に変換してシリアライズ"""
        return {
            "success": self.success,
            "output_path": str(self.output_path) if self.output_path else None,
        }


class TestSerializableRequest:
    """SerializableRequest プロトコルのテスト"""

    def test_to_dict_converts_path_to_str(self):
        """to_dict() が Path を str に変換することを確認"""
        req = MockSerializableRequest(
            episode_number=1,
            project_root=Path("/test/project"),
        )

        result = req.to_dict()

        assert isinstance(result["project_root"], str)
        # Windows/Unixで異なるパス区切りを許容
        assert result["project_root"] == str(Path("/test/project"))
        assert result["episode_number"] == 1

    def test_to_dict_handles_optional_path(self):
        """to_dict() がオプショナルな Path を適切に処理することを確認"""
        req = MockSerializableRequest(
            episode_number=2,
            project_root=Path("/test/project"),
            optional_path=Path("/test/optional"),
        )

        result = req.to_dict()

        assert isinstance(result["optional_path"], str)
        assert result["optional_path"] == str(Path("/test/optional"))

    def test_to_dict_handles_none_path(self):
        """to_dict() が None の Path を適切に処理することを確認"""
        req = MockSerializableRequest(
            episode_number=3,
            project_root=Path("/test/project"),
            optional_path=None,
        )

        result = req.to_dict()

        assert result["optional_path"] is None

    def test_to_dict_result_is_json_serializable(self):
        """to_dict() の結果が JSON シリアライズ可能であることを確認"""
        req = MockSerializableRequest(
            episode_number=4,
            project_root=Path("/test/project"),
            optional_path=Path("/test/optional"),
        )

        result = req.to_dict()

        # JSON シリアライズが成功することを確認（例外が発生しないこと）
        json_str = json.dumps(result)
        assert isinstance(json_str, str)

        # デシリアライズも成功することを確認
        deserialized = json.loads(json_str)
        assert deserialized["episode_number"] == 4
        assert deserialized["project_root"] == str(Path("/test/project"))


class TestSerializableResponse:
    """SerializableResponse プロトコルのテスト"""

    def test_response_to_dict_converts_path_to_str(self):
        """Response の to_dict() が Path を str に変換することを確認"""
        resp = MockSerializableResponse(
            success=True,
            output_path=Path("/output/file.txt"),
        )

        result = resp.to_dict()

        assert isinstance(result["output_path"], str)
        assert result["output_path"] == str(Path("/output/file.txt"))
        assert result["success"] is True

    def test_response_to_dict_result_is_json_serializable(self):
        """Response の to_dict() の結果が JSON シリアライズ可能であることを確認"""
        resp = MockSerializableResponse(
            success=False,
            output_path=None,
        )

        result = resp.to_dict()

        # JSON シリアライズが成功することを確認
        json_str = json.dumps(result)
        assert isinstance(json_str, str)

        deserialized = json.loads(json_str)
        assert deserialized["success"] is False
        assert deserialized["output_path"] is None


class TestSerializableIntegration:
    """SerializableRequest/Response の統合テスト"""

    def test_request_response_round_trip(self):
        """リクエスト→レスポンスの往復がJSONシリアライズ可能であることを確認"""
        # リクエスト作成
        req = MockSerializableRequest(
            episode_number=5,
            project_root=Path("/project"),
        )

        # リクエストをJSON化
        req_json = json.dumps(req.to_dict())
        req_data = json.loads(req_json)

        # レスポンス作成（リクエストデータを利用）
        resp = MockSerializableResponse(
            success=True,
            output_path=Path(req_data["project_root"]) / "output.txt",
        )

        # レスポンスをJSON化
        resp_json = json.dumps(resp.to_dict())
        resp_data = json.loads(resp_json)

        # 検証
        assert resp_data["success"] is True
        expected_path = str(Path(req_data["project_root"]) / "output.txt")
        assert resp_data["output_path"] == expected_path
