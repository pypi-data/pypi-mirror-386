"""Tools.langsmith_bugfix_helper
Where: Tool assisting with LangSmith bugfix workflows.
What: Wraps LangSmith artifact generation and patch application scripts.
Why: Simplifies bugfix workflows relying on LangSmith artifacts.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from noveler.application.services.langsmith_bugfix_workflow_service import (
    LangSmithBugfixWorkflowService,
)
from noveler.presentation.shared.shared_utilities import (
    CommonPathService,
    console,
    get_logger,
)

LOGGER = get_logger(__name__)


def _build_service(project_root: str | None) -> LangSmithBugfixWorkflowService:
    path_service = CommonPathService(Path(project_root)) if project_root else None
    return LangSmithBugfixWorkflowService(path_service=path_service)


def _handle_summarize(args: argparse.Namespace) -> int:
    service = _build_service(args.project_root)
    try:
        artifacts = service.prepare_artifacts(
            run_json=args.run_json,
            output_dir=Path(args.output_dir) if args.output_dir else None,
            dataset_name=args.dataset_name,
            expected_behavior=args.expected_behavior,
        )
    except Exception as exc:  # pragma: no cover - 予期せぬ障害
        console.print_error(f"❌ サマリー生成中にエラーが発生しました: {exc}")
        LOGGER.exception("Failed to prepare LangSmith artifacts")
        return 1

    console.print_success(f"📄 Summary: {artifacts.summary_path}")
    console.print_success(f"🪄 Prompt: {artifacts.prompt_path}")
    if artifacts.dataset_entry_path:
        console.print_success(f"🗂️ Dataset: {artifacts.dataset_entry_path}")
    return 0


def _handle_apply(args: argparse.Namespace) -> int:
    service = _build_service(args.project_root)
    try:
        if args.patch_file:
            patch_text = Path(args.patch_file).read_text(encoding="utf-8")
        else:
            patch_text = sys.stdin.read()
        if not patch_text.strip():
            console.print_error("❌ パッチ内容が空です")
            return 1
        result = service.apply_patch(
            patch_text,
            project_root=Path(args.project_root) if args.project_root else None,
            strip=args.strip,
        )
    except Exception as exc:  # pragma: no cover - 予期せぬ障害
        console.print_error(f"❌ パッチ適用中にエラーが発生しました: {exc}")
        LOGGER.exception("Failed to apply patch")
        return 1

    if not result.applied:
        console.print_error(result.stderr or "パッチ適用に失敗しました")
        return 1
    return 0


def _handle_verify(args: argparse.Namespace) -> int:
    command = list(args.verify_command or [])
    if command and command[0] == '--':
        command = command[1:]
    if not command:
        console.print_error("❌ 実行するコマンドを指定してください")
        return 1
    service = _build_service(args.project_root)
    try:
        result = service.run_verification(
            command=command,
            project_root=Path(args.project_root) if args.project_root else None,
        )
    except Exception as exc:  # pragma: no cover - 予期せぬ障害
        console.print_error(f"❌ 検証実行時にエラーが発生しました: {exc}")
        LOGGER.exception("Verification command failed to execute")
        return 1

    if result.returncode != 0:
        console.print_error(result.stderr or "検証コマンドが失敗しました")
        return result.returncode or 1
    return 0


_COMMAND_HANDLERS = {
    "summarize": _handle_summarize,
    "apply": _handle_apply,
    "verify": _handle_verify,
}


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LangSmithの失敗ランから修正・検証までを連携する支援ツール",
    )
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    summarize_parser = subparsers.add_parser(
        "summarize", help="LangSmithのrun.jsonから要約・プロンプト・データセットを生成する"
    )
    summarize_parser.add_argument("--run-json", required=True, help="LangSmithからエクスポートしたrun.json")
    summarize_parser.add_argument("--output-dir", help="成果物を出力するディレクトリ")
    summarize_parser.add_argument("--dataset-name", help="更新するデータセット名")
    summarize_parser.add_argument("--expected-behavior", help="期待する挙動の説明")
    summarize_parser.add_argument("--project-root", help="対象プロジェクトルート")

    apply_parser = subparsers.add_parser("apply", help="提案されたパッチを適用する")
    apply_parser.add_argument("--patch-file", help="適用するdiffファイルのパス。省略時はstdinを使用")
    apply_parser.add_argument("--strip", type=int, default=1, help="patchコマンドに渡す-p値 (default: 1)")
    apply_parser.add_argument("--project-root", help="対象プロジェクトルート")

    verify_parser = subparsers.add_parser("verify", help="修正後の検証コマンドを実行する")
    verify_parser.add_argument("--project-root", help="対象プロジェクトルート")
    verify_parser.add_argument("verify_command", nargs=argparse.REMAINDER, help="実行する検証コマンド")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _create_parser()
    args = parser.parse_args(argv)
    handler = _COMMAND_HANDLERS.get(args.command_name)
    if handler is None:  # pragma: no cover - argparseが保証
        console.print_error("未知のコマンドです")
        return 1
    return handler(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
