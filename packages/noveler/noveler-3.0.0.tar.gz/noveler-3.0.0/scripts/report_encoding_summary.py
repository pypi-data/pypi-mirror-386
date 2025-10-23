#!/usr/bin/env python3
# File: scripts/report_encoding_summary.py
# Purpose: Generate a simple Markdown summary from encoding scan reports.
# Inputs:
#   - reports/encoding-scan.filtered.txt (recommended)
#   - reports/encoding-scan.txt (optional)
# Output:
#   - reports/encoding-scan.summary.md

from __future__ import annotations

from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
import re

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
FILT = REPORTS / "encoding-scan.filtered.txt"
RAW = REPORTS / "encoding-scan.txt"
OUT = REPORTS / "encoding-scan.summary.md"

LINE_RE = re.compile(r"U\+FFFD:\s*(.*?):(\d+):(\d+):\s*(.*)")


def categorize(path: str) -> str:
    p = path.replace("\\", "/")
    if "/docs/archive/" in p:
        return "archive"
    if "/docs/backup/" in p:
        return "backup"
    if "/docs/guides/" in p:
        return "guides"
    if "/docs/proposals/" in p:
        return "proposals"
    if "/docs/mcp/" in p:
        return "mcp"
    if "/docs/architecture/" in p:
        return "architecture"
    if "/docs/troubleshooting/" in p:
        return "troubleshooting"
    if "/src/" in p:
        return "src"
    if "/docs/" in p:
        return "docs-other"
    return "other"


def parse_report(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.exists():
        return findings
    for line in path.read_text(encoding="utf-8").splitlines():
        if LINE_RE.match(line):
            findings.append(line)
    return findings


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    filtered = parse_report(FILT)
    raw = parse_report(RAW)

    # Per-file counts
    file_counts: Counter[str] = Counter()
    cat_counts: Counter[str] = Counter()
    for line in filtered:
        m = LINE_RE.match(line)
        assert m
        path = m.group(1)
        file_counts[path] += 1
        cat_counts[categorize(path)] += 1

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    top = file_counts.most_common(20)

    lines: list[str] = []
    lines.append(f"# Encoding Scan Summary ({now})")
    lines.append("")
    lines.append(f"- Filtered findings: {len(filtered)}")
    if raw:
        lines.append(f"- Unfiltered findings: {len(raw)}")
    lines.append("")
    lines.append("## By Category (filtered)")
    for cat, cnt in cat_counts.most_common():
        lines.append(f"- {cat}: {cnt}")

    lines.append("")
    lines.append("## Top 20 Files (filtered)")
    for cnt, (path, n) in enumerate(top, start=1):
        lines.append(f"{cnt:2d}. {n:5d}  {path}")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

