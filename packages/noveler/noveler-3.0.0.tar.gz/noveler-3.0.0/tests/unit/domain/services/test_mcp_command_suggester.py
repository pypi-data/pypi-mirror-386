# File: tests/unit/domain/services/test_mcp_command_suggester.py
# Purpose: Test MCP command suggester for slash command accuracy improvements
# Context: Validates command recognition, suggestion, and validation capabilities

import pytest
from noveler.domain.services.mcp_command_suggester import MCPCommandSuggester, CommandSuggestion


class TestMCPCommandSuggester:
    """MCPコマンドサジェスター機能のテストスイート"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.suggester = MCPCommandSuggester()

    def test_suggest_command_from_japanese_input(self):
        """日本語入力からの適切なコマンド提案"""
        # checkと話数を含む入力
        suggestions = self.suggester.suggest_command("check episode 1")
        assert len(suggestions) > 0
        assert suggestions[0].tool_name == "run_quality_checks"
        assert suggestions[0].parameters["episode_number"] == 1

        # fixと話数を含む入力
        suggestions = self.suggester.suggest_command("fix episode 5")
        assert len(suggestions) > 0
        assert suggestions[0].tool_name == "fix_quality_issues"
        assert suggestions[0].parameters["episode_number"] == 5

    def test_suggest_command_from_english_input(self):
        """英語入力からの適切なコマンド提案"""
        suggestions = self.suggester.suggest_command("check episode 3")
        assert len(suggestions) > 0
        assert suggestions[0].tool_name == "run_quality_checks"
        assert suggestions[0].parameters["episode_number"] == 3

        suggestions = self.suggester.suggest_command("improve episode 10 quality")
        assert len(suggestions) > 0
        assert suggestions[0].tool_name == "improve_quality_until"
        assert suggestions[0].parameters["episode_number"] == 10

    def test_suggest_command_with_mixed_input(self):
        """混合言語入力からの適切なコマンド提案"""
        suggestions = self.suggester.suggest_command("export レポート for episode 7")
        assert len(suggestions) > 0
        assert suggestions[0].tool_name == "export_quality_report"
        assert suggestions[0].parameters["episode_number"] == 7

    def test_validate_command_success(self):
        """正常なコマンドパラメータの検証"""
        # 品質チェックコマンド
        is_valid, errors, warnings = self.suggester.validate_command(
            "run_quality_checks",
            {"episode_number": 1, "additional_params": {"format": "summary"}}
        )
        assert is_valid is True
        assert len(errors) == 0

        # 修正コマンド
        is_valid, errors, warnings = self.suggester.validate_command(
            "fix_quality_issues",
            {"episode_number": 5, "additional_params": {"dry_run": True}}
        )
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_command_with_invalid_episode_number(self):
        """無効なエピソード番号での検証失敗"""
        # 範囲外のエピソード番号
        is_valid, errors, warnings = self.suggester.validate_command(
            "run_quality_checks",
            {"episode_number": 1000}
        )
        assert is_valid is False
        assert "episode_numberは1〜999の範囲内である必要があります" in errors

        # 負のエピソード番号
        is_valid, errors, warnings = self.suggester.validate_command(
            "run_quality_checks",
            {"episode_number": -1}
        )
        assert is_valid is False
        assert "episode_numberは1〜999の範囲内である必要があります" in errors

    def test_validate_command_with_missing_episode_number(self):
        """必須のエピソード番号が欠けている場合の検証失敗"""
        is_valid, errors, warnings = self.suggester.validate_command(
            "run_quality_checks",
            {}
        )
        assert is_valid is False
        assert "このコマンドにはepisode_numberが必要です" in errors

    def test_validate_command_with_invalid_additional_params(self):
        """無効な追加パラメータでの警告"""
        # 不正なformat値
        is_valid, errors, warnings = self.suggester.validate_command(
            "run_quality_checks",
            {
                "episode_number": 1,
                "additional_params": {"format": "invalid_format"}
            }
        )
        assert is_valid is True  # 警告のみなので有効
        assert "formatは'summary', 'ndjson', 'json'のいずれかを推奨" in warnings

        # 不正なdry_run型
        is_valid, errors, warnings = self.suggester.validate_command(
            "fix_quality_issues",
            {
                "episode_number": 1,
                "additional_params": {"dry_run": "yes"}
            }
        )
        assert is_valid is False
        assert "dry_runはbool値である必要があります" in errors

    def test_generate_usage_hint_for_failed_command(self):
        """失敗したコマンドに対する使用ヒントの生成"""
        # エピソード番号エラー
        hint = self.suggester.generate_usage_hint(
            "check episode",
            "episode_number is required"
        )
        assert "エピソード番号の指定例" in hint
        assert "episode_number" in hint

        # JSON形式エラー
        hint = self.suggester.generate_usage_hint(
            "run quality check",
            "Invalid JSON format"
        )
        assert "JSON" in hint
        assert "{" in hint and "}" in hint

    def test_generate_usage_hint_with_suggestions(self):
        """コマンド候補を含む使用ヒントの生成"""
        hint = self.suggester.generate_usage_hint("第3話の品質をチェック")
        assert "推奨コマンド" in hint or "利用可能なコマンド" in hint
        assert "run_quality_checks" in hint

    def test_normalize_tool_name(self):
        """ツール名の正規化"""
        # エイリアスからの正規化
        assert self.suggester._normalize_tool_name("check") == "run_quality_checks"
        assert self.suggester._normalize_tool_name("fix") == "fix_quality_issues"
        assert self.suggester._normalize_tool_name("improve") == "improve_quality_until"

        # 完全一致
        assert self.suggester._normalize_tool_name("run_quality_checks") == "run_quality_checks"

        # 部分一致
        assert self.suggester._normalize_tool_name("quality") == "run_quality_checks"

        # マッチしない
        assert self.suggester._normalize_tool_name("unknown_command") is None

    def test_find_similar_tools(self):
        """類似ツール名の検索"""
        similar = self.suggester._find_similar_tools("quality")
        assert "run_quality_checks" in similar

        similar = self.suggester._find_similar_tools("fix")
        assert "fix_quality_issues" in similar

        similar = self.suggester._find_similar_tools("report")
        assert "export_quality_report" in similar

    def test_extract_episode_number(self):
        """テキストからのエピソード番号抽出"""
        import re

        # パターンマッチでの抽出
        pattern = r"episode.*?(\d+)"
        match = re.search(pattern, "check episode 5", re.IGNORECASE)
        assert self.suggester._extract_episode_number("check episode 5", match) == 5

        # 日本語パターン
        pattern = r"第(\d+)話"
        match = re.search(pattern, "第10話をチェック")
        assert self.suggester._extract_episode_number("第10話をチェック", match) == 10

        # フォールバックでの抽出（マッチなし）
        match = None
        assert self.suggester._extract_episode_number("episode number is 42", match) == 42

    def test_build_command(self):
        """MCPコマンド文字列の構築"""
        command = self.suggester._build_command(
            "run_quality_checks",
            1,
            {"format": "summary"}
        )
        assert "noveler mcp call run_quality_checks" in command
        assert '"episode_number":1' in command
        assert '"format":"summary"' in command

    def test_calculate_confidence(self):
        """コマンド提案の信頼度計算"""
        # 高い信頼度（完全一致）
        confidence = self.suggester._calculate_confidence(
            "check episode 1",
            r"check.*episode.*(\d+)"
        )
        assert confidence > 0.5

        # 信頼度の範囲確認（0から1の間）
        confidence = self.suggester._calculate_confidence(
            "some text with check in it",
            r"check"
        )
        assert 0 <= confidence <= 1.0

    def test_command_suggestion_dataclass(self):
        """CommandSuggestionデータクラスの動作確認"""
        suggestion = CommandSuggestion(
            tool_name="run_quality_checks",
            command="noveler mcp call run_quality_checks '{\"episode_number\": 1}'",
            confidence=0.8,
            description="品質チェック",
            parameters={"episode_number": 1}
        )
        assert suggestion.tool_name == "run_quality_checks"
        assert suggestion.confidence == 0.8
        assert suggestion.parameters["episode_number"] == 1

    def test_multiple_suggestions_sorting(self):
        """複数の提案が信頼度順にソートされること"""
        suggestions = self.suggester.suggest_command("episode 5 quality fix improve")
        if len(suggestions) > 1:
            # 信頼度の降順でソートされていることを確認
            for i in range(len(suggestions) - 1):
                assert suggestions[i].confidence >= suggestions[i + 1].confidence

    def test_edge_cases(self):
        """エッジケースの処理"""
        # 空文字列
        suggestions = self.suggester.suggest_command("")
        assert len(suggestions) == 0

        # 数字のみ
        suggestions = self.suggester.suggest_command("123")
        assert len(suggestions) == 0

        # コマンドキーワードなし
        suggestions = self.suggester.suggest_command("これは普通のテキストです")
        assert len(suggestions) == 0
