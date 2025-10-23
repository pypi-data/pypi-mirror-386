#!/usr/bin/env python3
"""Claude Code実行関連バリューオブジェクト

仕様書: SPEC-CLAUDE-CODE-001
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ClaudeCodeExecutionRequest:
    """Claude Code実行リクエスト

    REQ-2.1: Claude Code実行に必要な情報を保持するバリューオブジェクト
    """

    prompt_content: str
    output_format: str = "json"
    max_turns: int = 3
    project_context_paths: list[Path] | None = None

    def __post_init__(self) -> None:
        """初期化後処理"""
        if self.project_context_paths is None:
            self.project_context_paths = []

        # バリデーション
        if not self.prompt_content.strip():
            msg = "prompt_content must not be empty"
            raise ValueError(msg)

        if self.max_turns <= 0:
            msg = "max_turns must be positive"
            raise ValueError(msg)

        if self.output_format not in ["json", "text", "stream-json"]:
            msg = f"Unsupported output_format: {self.output_format}"
            raise ValueError(msg)


@dataclass
class ClaudeCodeExecutionResponse:
    """Claude Code実行レスポンス

    REQ-2.2: Claude Code実行結果を保持するレスポンスエンティティ
    """

    success: bool
    response_content: str = ""
    json_data: dict | None = None
    execution_time_ms: float = 0.0
    error_message: str | None = None

    def is_success(self) -> bool:
        """実行成功判定"""
        return self.success and not self.error_message

    def has_json_data(self) -> bool:
        """JSON データ含有判定"""
        return self.json_data is not None and bool(self.json_data)

    def get_manuscript_content(self) -> str | None:
        """原稿内容取得

        JSONデータから原稿内容を抽出する
        """
        if not self.has_json_data():
            return self.response_content if self.response_content else None

        # エラー状態チェック（最優先）
        if self.is_claude_code_error():
            return None

        # 一般的なキー名での原稿内容検索
        manuscript_keys = ["manuscript", "content", "response", "text", "output"]
        for key in manuscript_keys:
            if key in self.json_data:
                return self.json_data[key]

        return None

    def is_claude_code_error(self) -> bool:
        """Claude Codeエラー状態判定

        JSON応答からエラー状態を検出する

        Returns:
            bool: エラー状態の場合True
        """
        if not self.has_json_data():
            return False

        # エラーサブタイプの検出
        error_subtypes = [
            "error_max_turns",
            "error_timeout",
            "error_invalid_request",
            "error_api_failure",
            "error_parse_failure",
        ]

        subtype = self.json_data.get("subtype", "")
        if subtype in error_subtypes:
            return True

        # typeがerrorの場合
        if self.json_data.get("type") == "error":
            return True

        # is_errorフラグがTrueの場合
        return self.json_data.get("is_error") is True

    def get_error_details(self) -> dict:
        """エラー詳細情報取得

        Returns:
            dict: エラー詳細情報
        """
        if not self.is_claude_code_error():
            return {}

        return {
            "type": self.json_data.get("type"),
            "subtype": self.json_data.get("subtype"),
            "duration_ms": self.json_data.get("duration_ms"),
            "num_turns": self.json_data.get("num_turns"),
            "total_cost_usd": self.json_data.get("total_cost_usd"),
            "error_message": self._extract_error_message(),
        }

    def _extract_error_message(self) -> str:
        """エラーメッセージ抽出"""
        if not self.has_json_data():
            return "不明なエラー"

        subtype = self.json_data.get("subtype", "")

        if subtype == "error_max_turns":
            turns = self.json_data.get("num_turns", "不明")
            return f"最大ターン数制限に到達しました（{turns}ターン）"
        if subtype == "error_timeout":
            return "実行タイムアウトが発生しました"
        if subtype == "error_invalid_request":
            return "無効なリクエストです"
        if subtype == "error_api_failure":
            return "API呼び出しに失敗しました"
        if subtype == "error_parse_failure":
            return "レスポンス解析に失敗しました"
        return f"Claude Codeエラー: {subtype}"

    def get_metadata(self) -> dict:
        """メタデータ取得"""
        if not self.has_json_data():
            return {}

        return self.json_data.get("metadata", {})
