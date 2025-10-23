#!/usr/bin/env python3
"""CI wrapper: write tool smoke check (offline, no LLM)

Generates a minimal JSON describing the intended write target and prompt stub.
- Resolves project root and episode-target manuscript path via PathService
- Optionally derives a plot artifact hash if a plot file exists
- Exits 2 when --fail-on-path-fallback and any PathService fallback occurred
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from noveler.infrastructure.adapters.path_service_adapter import create_path_service


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Smoke-run the write tool (no LLM), produce a JSON payload")
    p.add_argument("--episode", type=int, default=1, help="Episode number to target")
    p.add_argument("--project-root", type=str, default=None, help="Project root to analyze (changes working directory)")
    p.add_argument("--out", type=str, default=None, help="Path to write JSON result; also prints to stdout (default: temp/write_smoke.json)")
    p.add_argument("--fail-on-path-fallback", action="store_true", help="Exit with failure if path_fallback_used is true")
    return p.parse_args()


def auto_select_sample_project_if_needed(args: argparse.Namespace) -> None:
    if args.project_root:
        os.chdir(args.project_root)
        return
    # Heuristic: when running from 00_ガイド repo, prefer sibling sample project if present
    try:
        guide_root = ROOT
        if guide_root.exists() and guide_root.name.endswith("00_ガイド"):
            sample = guide_root.parent / "10_Fランク魔法使いはDEBUGログを読む"
            if sample.exists() and sample.is_dir():
                os.chdir(sample)
    except Exception:
        pass


def main() -> int:
    args = parse_args()
    auto_select_sample_project_if_needed(args)

    # Resolve paths
    ps = create_path_service()
    episode = int(args.episode)
    manuscript_path = ps.get_manuscript_path(episode)

    # Try to locate plot and derive a pseudo artifact id (hash)
    plot_file = None
    plot_artifact_id = None
    try:
        if hasattr(ps, "get_episode_plot_path"):
            plot_file = ps.get_episode_plot_path(episode)
        if plot_file and plot_file.exists():
            content = plot_file.read_text(encoding="utf-8")
            h = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
            plot_artifact_id = f"artifact-{h}"
    except Exception:
        plot_artifact_id = None

    # Minimal prompt stub (offline)
    prompt = (
        f"# 第{episode:03d}話 原稿執筆スモーク\n\n"
        f"- 目標: 500-800文字\n- 文体: ライトノベル調\n- 視点: 三人称単元\n\n"
        f"プロット参照: {plot_artifact_id or 'なし'}\n"
    )

    # Collect PathService fallback events if any
    fallback_events = []
    if hasattr(ps, "get_and_clear_fallback_events"):
        try:
            fallback_events = ps.get_and_clear_fallback_events() or []
        except Exception:
            fallback_events = []

    result = {
        "success": True,
        "episode": episode,
        "manuscript_path": str(manuscript_path),
        "prompt": prompt,
        "plot_artifact_id": plot_artifact_id,
        "path_fallback_used": bool(fallback_events),
        "path_fallback_events": fallback_events,
    }

    payload = json.dumps(result, ensure_ascii=False)
    print(payload)

    outp = Path(args.out) if args.out else Path("temp") / "write_smoke.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(payload, encoding="utf-8")

    if args.fail_on_path_fallback and result["path_fallback_used"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
