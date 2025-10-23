#!/usr/bin/env python3
"""
Audit v1→v2 template migration for information loss.

Compares each backup template under templates_backup_*/write_stepXX_*.yaml
with the current templates/writing/write_stepXX_*.yaml and checks for the
presence of key concept keywords (A38-derived) that should be preserved.

Outputs a Markdown report to reports/template_migration_audit.md
with per-step coverage and missing concept lists.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Dict

ROOT = Path(__file__).resolve().parents[1]


CONCEPTS: Dict[str, List[str]] = {
    # Global A38 core concepts
    "core": [
        r"8000", r"視点", r"禁止", r"直説説明|直説", r"感情直書き", r"会話", r"目的駆動|目的", r"フック",
        r"セクション|配分|15\s*/\s*70\s*/\s*15|15%|70%|転結|導入|展開",
        r"山場|クライマックス", r"承認", r"五感|感覚", r"非視覚|触覚|嗅覚|味覚", r"Golden|ゴールデン|サンプル",
        r"KPI|品質|ゲート|評価", r"公開|タグ|予約|タイトル", r"伏線|小道具|世界観",
    ],
    # Step-specific hints (partial, used in addition to core)
    "00": [r"スコープ|scope", r"制約|constraints", r"次話|引き継|継続"],
    "01": [r"起承転結", r"開始|終了", r"承認"],
    "02": [r"セクション|フェーズ|配分"],
    "03": [r"テーマ|独自性|Golden|比較|USP"],
    "04": [r"緩急|比率|フック"],
    "05": [r"シーン|ビート|scene|beats|pov"],
    "06": [r"論理|因果|動機|矛盾|修正"],
    "07": [r"口調|台詞|一貫性"],
    "08": [r"対話|サブテキスト|目的"],
    "09": [r"感情|カーブ|delta|before|after"],
    "10": [r"雰囲気|世界観|五感|sensory"],
    "11": [r"伏線|小道具|回収"],
    "12": [r"初稿|Markdown|見出し"],
    "13": [r"文字数|段落|60字|骨組み"],
    "14": [r"可読性|禁止表現|五感"],
    "15": [r"スマホ|会話比率|読みやすさ"],
    "16": [r"KPI|合否|総合点"],
    "17": [r"読者体験|公開|タグ|予約|校正"],
    "18": [r"最終確認|公開可否|チェックリスト"],
}


def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def concepts_for_step(step_key: str) -> List[str]:
    return CONCEPTS["core"] + CONCEPTS.get(step_key, [])


def audit_step(step: int, old: Path, new: Path) -> dict:
    old_txt = load_text(old)
    new_txt = load_text(new)
    step_key = f"{step:02d}"
    patterns = concepts_for_step(step_key)
    missing = []
    covered = []
    for pat in patterns:
        if re.search(pat, old_txt, flags=re.IGNORECASE):
            if re.search(pat, new_txt, flags=re.IGNORECASE):
                covered.append(pat)
            else:
                missing.append(pat)
    coverage = 0.0 if not (covered or missing) else len(covered) / (len(covered) + len(missing))
    return {
        "step": step,
        "old_exists": old.exists(),
        "new_exists": new.exists(),
        "covered": covered,
        "missing": missing,
        "coverage": coverage,
    }


def main() -> int:
    backup_dirs = sorted(ROOT.glob("templates_backup_*"))
    if not backup_dirs:
        print("No backup directories found under project root.")
        return 2
    backup = backup_dirs[-1]

    report_lines = ["# Template Migration Audit (v1→v2)", "", f"Backup: {backup.name}", ""]
    any_issue = False
    for step in range(0, 19):
        old = backup / f"write_step{step:02d}_"  # prefix only
        # find the first matching old file for the step
        old_files = list(backup.glob(f"write_step{step:02d}_*.yaml"))
        if not old_files:
            report_lines.append(f"- STEP {step:02d}: old missing")
            any_issue = True
            continue
        old_file = old_files[0]
        new_file = ROOT / "templates" / "writing" / f"write_step{step:02d}_*.yaml"
        new_files = list((ROOT / "templates" / "writing").glob(f"write_step{step:02d}_*.yaml"))
        if not new_files:
            report_lines.append(f"- STEP {step:02d}: new missing")
            any_issue = True
            continue
        new_file = new_files[0]
        res = audit_step(step, old_file, new_file)
        cov_pct = int(res["coverage"] * 100)
        status = "OK" if res["coverage"] >= 0.8 else ("WARN" if res["coverage"] >= 0.5 else "FAIL")
        if status != "OK":
            any_issue = True
        report_lines.append(f"## STEP {step:02d} — {status} ({cov_pct}% coverage)")
        report_lines.append(f"- old: {old_file.relative_to(ROOT)}")
        report_lines.append(f"- new: {new_file.relative_to(ROOT)}")
        if res["missing"]:
            report_lines.append("- Missing concepts from v1 → v2:")
            for pat in res["missing"]:
                report_lines.append(f"  - `{pat}`")
        if res["covered"]:
            report_lines.append("- Preserved concepts:")
            for pat in res["covered"]:
                report_lines.append(f"  - `{pat}`")
        report_lines.append("")

    out_dir = ROOT / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "template_migration_audit.md"
    out_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"Wrote audit report to {out_path}")
    return 1 if any_issue else 0


if __name__ == "__main__":
    raise SystemExit(main())

