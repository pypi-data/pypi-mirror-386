# File: specs/_scripts/generate_specs_index.py
# Purpose: Generate a consistent specs/README.md index grouped by category
# Context: Keeps the specs index accurate after reorganizations without manual edits.

import os
import re
from pathlib import Path
from typing import Dict, List


def find_spec_files(root: Path) -> List[Path]:
    """Discover SPEC-*.md files under root, excluding archive paths.

    Args:
        root: specs/ directory.
    Returns:
        A list of Path objects for spec files.
    """
    excludes = {
        str(root / "archive"),
        str(root / "_archive"),
        str(root / "design"),
        str(root / "meta"),
        str(root / "_meta"),
    }
    results: List[Path] = []
    for p in root.rglob("SPEC-*.md"):
        # skip archive-like folders
        if any(str(p).startswith(prefix) for prefix in excludes):
            continue
        # skip redirect stubs (first line begins with '# Moved')
        try:
            head = p.open("r", encoding="utf-8-sig", errors="ignore").read(64)
            if head.lstrip().lower().startswith("# moved"):
                continue
        except Exception:
            pass
        results.append(p)
    return results


SPEC_RE = re.compile(r"SPEC-([A-Z0-9]+)-([A-Za-z0-9]+).*?\.md$")


def group_by_category(files: List[Path], root: Path) -> Dict[str, List[Path]]:
    groups: Dict[str, List[Path]] = {}
    for f in files:
        m = SPEC_RE.search(f.name)
        if not m:
            # try more permissive match: SPEC-<CAT>-<NNN...>
            m2 = re.match(r"SPEC-([A-Z0-9]+).*?\.md$", f.name)
            cat = m2.group(1) if m2 else "MISC"
        else:
            cat = m.group(1)
        groups.setdefault(cat, []).append(f)
    for cat in groups:
        groups[cat].sort(key=lambda p: p.name)
    return dict(sorted(groups.items(), key=lambda kv: kv[0]))


def make_link_text(path: Path) -> str:
    stem = path.stem
    # Prefer spec id prefix for clarity
    return stem


def generate_readme(root: Path) -> str:
    files = find_spec_files(root)
    groups = group_by_category(files, root)
    lines: List[str] = []
    lines.append("# specs index")
    lines.append("")
    lines.append("This index is auto-generated. Do not edit manually.")
    lines.append("")
    lines.append("Policy:")
    lines.append("- Keep canonical specs under category directories.")
    lines.append("- Archive old versions under specs/archive/<date>/.")
    lines.append("- Filenames follow SPEC-<CATEGORY>-<NNN>_<slug>.md where applicable.")
    lines.append("")
    for cat, paths in groups.items():
        lines.append(f"## {cat}")
        lines.append("")
        for p in paths:
            rel = p.relative_to(root)
            text = make_link_text(p)
            lines.append(f"- [{text}](./{rel.as_posix()})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    root = Path(__file__).resolve().parents[1]
    readme = generate_readme(root)
    (root / "README.md").write_text(readme, encoding="utf-8")


if __name__ == "__main__":
    main()
