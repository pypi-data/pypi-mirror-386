#!/usr/bin/env python3
"""Update Claude Code slash command for noveler (MCP-first)

Writes an up-to-date ~/.claude/commands/noveler.md with correct allowed-tools and
MCP-first examples. Optionally writes to a custom path using --out.

Usage:
  python bin/update_claude_commands.py               # write to ~/.claude/commands/noveler.md
  python bin/update_claude_commands.py --out ./noveler.md --model claude-sonnet-4-20250514
"""
from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_TOOLS = [
    # Quality orchestration
    "mcp__noveler__run_quality_checks",
    "mcp__noveler__fix_quality_issues",
    "mcp__noveler__export_quality_report",
    "mcp__noveler__improve_quality_until",
    "mcp__noveler__get_issue_context",
    # Aspect-specific
    "mcp__noveler__check_rhythm",
    "mcp__noveler__check_readability",
    "mcp__noveler__check_grammar",
    "mcp__noveler__check_style",
    # Quality metadata utilities
    "mcp__noveler__list_quality_presets",
    "mcp__noveler__get_quality_schema",
    # Design/aux tools (optional but useful)
    "mcp__noveler__test_result_analysis",
    "mcp__noveler__backup_management",
    "mcp__noveler__design_conversations",
    "mcp__noveler__track_emotions",
    "mcp__noveler__design_scenes",
    "mcp__noveler__design_senses",
    "mcp__noveler__manage_props",
    "mcp__noveler__export_design_data",
    # Step tools (if present in server)
    "mcp__noveler__write_step_1",
    "mcp__noveler__write_step_2",
    "mcp__noveler__write_step_3",
    "mcp__noveler__write_step_4",
    "mcp__noveler__write_step_5",
    "mcp__noveler__write_step_6",
    "mcp__noveler__write_step_7",
    "mcp__noveler__write_step_8",
    "mcp__noveler__write_step_9",
    "mcp__noveler__write_step_10",
]


TEMPLATE_BODY = """
小説執筆支援（MCP優先）コマンドを実行します：

## よく使うコマンド

### 🔗 MCPサーバー起動
```bash
noveler mcp-server --dev --port 3001 --debug
```

### 🔍 品質チェック（軽量要約）
```bash
noveler mcp call run_quality_checks '{
  "episode_number": EPISODE,
  "additional_params": { "format": "summary", "severity_threshold": "medium" }
}'
```

オプション:
- weights: {"rhythm":0.35,"readability":0.35,"grammar":0.2,"style":0.1}
- strict運用: NOVELER_STRICT_PATHS=1

### 🛠️ 安全な自動修正
```bash
noveler mcp call fix_quality_issues '{
  "episode_number": EPISODE,
  "additional_params": { "dry_run": false }
}'
```

### 🔁 目標スコアまで反復改善
```bash
noveler mcp call improve_quality_until '{
  "episode_number": EPISODE,
  "additional_params": { "target_score": 80, "include_diff": false }
}'
```

補足（reason_codesの指定形式）:
- fix_quality_issues は `reason_codes: string[]`（配列）。
- improve_quality_until は `{ aspect: string[] }`（オブジェクト）推奨ですが、後方互換で配列も受理します。
  - 配列で渡した場合は、指定アスペクト全てに同一セットを適用します。
  - 例（オブジェクト）:
    ```bash
    noveler mcp call improve_quality_until '{
      "episode_number": EPISODE,
      "additional_params": {
        "aspects": ["rhythm"],
        "target_score": 85,
        "reason_codes": {"rhythm": ["LINE_WIDTH_OVERFLOW","CONSECUTIVE_LONG_SENTENCES","ELLIPSIS_STYLE"]}
      }
    }'
    ```
  - 例（配列・後方互換）:
    ```bash
    noveler mcp call improve_quality_until '{
      "episode_number": EPISODE,
      "additional_params": {
        "aspects": ["rhythm"],
        "target_score": 85,
        "reason_codes": ["LINE_WIDTH","DASH","CONSECUTIVE_LONG_SENTENCES"]
      }
    }'
    ```
    上記は実行時に `LINE_WIDTH`→`LINE_WIDTH_OVERFLOW`、`DASH`→`DASH_STYLE` へ正規化され、非対応コードは `metadata.ignored_reason_codes` に記録されます。

### 📝 レポート出力（Markdown）
```bash
noveler mcp call export_quality_report '{
  "episode_number": EPISODE,
  "additional_params": {
    "format": "md",
    "destination": "50_管理資料/quality_epEPISODE.md",
    "template": "compact",
    "include_details": false
  }
}'
```

### 🧭 互換（必要時のみ）
PATHに bin を追加後:
```bash
noveler check EPISODE --auto-fix
```
内部で MCP ツールへリダイレクトして実行します。
""".strip()


def build_front_matter(tools: list[str], model: str) -> str:
    # YAML-like header used by Claude Code commands
    items = ("[\n  \"" + "\",\n  \"".join(tools) + "\"\n]") if tools else "[]"
    header = (
        "---\n"
        f"allowed-tools: {items}\n"
        "argument-hint: \"<command> [options]\"\n"
        "description: \"小説執筆支援（MCP優先・品質/修正/レポート）\"\n"
        f"model: \"{model}\"\n"
        "---\n\n"
    )
    return header


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=None, help="Write to a specific file (default: ~/.claude/commands/noveler.md)")
    ap.add_argument("--model", type=str, default="claude-sonnet-4-20250514", help="Claude model id to set in header")
    args = ap.parse_args()

    out_path = args.out
    if out_path is None:
        home = Path.home()
        out_path = home / ".claude" / "commands" / "noveler.md"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    content = build_front_matter(DEFAULT_TOOLS, args.model) + TEMPLATE_BODY + "\n"
    out_path.write_text(content, encoding="utf-8")
    print(f"✅ Updated: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
