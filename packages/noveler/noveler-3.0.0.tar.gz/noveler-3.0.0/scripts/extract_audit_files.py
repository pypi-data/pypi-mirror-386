#!/usr/bin/env python3
"""Extract unique files from audit script output."""

import subprocess
import sys
import re
from pathlib import Path
from collections import Counter

# Run audit
result = subprocess.run(
    [sys.executable, "scripts/comment_header_audit.py"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace"
)

# Combine stdout and stderr
output = result.stdout + result.stderr

# Extract file paths using regex
# Pattern: C:\...\filename.py:lineno: message
pattern = r'([A-Z]:[^:]+\.py):\d+:'
matches = re.findall(pattern, output)

# Normalize paths
file_counter = Counter()
for match in matches:
    try:
        path = Path(match)
        rel_path = path.relative_to(Path.cwd())
        file_counter[str(rel_path)] += 1
    except ValueError:
        file_counter[match] += 1

print(f"Total unique files with violations: {len(file_counter)}")
print(f"Total violations found: {sum(file_counter.values())}")
print()

print("Top 30 files by violation count:")
print("=" * 80)
for i, (file_path, count) in enumerate(file_counter.most_common(30), 1):
    # Replace problematic Unicode characters for display
    safe_path = file_path.replace('\ufffd', '?')
    print(f"{i:2d}. {safe_path:70s} ({count:4d} violations)")
