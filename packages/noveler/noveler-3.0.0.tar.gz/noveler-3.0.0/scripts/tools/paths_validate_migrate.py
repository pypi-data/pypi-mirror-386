#!/usr/bin/env python3
"""パス命名バリデーション/移行ツール

目的:
- 原稿/プロットの旧仕様命名・配置を検出
- 可能な範囲で安全に新仕様へリネーム/移動（デフォルトはドライラン）

使い方:
  検出のみ:
    python scripts/tools/paths_validate_migrate.py validate --project-root /path/to/project

  自動移行（ドライラン）:
    python scripts/tools/paths_validate_migrate.py migrate --project-root /path/to/project --dry-run

  実行移行（原稿+プロット）:
    python scripts/tools/paths_validate_migrate.py migrate --project-root /path/to/project \
      --fix-manuscripts --fix-plots

出力:
- コンソール要約
- --json-out で詳細JSONを書き出し
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _parse_episode_from_manuscript(name: str) -> tuple[int | None, str | None]:
    m = re.match(r"^第(\d{3})話(?:_(.*))?\.md$", name)
    if not m:
        return None, None
    num = int(m.group(1))
    title = m.group(2) or None
    return num, title


def validate(project_root: Path, fix_manuscripts: bool = False, fix_plots: bool = False, dry_run: bool = True) -> dict:
    from noveler.infrastructure.adapters.path_service_adapter import create_path_service

    ps = create_path_service(project_root)

    issues: dict[str, list[dict]] = {"manuscripts": [], "plots": []}
    actions: list[dict] = []

    # 原稿検出
    mdir = ps.get_manuscript_dir()
    if mdir.exists():
        for p in sorted(mdir.glob("*.md")):
            ep, title = _parse_episode_from_manuscript(p.name)
            if ep is None:
                continue
            expected = ps.get_manuscript_path(ep)
            if title is None:
                issues["manuscripts"].append({
                    "kind": "missing_title",
                    "file": str(p),
                    "episode": ep,
                    "expected": str(expected),
                })
                if fix_manuscripts:
                    new_title = ps.get_episode_title(ep) or "無題"
                    target = expected.parent / f"第{ep:03d}話_{new_title}.md"
                    actions.append({
                        "op": "rename",
                        "from": str(p),
                        "to": str(target),
                        "reason": "add_title",
                    })
            elif p != expected:
                # 名前や場所が異なる
                issues["manuscripts"].append({
                    "kind": "mismatch",
                    "file": str(p),
                    "episode": ep,
                    "expected": str(expected),
                })
                if fix_manuscripts:
                    actions.append({
                        "op": "rename",
                        "from": str(p),
                        "to": str(expected),
                        "reason": "unify_name",
                    })

    # プロット検出（20_プロット直下の旧配置）
    pdir = ps.get_plots_dir()
    epdir = ps.get_episode_plots_dir()
    patterns = [
        "第*.yaml",
        "第*.yml",
        "第*.md",
    ]
    misplaced = []
    if pdir.exists():
        for pat in patterns:
            for f in pdir.glob(pat):
                # 話別プロット直下にあるべきファイルを検出（既に話別プロットにあるものは除外）
                if f.parent == epdir:
                    continue
                # 簡易に第NNN話* を抽出
                if re.match(r"^第\d{3}話.*\.(yaml|yml|md)$", f.name):
                    misplaced.append(f)
    for f in misplaced:
        issues["plots"].append({
            "kind": "misplaced_plot",
            "file": str(f),
            "expected_dir": str(epdir),
        })
        if fix_plots:
            target = epdir / f.name
            actions.append({
                "op": "move",
                "from": str(f),
                "to": str(target),
                "reason": "move_to_episode_plots",
            })

    # 実行（ドライランでない場合）
    executed: list[dict] = []
    if not dry_run:
        for act in actions:
            src = Path(act["from"]) if Path(act["from"]).is_absolute() else project_root / act["from"]
            dst = Path(act["to"]) if Path(act["to"]).is_absolute() else project_root / act["to"]
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                if act["op"] == "rename" or act["op"] == "move":
                    if dst.exists() and src.resolve() == dst.resolve():
                        # 既に期待名で存在
                        executed.append({**act, "status": "skip_exists"})
                        continue
                    if dst.exists():
                        executed.append({**act, "status": "conflict"})
                        continue
                    src.rename(dst)
                    executed.append({**act, "status": "done"})
                else:
                    executed.append({**act, "status": "unknown_op"})
            except Exception as e:
                executed.append({**act, "status": "error", "error": str(e)})

    return {
        "project_root": str(project_root),
        "issues": issues,
        "planned_actions": actions,
        "executed": executed,
        "dry_run": dry_run,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="原稿/プロットのパス命名検証と移行ツール")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_common(a: argparse.ArgumentParser) -> None:
        a.add_argument("--project-root", type=Path, default=Path.cwd(), help="プロジェクトルート")
        a.add_argument("--json-out", type=Path, default=None, help="結果JSONの出力先")
        a.add_argument("--verbose", action="store_true", help="詳細出力")

    ap_val = sub.add_parser("validate", help="検出のみ実行")
    add_common(ap_val)

    ap_mig = sub.add_parser("migrate", help="可能な範囲で自動移行")
    add_common(ap_mig)
    ap_mig.add_argument("--dry-run", action="store_true", help="ドライラン（実ファイル変更なし）", default=False)
    ap_mig.add_argument("--fix-manuscripts", action="store_true", help="原稿の命名を統一")
    ap_mig.add_argument("--fix-plots", action="store_true", help="話別プロットの配置を統一")

    args = ap.parse_args()

    if args.cmd == "validate":
        result = validate(args.project_root, fix_manuscripts=False, fix_plots=False, dry_run=True)
    else:
        result = validate(
            args.project_root,
            fix_manuscripts=args.fix_manuscripts,
            fix_plots=args.fix_plots,
            dry_run=bool(args.dry_run),
        )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # コンソール要約
    man_issues = len(result["issues"]["manuscripts"]) \
        if isinstance(result.get("issues", {}), dict) else 0
    plot_issues = len(result["issues"]["plots"]) \
        if isinstance(result.get("issues", {}), dict) else 0
    print(f"検出: 原稿 {man_issues} 件, プロット {plot_issues} 件")
    if result.get("planned_actions"):
        print(f"計画アクション: {len(result['planned_actions'])} 件, ドライラン={result['dry_run']}")
    if result.get("executed"):
        done = [a for a in result["executed"] if a.get("status") == "done"]
        print(f"実行: {len(done)} 件 / {len(result['executed'])} 件")


if __name__ == "__main__":  # pragma: no cover
    main()

