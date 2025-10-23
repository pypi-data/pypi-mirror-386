#!/usr/bin/env python3
"""Clear __pycache__ directories after ruff execution."""

import shutil
from pathlib import Path

dirs = list(Path('.').rglob('__pycache__'))
count = 0

for d in dirs:
    try:
        shutil.rmtree(d)
        count += 1
    except (OSError, PermissionError):
        pass

print(f'[pre-commit] Cleared {count}/{len(dirs)} cache dirs')
