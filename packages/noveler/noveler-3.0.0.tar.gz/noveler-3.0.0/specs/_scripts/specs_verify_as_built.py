"""Specs.scripts.specs_verify_as_built
Where: Specs automation script verifying as-built documentation.
What: Confirms the as-built documentation matches expectations.
Why: Provides assurance that generated docs reflect actual system state.
"""

#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def load_registry():
    data = json.loads(read(ROOT / "_meta/_registry.json"))
    entries = data.get("entries", [])
    return {e["spec_id"]: e for e in entries}


def parse_e2e_mapping():
    text = read(ROOT / "E2E_TEST_MAPPING.yaml")
    out = {}
    if not text:
        return out
    lines = text.splitlines()
    in_e2e = False
    cur_sid = None
    for i, line in enumerate(lines):
        if line.strip().startswith('#'):
            continue
        if not in_e2e:
            if re.match(r"^e2e_mappings:\s*$", line):
                in_e2e = True
            continue
        if re.match(r"^[A-Za-z_]+:\s*$", line):
            break
        m = re.match(r"^\s{2,}(SPEC-[A-Z0-9-]+):\s*$", line)
        if m:
            cur_sid = m.group(1)
            continue
        if cur_sid:
            mt = re.search(r'test_path:\s*"([^"]+)"', line)
            if mt:
                out[cur_sid] = mt.group(1)
                cur_sid = None
    return out


def parse_req_status():
    md = read(ROOT / "REQ_SPEC_MAPPING_MATRIX.md")
    out = {}
    for line in md.splitlines():
        if not line.strip().startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|\n').split('|')]
        if len(cells) < 4 or cells[0] == '要件ID':
            continue
        specfile = cells[2]
        status = cells[3]
        m = re.match(r'(SPEC-[A-Za-z0-9-]+)', specfile)
        if m:
            sid = m.group(1)
            out[sid] = status
    return out


def main(argv):
    reg = load_registry()
    e2e_map = parse_e2e_mapping()
    req_status = parse_req_status()

    issues = []
    counts = {"both": 0, "e2e": 0, "req": 0, "impl": 0, "inprog": 0, "unknown": 0}

    for sid, e in sorted(reg.items()):
        srcs = set(e.get("sources") or [])
        src_tag = 'BOTH' if srcs == {'E2E', 'REQ'} else ('E2E' if srcs == {'E2E'} else ('REQ' if srcs == {'REQ'} else ','.join(sorted(srcs))))
        if src_tag == 'BOTH': counts["both"] += 1
        elif src_tag == 'E2E': counts["e2e"] += 1
        elif src_tag == 'REQ': counts["req"] += 1

        # REQ status
        st = req_status.get(sid)
        if st is None:
            counts["unknown"] += 1
        elif '実装済み' in st:
            counts["impl"] += 1
        elif '実装中' in st:
            counts["inprog"] += 1
        else:
            counts["unknown"] += 1

        # E2E test existence check for E2E/BOTH
        if src_tag in ('E2E', 'BOTH'):
            tpath = e2e_map.get(sid)
            if not tpath or not Path(tpath).exists():
                issues.append((sid, f"missing-e2e-test:{tpath or 'N/A'}"))

        # As-built rule: if REQ-only, must be 実装済み; if E2E/BOTH, must have test present and REQ status 実装済み (if available)
        if src_tag == 'REQ' and not (st and '実装済み' in st):
            issues.append((sid, f"req-not-implemented:{st or 'N/A'}"))
        if src_tag in ('E2E', 'BOTH'):
            # test path present is already checked; also check status if available
            if st and '実装済み' not in st:
                issues.append((sid, f"req-status-not-implemented:{st}"))

    print("[AS-BUILT SUMMARY]")
    print(f"  Current specs: {len(reg)} | Sources BOTH:{counts['both']} E2E:{counts['e2e']} REQ:{counts['req']}")
    print(f"  REQ status: 実装済み:{counts['impl']} 実装中:{counts['inprog']} 不明:{counts['unknown']}")
    if issues:
        print(f"[AS-BUILT] FAILED: {len(issues)} issues")
        for sid, msg in issues[:20]:
            print(f"  - {sid}: {msg}")
        return 1
    print("[AS-BUILT] OK: All current specs meet as-built criteria")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
