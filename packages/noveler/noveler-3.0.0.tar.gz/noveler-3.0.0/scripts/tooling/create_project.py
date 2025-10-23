# File: scripts/tooling/create_project.py
# Purpose: Cross-platform project creation utility invoked from shell wrappers.
# Context: Replaces bash-specific create-project script with a Python implementation usable on Windows and WSL.

"""Create a new novel project structure with sensible defaults."""

from __future__ import annotations

import argparse
import datetime as _dt
import os
from pathlib import Path
from textwrap import dedent

ROOT_DIR = Path(__file__).resolve().parents[2]
GUIDE_ROOT = ROOT_DIR
DEFAULT_NOVEL_ROOT = Path(os.environ.get("NOVEL_ROOT", GUIDE_ROOT.parent))


def _print(message: str) -> None:
    print(message)


def _confirm(prompt: str) -> bool:
    try:
        response = input(prompt).strip().lower()
    except EOFError:
        return False
    return response in {"y", "yes"}


def _create_project(args: argparse.Namespace) -> None:
    project_root = args.novel_root / args.project_name
    project_root.mkdir(parents=True, exist_ok=True)

    # Step 1: directory structure
    (project_root / "10_企画").mkdir(parents=True, exist_ok=True)
    (project_root / "20_プロット" / "章別プロット").mkdir(parents=True, exist_ok=True)
    (project_root / "30_設定集").mkdir(parents=True, exist_ok=True)
    (project_root / "40_原稿").mkdir(parents=True, exist_ok=True)
    (project_root / "50_管理資料" / "執筆記録").mkdir(parents=True, exist_ok=True)
    (project_root / "90_アーカイブ").mkdir(parents=True, exist_ok=True)

    # Step 2: project configuration
    template = GUIDE_ROOT / "templates" / "プロジェクト設定テンプレート.yaml"
    config_path = project_root / "プロジェクト設定.yaml"
    today = _dt.date.today().isoformat()
    title = args.project_name.split("_", 1)[-1]

    if template.exists():
        content = template.read_text(encoding="utf-8")
        content = content.replace("/path/to/your/小説プロジェクト", str(project_root))
        content = content.replace("作品タイトル", title)
        content = content.replace("2024-01-01", today)
        config_path.write_text(content, encoding="utf-8")
    else:
        fallback = dedent(
            f"""
            paths:
              project_root: "{project_root}"

            project:
              name: "{title}"
              genre: "ファンタジー"
              status: "planning"
              created_date: "{today}"

            author:
              pen_name: "ペンネーム"
            """
        ).strip() + "\n"
        config_path.write_text(fallback, encoding="utf-8")

    # Step 3: README.md
    readme = project_root / "README.md"
    readme_contents = dedent(
        f"""
        # {title}

        作成日: {today}

        ## 概要

        [作品の概要をここに記載]

        ## 進捗状況

        - [ ] 企画・設計
        - [ ] プロット作成
        - [ ] 設定集作成
        - [ ] 執筆開始
        - [ ] 第1話完成

        ## ディレクトリ構成

        ```
        {args.project_name}/
        ├── 10_企画/
        ├── 20_プロット/
        ├── 30_設定集/
        ├── 40_原稿/
        ├── 50_管理資料/
        └── 90_アーカイブ/
        ```
        """
    ).strip() + "\n"
    readme.write_text(readme_contents, encoding="utf-8")

    gitignore = project_root / ".gitignore"
    gitignore.write_text(
        "# Temporary files\n*.tmp\n*.bak\n*~\n\n"
        "# Logs\n*.log\n\n"
        "# Personal settings\n.env\npersonal_notes.md\n\n"
        "# Generated files\ndropout_analysis_report.md\nアクセス分析_*\\.yaml\n",
        encoding="utf-8",
    )

    _print("\n=== プロジェクト作成完了 ===")
    _print(f"作成場所: {project_root}")
    _print("\n次のステップ:")
    _print("1. プロジェクト設定.yamlを編集")
    _print(f"   $ cd '{project_root}'")
    _print("   $ editors プロジェクト設定.yaml")
    _print("\n2. 環境変数を設定 (PATH 追加後に新しいシェルで)")
    _print(f"   $ export PROJECT_ROOT='{project_root}'")
    _print(f"   $ export GUIDE_ROOT='{GUIDE_ROOT}'")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a new novel project")
    parser.add_argument("project_name", help="Project directory name (e.g. 08_時空の図書館)")
    parser.add_argument(
        "--novel-root",
        dest="novel_root",
        default=DEFAULT_NOVEL_ROOT,
        type=Path,
        help="Root directory under which projects are created",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Proceed without confirmation when the project directory already exists",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    project_root = args.novel_root / args.project_name
    if project_root.exists() and not args.yes:
        if not _confirm(f"警告: {project_root} は既に存在します。続行しますか？ (y/N): "):
            raise SystemExit(1)

    _create_project(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
