#!/usr/bin/env python3
"""
プロジェクト統計レポート自動生成

概要:
- リポジトリの基本統計（ファイル数、言語別行数、docs分量）を集計
- テスト・スクリプト・設定などの分布を可視化
- Markdownレポートを reports/stats_report.md に出力

実行:
  python scripts/generate_stats_report.py
"""
from __future__ import annotations

import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"
OUTPUT = REPORTS_DIR / "stats_report.md"


def count_lines(path: Path) -> int:
    try:
        # バイナリや巨大ファイルはスキップ
        if path.stat().st_size > 5_000_000:
            return 0
        with open(path, "rb") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def main() -> None:
    exts_of_interest = {
        ".py": "python",
        ".md": "markdown",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
    }

    by_ext_count: Counter[str] = Counter()
    by_ext_lines: Counter[str] = Counter()
    by_dir_files: defaultdict[str, int] = defaultdict(int)

    for dirpath, dirnames, filenames in os.walk(ROOT):
        # .git, dist, build などは除外
        parts = Path(dirpath).parts
        if any(p in {".git", "dist", "build", "__pycache__", ".ruff_cache", ".benchmarks"} for p in parts):
            continue

        for name in filenames:
            p = Path(dirpath) / name
            ext = p.suffix.lower()
            if ext not in exts_of_interest:
                continue

            lang = exts_of_interest[ext]
            by_ext_count[lang] += 1
            by_dir_files[str(Path(dirpath).relative_to(ROOT))] += 1
            by_ext_lines[lang] += count_lines(p)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append(f"# プロジェクト統計レポート\n")
    lines.append(f"最終更新: {now}\n")
    lines.append("\n---\n")

    total_files = sum(by_ext_count.values())
    total_lines = sum(by_ext_lines.values())
    lines.append(f"## 概要\n")
    lines.append(f"- 対象ファイル数: {total_files}\n")
    lines.append(f"- 総行数(概算): {total_lines}\n")

    lines.append("\n## 言語別内訳\n")
    for lang in sorted(by_ext_count):
        lines.append(f"- {lang}: {by_ext_count[lang]} files / {by_ext_lines[lang]} lines")

    lines.append("\n## 主要ディレクトリ別ファイル数\n")
    for d, c in sorted(by_dir_files.items(), key=lambda x: (-x[1], x[0]))[:15]:
        lines.append(f"- {d}: {c}")

    lines.append("\n---\n")
    lines.append("このレポートは scripts/generate_stats_report.py により自動生成されました。\n")

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[ok] wrote {OUTPUT}")


if __name__ == "__main__":
    main()
