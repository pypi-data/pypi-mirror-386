# File: specs/_scripts/check_links.py
# Purpose: Check Markdown links under specs/ and report broken internal references
# Context: Validates reorg safety by ensuring relative links pointing within specs/ still resolve.

import re
from pathlib import Path
from typing import Iterable, List, Tuple


LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
CODE_BLOCK_RE = re.compile(r"```.*?```", re.S)


def iter_markdown(root: Path) -> Iterable[Path]:
    for p in root.rglob("*.md"):
        # Skip archive and meta; skip redirect stubs
        if any(part in {"archive", "_archive", "meta", "_meta"} for part in p.parts):
            continue
        try:
            head = p.open("r", encoding="utf-8-sig", errors="ignore").read(64)
            if head.lstrip().lower().startswith("# moved"):
                continue
        except Exception:
            pass
        yield p


def resolve_link(base: Path, href: str) -> Path:
    # Ignore anchors and external links
    if href.startswith("http:") or href.startswith("https:"):
        return Path("__external__")
    if href.startswith("#"):
        return Path("__anchor__")
    # Normalize "./" and strip anchors
    href = href.split("#", 1)[0]
    return (base.parent / href).resolve()


def check_links(specs_root: Path) -> List[Tuple[Path, str]]:
    broken: List[Tuple[Path, str]] = []
    specs_root = specs_root.resolve()
    for md in iter_markdown(specs_root):
        text = md.read_text(encoding="utf-8-sig", errors="ignore")
        text = CODE_BLOCK_RE.sub("", text)
        for m in LINK_RE.finditer(text):
            href = m.group(1).strip()
            target = resolve_link(md, href)
            # Only check paths that point back inside specs/
            if target.name in {"__external__", "__anchor__"}:
                continue
            try:
                target.relative_to(specs_root)
            except Exception:
                # Not inside specs → ignore
                continue
            if not target.exists():
                broken.append((md.relative_to(specs_root), href))
    return broken


def main():
    root = Path(__file__).resolve().parents[1]
    broken = check_links(root)
    if not broken:
        print("LLM:BEGIN")
        print("link_check: ok (no broken internal links)")
        print("LLM:END")
        return
    print("LLM:BEGIN")
    print(f"link_check: broken={len(broken)}")
    for md, href in broken:
        print(f"- {md.as_posix()} -> {href}")
    print("LLM:END")


if __name__ == "__main__":
    main()
