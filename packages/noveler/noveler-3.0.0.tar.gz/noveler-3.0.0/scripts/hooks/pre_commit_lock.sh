#!/bin/bash
# File: scripts/hooks/pre_commit_lock.sh
# Purpose: Serialize pre-commit execution across multiple sessions to prevent
#          race conditions during ruff/pre-commit auto-fix that cause Python
#          bytecode cache corruption
# Context: Part of Phase 2 cache corruption prevention strategy
#          (docs/troubleshooting/python_cache_corruption.md)

LOCK_FILE=".git/hooks/pre-commit.lock"
MAX_WAIT=30

acquire_lock() {
    local waited=0

    while [ -f "$LOCK_FILE" ]; do
        if [ $waited -ge $MAX_WAIT ]; then
            echo "[WARN] Pre-commit lock timeout (${MAX_WAIT}s). Removing stale lock."
            rm -f "$LOCK_FILE"
            break
        fi
        echo "[WAIT] Waiting for other pre-commit session... ($waited/${MAX_WAIT}s)"
        sleep 1
        waited=$((waited + 1))
    done

    echo $$ > "$LOCK_FILE"
    trap "rm -f $LOCK_FILE" EXIT INT TERM
}

acquire_lock
