#!/usr/bin/env bash
# File: scripts/ci/diff_gate.sh
# Purpose: CI diff gate—run collect-only pytest (smoke) and encoding guard limited to changed files.
# Usage: scripts/ci/diff_gate.sh [DIFF_RANGE]
#   DIFF_RANGE defaults to origin/main...HEAD
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../" && pwd)"
cd "$ROOT_DIR"

DIFF_RANGE=${1:-"origin/main...HEAD"}

echo "[diff-gate] Running collect-only pytest smoke"
python3 -m pytest --collect-only -q tests/docs/test_docs_sample_paths.py || {
  echo "[diff-gate] collect-only smoke failed" >&2
  exit 1
}

echo "[diff-gate] Running encoding guard for diff range: $DIFF_RANGE"
python scripts/hooks/encoding_guard.py \
  --diff-range "$DIFF_RANGE" \
  --fail src/**/*.py \
  --warn docs/**/*.md \
  --exclude docs/archive/** docs/backup/**

echo "[diff-gate] Generating encoding scan summary"
python3 scripts/report_encoding_summary.py || true

echo "[diff-gate] Done"