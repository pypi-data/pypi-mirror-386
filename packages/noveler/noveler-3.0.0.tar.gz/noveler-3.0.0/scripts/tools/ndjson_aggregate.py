#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from collections import defaultdict
from pathlib import Path
from typing import Any

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Aggregate fail-only NDJSON into Markdown summary")
    p.add_argument("--input", default="reports/llm_fail.ndjson")
    p.add_argument("--output", default="reports/llm_fail_summary.md")
    p.add_argument("--top", type=int, default=50)
    return p.parse_args()

def load_ndjson(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line=line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out

def aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_test = defaultdict(lambda: {"failed":0, "error":0, "crashed":0, "last_phase":None, "last_duration_s":0.0})
    failed=error=crashed=0
    workers=set()
    for rec in records:
        if rec.get("event")!="test_phase":
            continue
        oc=str(rec.get("outcome",""))
        if oc not in {"failed","error","crashed"}: continue
        tid=str(rec.get("test_id",""))
        by_test[tid][oc]+=1
        by_test[tid]["last_phase"]=rec.get("phase")
        try:
            by_test[tid]["last_duration_s"]=float(rec.get("duration_s",0.0) or 0.0)
        except Exception:
            pass
        if oc=="failed": failed+=1
        elif oc=="error": error+=1
        else: crashed+=1
        w=rec.get("worker_id")
        if w: workers.add(w)
    return {"by_test":by_test, "failed":failed, "error":error, "crashed":crashed, "workers":workers}

def to_markdown(summary: dict[str, Any], records: list[dict[str, Any]], top_n: int) -> str:
    total=summary["failed"]+summary["error"]+summary["crashed"]
    workers=", ".join(sorted(summary["workers"])) if summary["workers"] else "-"
    md=[]
    md.append("# Fail-only NDJSON Summary
")
    md.append(f"- Total fail events: {total} (failed={summary['failed']}, error={summary['error']}, crashed={summary['crashed']})")
    md.append(f"- Workers: {workers}
")
    items=list(summary["by_test"].items())
    items.sort(key=lambda kv: kv[1]['failed']+kv[1]['error']+kv[1]['crashed'], reverse=True)
    if items:
        md.append("## Top Failing Tests
")
        md.append("| # | Test ID | failed | error | crashed | last_phase | last_duration_s |")
        md.append("|---:|---|---:|---:|---:|---|---:|")
        for i,(tid,c) in enumerate(items[:top_n],1):
            md.append(f"| {i} | {tid} | {c['failed']} | {c['error']} | {c['crashed']} | {c.get('last_phase') or '-'} | {c.get('last_duration_s',0.0):.3f} |")
        md.append("")
    else:
        md.append("> No failing events were recorded.
")
    # session summary block
    ss=None
    for rec in reversed(records):
        if rec.get("event")=="session_summary":
            ss=rec; break
    if ss:
        md.append("## Session Summary
")
        md.append("```json")
        md.append(json.dumps(ss, ensure_ascii=False, indent=2))
        md.append("```")
    return "
".join(md)+"
"

def main()->int:
    args=parse_args()
    inp=Path(args.input)
    outp=Path(args.output)
    outp.parent.mkdir(parents=True, exist_ok=True)
    recs=load_ndjson(inp)
    summ=aggregate(recs)
    md=to_markdown(summ, recs, args.top)
    outp.write_text(md, encoding='utf-8')
    print(outp)
    return 0

if __name__=='__main__':
    raise SystemExit(main())
