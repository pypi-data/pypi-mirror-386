# File: scripts/diagnostics/setup_git_worktree.sh
# Purpose: Configure bare Git repository and working tree for WSL/Linux environments.
# Context: Mirrors PowerShell helper so developers can align core.worktree and environment quickly.

set -euo pipefail

log() {
  printf '[setup-git] %s\n' "$1"
}

usage() {
  cat <<'EOF'
Usage: setup_git_worktree.sh [--git-dir PATH] [--work-tree PATH] [--dry-run]

Options:
  --git-dir PATH     Path to bare git directory (default: ~/.git-noveler)
  --work-tree PATH   Path to working tree directory (default: /mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド)
  --dry-run          Show git commands without executing them
EOF
}

GIT_DIR_PATH="${HOME}/.git-noveler"
WORK_TREE_PATH="/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --git-dir)
      GIT_DIR_PATH="$2"
      shift 2
      ;;
    --work-tree)
      WORK_TREE_PATH="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      log "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if ! command -v git >/dev/null 2>&1; then
  log 'git command not found; install git and retry.'
  exit 1
fi

expand_path() {
  local path="$1"
  if [[ $path == ~* ]]; then
    echo "${path/#~/$HOME}"
  else
    echo "$path"
  fi
}

GIT_DIR_PATH=$(expand_path "$GIT_DIR_PATH")
WORK_TREE_PATH=$(expand_path "$WORK_TREE_PATH")

log "Git directory : $GIT_DIR_PATH"
log "Work tree     : $WORK_TREE_PATH"

if [[ ! -d "$GIT_DIR_PATH" ]]; then
  log "Git directory not found: $GIT_DIR_PATH"
  exit 1
fi
if [[ ! -d "$WORK_TREE_PATH" ]]; then
  log "Work tree directory not found: $WORK_TREE_PATH"
  exit 1
fi

run_git() {
  local args=("--git-dir=$GIT_DIR_PATH" "--work-tree=$WORK_TREE_PATH" "$@")
  if [[ $DRY_RUN -eq 1 ]]; then
    log "Preview: git ${args[*]}"
  else
    git "${args[@]}"
  fi
}

run_git config --local core.worktree "$WORK_TREE_PATH"
log 'core.worktree updated.'

if [[ $DRY_RUN -eq 1 ]]; then
  exit 0
fi

CURRENT=$(git --git-dir="$GIT_DIR_PATH" config --local --get core.worktree 2>/dev/null || true)
log "Current core.worktree: ${CURRENT:-<unset>}"

log 'Running git status to verify configuration...'
RUN_OUTPUT=$(GIT_DIR="$GIT_DIR_PATH" GIT_WORK_TREE="$WORK_TREE_PATH" git status --short)
log "$RUN_OUTPUT"

cat <<EOF
[setup-git] To export this context for the current shell:
  export GIT_DIR="$GIT_DIR_PATH"
  export GIT_WORK_TREE="$WORK_TREE_PATH"
[setup-git] Consider adding the above to your shell profile for persistence.
EOF
