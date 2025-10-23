"""fix_style_extended ツールの実装

TODO.md対応: style拡張（任意/opt-in）機能
- FULLWIDTH_SPACE の正規化（opt-in: 半角化/除去）。台詞/地の文で挙動切替
- BRACKETS_MISMATCH の自動補正（簡易ヒューリスティクス、dry_run表示のみでも可）
"""
from __future__ import annotations

import difflib
import hashlib
import re
import time
from pathlib import Path
from typing import Any

from mcp_servers.noveler.domain.entities.mcp_tool_base import (
    MCPToolBase,
    ToolRequest,
    ToolResponse,
)
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.infrastructure.caching.file_cache_service import get_file_cache_service
from noveler.infrastructure.adapters.path_service_adapter import create_path_service


class FixStyleExtendedTool(MCPToolBase):
    """style拡張機能（任意/opt-in）の自動修正ツール"""

    def __init__(self) -> None:
        super().__init__(
            tool_name="fix_style_extended",
            tool_description="style拡張機能（opt-in）: FULLWIDTH_SPACE正規化とBRACKETS_MISMATCH自動補正",
        )

    def get_input_schema(self) -> dict[str, Any]:
        schema = self._get_common_input_schema()
        schema["properties"].update({
            "file_path": {
                "type": "string",
                "description": "直接ファイルパス指定（episode_numberより優先）",
            },
            "fullwidth_space_mode": {
                "type": "string",
                "enum": ["normalize", "remove", "dialogue_only", "narrative_only", "disabled"],
                "default": "disabled",
                "description": "全角スペース処理モード（opt-in）",
            },
            "brackets_fix_mode": {
                "type": "string",
                "enum": ["auto", "conservative", "disabled"],
                "default": "disabled",
                "description": "括弧の自動補正モード（opt-in）",
            },
            "dry_run": {
                "type": "boolean",
                "default": True,
                "description": "差分表示のみ（実際の書き込みは行わない）",
            },
        })
        return schema

    def execute(self, request: ToolRequest) -> ToolResponse:
        logger = get_logger(__name__)
        start = time.time()
        try:
            self._validate_request(request)
            ap = request.additional_params or {}

            # パラメータ取得
            fullwidth_mode = ap.get("fullwidth_space_mode", "disabled")
            brackets_mode = ap.get("brackets_fix_mode", "disabled")
            dry_run = ap.get("dry_run", True)

            # ファイル取得
            file_path: Path | None = None
            if isinstance(ap.get("content"), str):
                content = ap.get("content") or ""
                if isinstance(ap.get("file_path"), str):
                    fp = Path(ap["file_path"]).expanduser()
                    file_path = fp if fp.exists() else fp
            else:
                if isinstance(ap.get("file_path"), str):
                    file_path = Path(ap["file_path"]).expanduser()
                    content = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
                else:
                    content = self._load_episode_content(request.episode_number, request.project_name)
                    try:
                        ps = create_path_service()
                        cache = get_file_cache_service()
                        md = ps.get_manuscript_dir()
                        file_path = cache.get_episode_file_cached(md, request.episode_number)
                        self._ps_collect_fallback(ps)
                    except Exception:
                        file_path = None

            if not content:
                return self._create_response(
                    True, 100.0, [], start,
                    "対象ファイルが空のため、処理をスキップしました"
                )

            original_content = content
            modified_content = content
            changes_made = []

            # 1. FULLWIDTH_SPACE正規化処理
            if fullwidth_mode != "disabled":
                modified_content, fs_changes = self._process_fullwidth_spaces(
                    modified_content, fullwidth_mode
                )
                changes_made.extend(fs_changes)

            # 2. BRACKETS_MISMATCH自動補正処理
            if brackets_mode != "disabled":
                modified_content, bracket_changes = self._process_bracket_mismatches(
                    modified_content, brackets_mode
                )
                changes_made.extend(bracket_changes)

            # 結果の生成
            if modified_content != original_content:
                # 差分生成
                diff_lines = list(difflib.unified_diff(
                    original_content.splitlines(keepends=True),
                    modified_content.splitlines(keepends=True),
                    fromfile="original",
                    tofile="modified",
                    lineterm=""
                ))
                diff_text = "".join(diff_lines)

                # dry_run無効の場合のみファイル書き込み
                if not dry_run and file_path and file_path.exists():
                    file_path.write_text(modified_content, encoding="utf-8")
                    logger.info(f"ファイルを更新しました: {file_path}")

                resp = self._create_response(
                    True, 100.0, [], start,
                    f"style拡張処理が完了しました。{len(changes_made)}件の変更を実行しました。"
                )
                resp.metadata.update({
                    "changes_made": len(changes_made),
                    "changes_detail": changes_made,
                    "diff": diff_text,
                    "dry_run": dry_run,
                    "fullwidth_mode": fullwidth_mode,
                    "brackets_mode": brackets_mode,
                })

                if file_path:
                    resp.metadata["file_path"] = str(file_path)
                    if not dry_run:
                        resp.metadata["file_updated"] = True

            else:
                resp = self._create_response(
                    True, 100.0, [], start,
                    "修正が必要な箇所が見つかりませんでした。"
                )
                resp.metadata.update({
                    "changes_made": 0,
                    "dry_run": dry_run,
                    "fullwidth_mode": fullwidth_mode,
                    "brackets_mode": brackets_mode,
                })

            self._apply_fallback_metadata(resp)
            return resp

        except Exception as e:
            logger.exception("style拡張処理でエラーが発生しました")
            return self._create_response(False, 0.0, [], start, f"style拡張処理エラー: {e!s}")

    def _process_fullwidth_spaces(self, content: str, mode: str) -> tuple[str, list[str]]:
        """全角スペースの正規化処理"""
        changes = []
        lines = content.split("\n")
        modified_lines = []

        for line_num, line in enumerate(lines, 1):
            original_line = line

            if "　" not in line:
                modified_lines.append(line)
                continue

            if mode == "normalize":
                # 全角スペースを半角スペースに変換
                line = line.replace("　", " ")

            elif mode == "remove":
                # 全角スペースを除去
                line = line.replace("　", "")

            elif mode == "dialogue_only":
                # 台詞内の全角スペースのみ処理（「」『』内）
                line = self._process_dialogue_spaces(line, "normalize")

            elif mode == "narrative_only":
                # 地の文の全角スペースのみ処理（台詞外）
                line = self._process_narrative_spaces(line, "normalize")

            if line != original_line:
                changes.append(f"行{line_num}: 全角スペース処理 ({mode})")

            modified_lines.append(line)

        return "\n".join(modified_lines), changes

    def _process_dialogue_spaces(self, line: str, action: str) -> str:
        """台詞内の全角スペースを処理"""
        # 「」内と『』内の全角スペースを処理
        def replace_in_quotes(match):
            quote_content = match.group(0)
            if action == "normalize":
                return quote_content.replace("　", " ")
            elif action == "remove":
                return quote_content.replace("　", "")
            return quote_content

        # 「」の処理
        line = re.sub(r'「[^」]*」', replace_in_quotes, line)
        # 『』の処理
        line = re.sub(r'『[^』]*』', replace_in_quotes, line)

        return line

    def _process_narrative_spaces(self, line: str, action: str) -> str:
        """地の文（台詞外）の全角スペースを処理"""
        # 台詞部分を一時的に保護
        dialogue_parts = []

        # 「」部分を保護
        def protect_quotes(match):
            dialogue_parts.append(match.group(0))
            return f"__DIALOGUE_{len(dialogue_parts)-1}__"

        line = re.sub(r'「[^」]*」', protect_quotes, line)
        line = re.sub(r'『[^』]*』', protect_quotes, line)

        # 保護されていない部分（地の文）の全角スペースを処理
        if action == "normalize":
            line = line.replace("　", " ")
        elif action == "remove":
            line = line.replace("　", "")

        # 保護した台詞部分を復元
        for i, dialogue in enumerate(dialogue_parts):
            line = line.replace(f"__DIALOGUE_{i}__", dialogue)

        return line

    def _process_bracket_mismatches(self, content: str, mode: str) -> tuple[str, list[str]]:
        """括弧の対応不一致の自動補正処理"""
        changes = []

        # 日本語括弧のペア定義
        bracket_pairs = [
            ("「", "」"),
            ("『", "』"),
            ("（", "）"),
            ("【", "】"),
            ("〈", "〉"),
            ("《", "》"),
            ("〔", "〕"),
        ]

        for left, right in bracket_pairs:
            left_count = content.count(left)
            right_count = content.count(right)

            if left_count == right_count:
                continue  # 対応が取れている

            if mode == "conservative" and abs(left_count - right_count) > 3:
                # 保守的モードでは大きな不一致は修正しない
                continue

            if left_count > right_count:
                # 右括弧が不足している場合
                deficit = left_count - right_count
                content = self._add_closing_brackets(content, left, right, deficit)
                changes.append(f"括弧補正: {right} を {deficit} 個追加")

            elif right_count > left_count:
                # 左括弧が不足している場合
                deficit = right_count - left_count
                content = self._add_opening_brackets(content, left, right, deficit)
                changes.append(f"括弧補正: {left} を {deficit} 個追加")

        return content, changes

    def _add_closing_brackets(self, content: str, left: str, right: str, count: int) -> str:
        """閉じ括弧を追加"""
        lines = content.split("\n")
        added = 0

        for i in range(len(lines) - 1, -1, -1):  # 後ろから処理
            if added >= count:
                break

            line = lines[i].strip()
            if line and left in line and not line.endswith(right):
                # この行に開き括弧があり、閉じ括弧で終わっていない
                lines[i] = lines[i].rstrip() + right
                added += 1

        return "\n".join(lines)

    def _add_opening_brackets(self, content: str, left: str, right: str, count: int) -> str:
        """開き括弧を追加"""
        lines = content.split("\n")
        added = 0

        for i in range(len(lines)):  # 前から処理
            if added >= count:
                break

            line = lines[i].strip()
            if line and right in line and not line.startswith(left):
                # この行に閉じ括弧があり、開き括弧で始まっていない
                lines[i] = left + lines[i].lstrip()
                added += 1

        return "\n".join(lines)
