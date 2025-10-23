# File: src/noveler/domain/services/mcp_command_suggester.py
# Purpose: Provide command suggestion and validation for MCP slash commands
# Context: Improves accuracy of slash command recognition and execution

import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class CommandSuggestion:
    """MCPコマンド提案の詳細"""
    tool_name: str
    command: str
    confidence: float
    description: str
    parameters: Dict


class MCPCommandSuggester:
    """MCPコマンドの補完・サジェスト機能を提供"""

    def __init__(self):
        """コマンドパターンとツールマッピングを初期化"""
        self.command_patterns = {
            r"(?:check|チェック|確認).*(?:episode|第|話|エピソード).*?(\d+)": {
                "tool": "run_quality_checks",
                "description": "品質チェック（軽量要約）",
                "default_params": {"format": "summary", "severity_threshold": "medium"}
            },
            r"(?:fix|修正|直す).*(?:episode|第|話|エピソード).*?(\d+)": {
                "tool": "fix_quality_issues",
                "description": "安全な自動修正",
                "default_params": {"dry_run": False}
            },
            r"(?:improve|改善|向上).*(?:episode|第|話|エピソード).*?(\d+)": {
                "tool": "improve_quality_until",
                "description": "目標スコアまで反復改善",
                "default_params": {"target_score": 80, "include_diff": False}
            },
            r"(?:export|エクスポート|出力).*(?:report|レポート).*(?:episode|第|話|エピソード).*?(\d+)": {
                "tool": "export_quality_report",
                "description": "レポート出力（Markdown）",
                "default_params": {"format": "md", "template": "compact", "include_details": False}
            }
        }

        # よく使われるエイリアス
        self.tool_aliases = {
            "quality_check": "run_quality_checks",
            "check": "run_quality_checks",
            "fix": "fix_quality_issues",
            "improve": "improve_quality_until",
            "export": "export_quality_report",
            "report": "export_quality_report"
        }

    def suggest_command(self, user_input: str) -> List[CommandSuggestion]:
        """
        ユーザー入力から適切なMCPコマンドを提案

        Args:
            user_input: ユーザーの入力文字列

        Returns:
            信頼度順にソートされたコマンド提案リスト
        """
        suggestions = []

        for pattern, config in self.command_patterns.items():
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                episode_num = self._extract_episode_number(user_input, match)

                if episode_num:
                    command = self._build_command(
                        config["tool"],
                        episode_num,
                        config["default_params"]
                    )

                    suggestions.append(CommandSuggestion(
                        tool_name=config["tool"],
                        command=command,
                        confidence=self._calculate_confidence(user_input, pattern),
                        description=config["description"],
                        parameters={
                            "episode_number": episode_num,
                            "additional_params": config["default_params"]
                        }
                    ))

        return sorted(suggestions, key=lambda x: x.confidence, reverse=True)

    def validate_command(self, command: str, params: Dict) -> Tuple[bool, List[str], List[str]]:
        """
        MCPコマンドとパラメータの妥当性を検証

        Args:
            command: MCPツール名
            params: コマンドパラメータ

        Returns:
            (有効性, エラーリスト, 警告リスト)
        """
        errors = []
        warnings = []

        # ツール名の正規化と検証
        normalized_tool = self._normalize_tool_name(command)
        if not normalized_tool:
            errors.append(f"不明なMCPツール: {command}")
            similar = self._find_similar_tools(command)
            if similar:
                warnings.append(f"もしかして: {', '.join(similar)}")

        # エピソード番号の検証
        if "episode_number" in params:
            ep_num = params["episode_number"]
            if not isinstance(ep_num, int):
                errors.append("episode_numberは整数である必要があります")
            elif ep_num < 1 or ep_num > 999:
                errors.append("episode_numberは1〜999の範囲内である必要があります")
        elif normalized_tool and self._requires_episode_number(normalized_tool):
            errors.append("このコマンドにはepisode_numberが必要です")

        # 追加パラメータの検証
        if "additional_params" in params:
            add_params = params["additional_params"]
            if not isinstance(add_params, dict):
                errors.append("additional_paramsは辞書形式である必要があります")
            else:
                self._validate_additional_params(normalized_tool, add_params, errors, warnings)

        return (len(errors) == 0, errors, warnings)

    def generate_usage_hint(self, failed_command: str, error: str = None) -> str:
        """
        失敗したコマンドに対する具体的な使用例を生成

        Args:
            failed_command: 失敗したコマンド文字列
            error: エラーメッセージ（オプション）

        Returns:
            使用例を含むヘルプメッセージ
        """
        hints = []

        # エラーメッセージから推測
        if error:
            if "episode_number" in error.lower():
                hints.append("エピソード番号の指定例:")
                hints.append('noveler mcp call run_quality_checks \'{"episode_number": 1}\'')
            elif "json" in error.lower():
                hints.append("JSONフォーマットの例:")
                hints.append('\'{"episode_number": 1, "additional_params": {...}}\'')

        # コマンドから推測
        suggestions = self.suggest_command(failed_command)
        if suggestions:
            hints.append("推奨コマンド:")
            for suggestion in suggestions[:3]:
                hints.append(f"  {suggestion.command}")
                hints.append(f"  → {suggestion.description}")
        else:
            hints.append("利用可能なコマンド例:")
            hints.append(self._get_generic_examples())

        return "\n".join(hints)

    def _extract_episode_number(self, text: str, match: Optional[re.Match]) -> Optional[int]:
        """テキストからエピソード番号を抽出"""
        # マッチグループから直接取得を試みる
        if match and match.groups():
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                pass

        # 全体のテキストから数字を探す
        numbers = re.findall(r'\d+', text)
        if numbers:
            # 最初に見つかった妥当な範囲の数字を返す
            for num_str in numbers:
                num = int(num_str)
                if 1 <= num <= 999:
                    return num

        return None

    def _build_command(self, tool: str, episode_num: int, additional_params: Dict) -> str:
        """MCPコマンド文字列を構築"""
        params = {
            "episode_number": episode_num
        }

        if additional_params:
            params["additional_params"] = additional_params

        params_json = json.dumps(params, ensure_ascii=False, separators=(',', ':'))
        return f"noveler mcp call {tool} '{params_json}'"

    def _calculate_confidence(self, user_input: str, pattern: str) -> float:
        """コマンド提案の信頼度を計算"""
        confidence = 0.5

        # パターンマッチの強さ
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            matched_text = match.group(0)
            coverage = len(matched_text) / len(user_input)
            confidence += coverage * 0.3

        # キーワードの存在
        keywords = ["episode", "エピソード", "第", "話", "check", "fix", "improve", "export"]
        keyword_count = sum(1 for kw in keywords if kw.lower() in user_input.lower())
        confidence += min(keyword_count * 0.1, 0.2)

        return min(confidence, 1.0)

    def _normalize_tool_name(self, tool: str) -> Optional[str]:
        """ツール名を正規化"""
        tool_lower = tool.lower()

        # エイリアスチェック
        if tool_lower in self.tool_aliases:
            return self.tool_aliases[tool_lower]

        # 完全一致
        known_tools = [
            "run_quality_checks", "fix_quality_issues",
            "improve_quality_until", "export_quality_report"
        ]

        if tool in known_tools:
            return tool

        # 部分一致
        for known in known_tools:
            if tool_lower in known.lower() or known.lower() in tool_lower:
                return known

        return None

    def _find_similar_tools(self, tool: str) -> List[str]:
        """類似したツール名を検索"""
        known_tools = [
            "run_quality_checks", "fix_quality_issues",
            "improve_quality_until", "export_quality_report"
        ]

        similar = []
        tool_lower = tool.lower()

        for known in known_tools:
            # レーベンシュタイン距離の簡易版
            if any(part in known.lower() for part in tool_lower.split('_')):
                similar.append(known)
            elif any(part in tool_lower for part in known.lower().split('_')):
                similar.append(known)

        return similar[:3]

    def _requires_episode_number(self, tool: str) -> bool:
        """ツールがエピソード番号を必要とするか判定"""
        episode_required_tools = [
            "run_quality_checks", "fix_quality_issues",
            "improve_quality_until", "export_quality_report"
        ]
        return tool in episode_required_tools

    def _validate_additional_params(self, tool: str, params: Dict,
                                   errors: List[str], warnings: List[str]) -> None:
        """追加パラメータの検証"""
        if tool == "run_quality_checks":
            if "format" in params and params["format"] not in ["summary", "ndjson", "json"]:
                warnings.append("formatは'summary', 'ndjson', 'json'のいずれかを推奨")
            if "severity_threshold" in params and params["severity_threshold"] not in ["low", "medium", "high"]:
                warnings.append("severity_thresholdは'low', 'medium', 'high'のいずれかを推奨")

        elif tool == "fix_quality_issues":
            if "dry_run" in params and not isinstance(params["dry_run"], bool):
                errors.append("dry_runはbool値である必要があります")

        elif tool == "improve_quality_until":
            if "target_score" in params:
                score = params["target_score"]
                if not isinstance(score, (int, float)):
                    errors.append("target_scoreは数値である必要があります")
                elif score < 0 or score > 100:
                    warnings.append("target_scoreは0〜100の範囲を推奨")

        elif tool == "export_quality_report":
            if "format" in params and params["format"] not in ["md", "html", "json"]:
                warnings.append("formatは'md', 'html', 'json'のいずれかを推奨")

    def _get_generic_examples(self) -> str:
        """汎用的な使用例を取得"""
        return """
# 品質チェック
noveler mcp call run_quality_checks '{"episode_number": 1}'

# 自動修正
noveler mcp call fix_quality_issues '{"episode_number": 1, "additional_params": {"dry_run": false}}'

# 品質改善
noveler mcp call improve_quality_until '{"episode_number": 1, "additional_params": {"target_score": 80}}'

# レポート出力
noveler mcp call export_quality_report '{"episode_number": 1, "additional_params": {"format": "md"}}'
"""
