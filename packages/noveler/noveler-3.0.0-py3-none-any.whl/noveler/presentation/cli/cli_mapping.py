"""Shared CLI ↔ MCP tool mapping used for help text and documentation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class CommandMapping:
    cli_command: str
    mcp_tool: str
    description: str


MAPPINGS: tuple[CommandMapping, ...] = (
    CommandMapping(
        cli_command="noveler write tasks --episode-number <n>",
        mcp_tool="enhanced_get_writing_tasks",
        description="18ステップ拡張版のタスクリスト取得",
    ),
    CommandMapping(
        cli_command="noveler write step --episode-number <n> --step-id <id>",
        mcp_tool="enhanced_execute_writing_step",
        description="指定ステップの実行（dry_run対応）",
    ),
    CommandMapping(
        cli_command="noveler write resume --episode-number <n> --recovery-point <id>",
        mcp_tool="enhanced_resume_from_partial_failure",
        description="部分失敗復旧",
    ),
    CommandMapping(
        cli_command="noveler check run --episode-number <n> [--format summary]",
        mcp_tool="run_quality_checks",
        description="品質チェック実行",
    ),
    CommandMapping(
        cli_command="noveler check improve --episode-number <n> [--aspects ...]",
        mcp_tool="improve_quality_until",
        description="ターゲットスコアまで品質改善",
    ),
    CommandMapping(
        cli_command="noveler polish stage --episode-number <n> --stages stage2,stage3",
        mcp_tool="polish_manuscript",
        description="推敲ステージ実行（dry_run対応）",
    ),
    CommandMapping(
        cli_command="noveler polish apply --episode-number <n> --stages stage2,stage3",
        mcp_tool="polish_manuscript_apply",
        description="推敲適用・レポート生成",
    ),
    CommandMapping(
        cli_command="noveler artifacts list --episode-number <n>",
        mcp_tool="list_artifacts",
        description="アーティファクト一覧取得",
    ),
    CommandMapping(
        cli_command="noveler artifacts get --episode-number <n> --artifact-id <id>",
        mcp_tool="fetch_artifact",
        description="アーティファクト取得",
    ),
    CommandMapping(
        cli_command="noveler mcp call <tool> '{JSON}'",
        mcp_tool="<direct tool call>",
        description="任意のMCPツールを直接呼び出すラッパー",
    ),
)


def iter_mappings() -> Iterable[CommandMapping]:
    return MAPPINGS

