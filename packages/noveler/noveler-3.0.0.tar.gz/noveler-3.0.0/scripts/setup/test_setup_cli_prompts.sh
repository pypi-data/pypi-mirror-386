#!/usr/bin/env bash
# File: scripts/setup/test_setup_cli_prompts.sh
# Purpose: Sandboxed test for setup_cli_prompts.sh without touching real $HOME.
# Context: Creates a temporary HOME under workspace/temp/, runs setup with --home-dir,
#          then asserts the expected symlinks exist and point to the repo prompts/.

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
SETUP_SCRIPT="$ROOT_DIR/scripts/setup/setup_cli_prompts.sh"
SOURCE_DIR="$ROOT_DIR/prompts"
SANDBOX_HOME="$ROOT_DIR/workspace/temp/home_test_prompts"

echo "[test] root: $ROOT_DIR"
echo "[test] setup: $SETUP_SCRIPT"
echo "[test] source: $SOURCE_DIR"
echo "[test] sandbox home: $SANDBOX_HOME"

rm -rf "$SANDBOX_HOME"
mkdir -p "$SANDBOX_HOME"

# Ensure sample files exist in prompts/
mkdir -p "$SOURCE_DIR"
echo "Sample A" > "$SOURCE_DIR/sample_a.md"
echo "Sample B" > "$SOURCE_DIR/sample_b.md"

# Dry-run first
bash "$SETUP_SCRIPT" --home-dir "$SANDBOX_HOME" --dry-run

# Real run (force to ensure idempotence)
bash "$SETUP_SCRIPT" --home-dir "$SANDBOX_HOME" --force

# Assertions
COD_PATH="$SANDBOX_HOME/.codex/prompts"
CLA_PATH="$SANDBOX_HOME/.claude/commands"

if [[ ! -L "$COD_PATH" ]]; then
  echo "[test][fail] ~/.codex/prompts is not a symlink: $COD_PATH" >&2
  exit 1
fi

RESOLVED=$(readlink -f "$COD_PATH")
SRC_RES=$(readlink -f "$SOURCE_DIR")
if [[ "$RESOLVED" != "$SRC_RES" ]]; then
  echo "[test][fail] ~/.codex/prompts does not point to source ($RESOLVED != $SRC_RES)" >&2
  exit 1
fi

# Claude merge mode: file-level links should exist
for f in sample_a.md sample_b.md; do
  if [[ ! -L "$CLA_PATH/$f" ]]; then
    echo "[test][fail] ~/.claude/commands/$f is not a symlink" >&2
    exit 1
  fi
  R=$(readlink -f "$CLA_PATH/$f")
  if [[ "$R" != "$SRC_RES/$f" ]]; then
    echo "[test][fail] ~/.claude/commands/$f does not point to source file" >&2
    exit 1
  fi
done

echo "[test][ok] setup_cli_prompts.sh passed in sandbox"
