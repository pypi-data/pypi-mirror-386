#!/usr/bin/env python3
"""原稿処理サービス

原稿内容の抽出、保存、エラー処理を担当するドメインサービス
EnhancedIntegratedWritingUseCaseから分離されたコンポーネント
"""

from pathlib import Path
from typing import TYPE_CHECKING

from noveler.domain.interfaces.path_service import IPathService

if TYPE_CHECKING:
    from noveler.domain.interfaces.console_service_protocol import IConsoleService
    from noveler.domain.interfaces.logger import ILogger
    from noveler.domain.interfaces.path_service_protocol import IPathService

from noveler.domain.value_objects.claude_code_execution import ClaudeCodeExecutionResponse


class ManuscriptProcessingService:
    """原稿処理ドメインサービス

    責務:
    - Claude Code応答からの原稿内容抽出
    - エラー時の代替原稿生成
    - 原稿ファイルの保存処理
    """

    def __init__(self, path_service: "IPathService", console_service: "IConsoleService", logger: "ILogger") -> None:
        """初期化

        Args:
            path_service: パスサービス
            console_service: コンソールサービス
            logger: ロガー（インターフェース）
        """
        self.path_service = path_service
        self.console_service = console_service
        self.logger = logger

    def extract_manuscript_content(self, claude_response: ClaudeCodeExecutionResponse) -> str:
        """Claude Code応答から原稿内容抽出

        Args:
            claude_response: Claude Code実行結果

        Returns:
            str: 抽出された原稿内容
        """
        # Claude Codeエラー状態チェック
        if claude_response.is_claude_code_error():
            error_details = claude_response.get_error_details()
            error_msg = error_details.get("error_message", "未知のエラー")

            self.logger.error("❌ Claude Code実行エラー: %s", error_msg)
            self.console_service.print_error("エラーが発生しました")

            # 詳細情報を表示
            if error_details.get("total_cost_usd"):
                self.logger.info(f"💰 実行コスト: ${error_details['total_cost_usd']:.4f}")
                self.console_service.print_warning("警告メッセージ")
            if error_details.get("duration_ms"):
                self.logger.info(f"⏱️ 実行時間: {error_details['duration_ms']:.0f}ms")
                self.console_service.print_warning("警告メッセージ")

            # エラー専用の原稿内容を生成
            return self._generate_error_manuscript(error_details)

        manuscript_content = claude_response.get_manuscript_content()

        if manuscript_content:
            return manuscript_content

        # JSONデータが取得できない場合の警告（ただしエラー応答ではない場合のみ）
        self.logger.warning(
            "原稿内容をJSONから抽出できませんでした - Claude Codeの応答形式が想定と異なる可能性があります"
        )
        self.console_service.print_warning("処理中...")
        self.console_service.print_warning("処理中...")

        # エラーではないが原稿が抽出できない場合の対処
        return self._generate_fallback_manuscript(claude_response)

    def _generate_error_manuscript(self, error_details: dict) -> str:
        """エラー時の原稿内容生成

        Args:
            error_details: エラー詳細情報

        Returns:
            str: エラー情報を含む原稿内容
        """
        error_msg = error_details.get("error_message", "未知のエラー")
        subtype = error_details.get("subtype", "unknown")
        cost = error_details.get("total_cost_usd", 0.0)
        duration = error_details.get("duration_ms", 0.0)
        turns = error_details.get("num_turns", 0)

        return f"""# Claude Code実行エラー

## エラー詳細
- **エラータイプ**: {subtype}
- **エラーメッセージ**: {error_msg}
- **実行ターン数**: {turns}ターン
- **実行時間**: {duration:.0f}ms
- **実行コスト**: ${cost:.4f}

## 対処方法

### {subtype}の場合の推奨対処法:
{self._get_error_solution_guide(subtype)}

## 再実行について
このエラーが発生した場合は、以下を確認してから再実行してください：
1. プロンプト内容の複雑さ
2. ターン数制限の調整（現在: 3ターン）
3. タイムアウト設定の確認

---
*この内容は執筆システムによって自動生成されたエラー情報です*
"""

    def _get_error_solution_guide(self, subtype: str) -> str:
        """エラータイプ別解決ガイド"""
        guides = {
            "error_max_turns": """
- プロンプトをより具体的で簡潔にする
- ターン数制限を増やす（--max-turns パラメータ）
- 段階的に分割して実行する""",
            "error_timeout": """
- より短い原稿を指定する
- タイムアウト時間を延長する
- ネットワーク接続を確認する""",
            "error_invalid_request": """
- プロンプト形式を確認する
- 必要なパラメータが不足していないか確認する
- Claude Codeのバージョンを確認する""",
        }

        return guides.get(subtype, "- Claude Codeのドキュメントを確認してください\n- システム管理者に連絡してください")

    def _generate_fallback_manuscript(self, claude_response: ClaudeCodeExecutionResponse) -> str:
        """フォールバック原稿内容生成"""
        return f"""# 原稿抽出エラー

Claude Codeからの応答を正常に受信しましたが、期待される形式で原稿内容を抽出できませんでした。

## 受信した応答の概要
- **成功フラグ**: {claude_response.success}
- **JSONデータ有無**: {claude_response.has_json_data()}
- **応答文字数**: {len(claude_response.response_content)}文字

## 生応答内容（先頭500文字）
```
{claude_response.response_content[:500]}...
```

## 対処方法
1. Claude Codeの出力形式設定を確認
2. プロンプト内容を調整
3. システム管理者に連絡

---
*この内容は執筆システムによって自動生成されたフォールバック情報です*
"""

    async def save_manuscript(self, manuscript_content: str, episode_number: int) -> Path:
        """原稿内容保存処理

        Args:
            manuscript_content: 原稿内容
            episode_number: エピソード番号

        Returns:
            Path: 保存された原稿ファイルパス
        """
        # パスサービス使用（統一命名に準拠）
        manuscript_path = self.path_service.get_manuscript_path(episode_number)

        manuscript_path.write_text(manuscript_content, encoding="utf-8")

        self.logger.info("📝 原稿保存完了: %s", manuscript_path)
        self.console_service.print_success(f"原稿保存完了: {manuscript_path}")
        return manuscript_path
