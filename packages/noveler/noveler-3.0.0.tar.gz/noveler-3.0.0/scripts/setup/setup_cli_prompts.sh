#!/usr/bin/env bash
# File: scripts/setup/setup_cli_prompts.sh
# Purpose: Safely wire a single source prompts directory into both Codex and Claude Code CLIs.
# Context: Creates symlinks so that Codex (at ~/.codex/prompts) and Claude Code (at ~/.claude/commands)
#          see the same prompts managed under this repository (prompts/). Default actions are conservative
#          and reversible; no destructive operations are performed without --force.

set -euo pipefail

print_usage() {
  cat <<'USAGE'
Setup prompts directory for Codex and Claude Code via symlinks.

By default, links repository prompts/ into:
  - ~/.codex/prompts      (Codex)
  - ~/.claude/commands    (Claude Code; merged file-level symlinks to preserve existing files)

Options:
  --source-dir <dir>        Source prompts directory (default: repo_root/prompts)
  --home-dir <dir>          Override HOME detection (for testing)
  --force                   Allow replacing existing targets (with timestamped backup)
  --dry-run                 Show actions without making changes
  --claude-mode <merge|link>
                            merge (default): create file-level symlinks into ~/.claude/commands
                            link: replace ~/.claude/commands with a symlink to --source-dir
  -h, --help                Show this help

Examples:
  bash scripts/setup/setup_cli_prompts.sh
  bash scripts/setup/setup_cli_prompts.sh --dry-run
  bash scripts/setup/setup_cli_prompts.sh --force --claude-mode link
USAGE
}

ts() { date +"%Y%m%d_%H%M%S"; }

log()  { echo "[setup-prompts] $*"; }
warn() { echo "[setup-prompts][warn] $*" >&2; }
err()  { echo "[setup-prompts][error] $*" >&2; }

# Resolve project root and default source
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
DEFAULT_SOURCE="$PROJECT_ROOT/prompts"

SOURCE_DIR="$DEFAULT_SOURCE"
HOME_DIR="${HOME:-$PROJECT_ROOT}"
FORCE=false
DRY_RUN=false
CLAUDE_MODE="merge"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source-dir)
      SOURCE_DIR="$2"; shift 2 ;;
    --home-dir)
      HOME_DIR="$2"; shift 2 ;;
    --force)
      FORCE=true; shift ;;
    --dry-run)
      DRY_RUN=true; shift ;;
    --claude-mode)
      CLAUDE_MODE="$2"; shift 2 ;;
    -h|--help)
      print_usage; exit 0 ;;
    *)
      err "Unknown argument: $1"; print_usage; exit 2 ;;
  esac
done

ensure_dir() {
  local path="$1"
  if [[ "$DRY_RUN" == true ]]; then
    log "[dry-run] mkdir -p $path"
  else
    mkdir -p "$path"
  fi
}

backup_path() {
  local path="$1"
  local backup="${path}.backup_$(ts)"
  if [[ "$DRY_RUN" == true ]]; then
    log "[dry-run] backup -> $backup"
  else
    if [[ -e "$path" || -L "$path" ]]; then
      mv "$path" "$backup"
      log "backup created: $backup"
    fi
  fi
}

safe_symlink() {
  local src="$1"
  local dst="$2"
  local parent
  parent=$(dirname "$dst")
  ensure_dir "$parent"

  if [[ -L "$dst" ]]; then
    # If already pointing to src, do nothing
    local cur
    cur=$(readlink -f "$dst" || true)
    local abs
    abs=$(readlink -f "$src" || true)
    if [[ "$cur" == "$abs" ]]; then
      log "unchanged symlink: $dst -> $src"
      return 0
    fi
  fi

  if [[ -e "$dst" || -L "$dst" ]]; then
    if [[ "$FORCE" == true ]]; then
      backup_path "$dst"
    else
      warn "exists: $dst (use --force to replace)"; return 0
    fi
  fi

  if [[ "$DRY_RUN" == true ]]; then
    log "[dry-run] ln -s $src $dst"
  else
    ln -s "$src" "$dst"
    log "symlink created: $dst -> $src"
  fi
}

safe_symlink_into_dir() {
  # Create a symlink inside target dir pointing to src file as same basename
  local src="$1"
  local target_dir="$2"
  local name
  name=$(basename "$src")
  local dst="$target_dir/$name"
  if [[ -e "$dst" || -L "$dst" ]]; then
    # If destination exists but is not our symlink to src, keep it (non-destructive)
    local is_link_to_src=false
    if [[ -L "$dst" ]]; then
      local cur
      cur=$(readlink -f "$dst" || true)
      local abs
      abs=$(readlink -f "$src" || true)
      if [[ "$cur" == "$abs" ]]; then
        is_link_to_src=true
      fi
    fi
    if [[ "$is_link_to_src" == true ]]; then
      log "unchanged file-link: $dst -> $src"
    else
      warn "kept existing: $dst"
    fi
    return 0
  fi
  if [[ "$DRY_RUN" == true ]]; then
    log "[dry-run] ln -s $src $dst"
  else
    ln -s "$src" "$dst"
    log "file symlink created: $dst -> $src"
  fi
}

# Validate source
if [[ ! -d "$SOURCE_DIR" ]]; then
  err "source directory not found: $SOURCE_DIR"; exit 1
fi

log "Project root : $PROJECT_ROOT"
log "Source dir   : $SOURCE_DIR"
log "Home dir     : $HOME_DIR"
log "Claude mode  : $CLAUDE_MODE"
log "Force        : $FORCE, Dry-run: $DRY_RUN"

# 1) Codex: ~/.codex/prompts -> SOURCE_DIR
CODEX_DIR="$HOME_DIR/.codex"
CODEX_PROMPTS="$CODEX_DIR/prompts"
ensure_dir "$CODEX_DIR"
safe_symlink "$SOURCE_DIR" "$CODEX_PROMPTS"

# 2) Claude Code
CLAUDE_DIR="$HOME_DIR/.claude"
CLAUDE_CMDS="$CLAUDE_DIR/commands"
ensure_dir "$CLAUDE_DIR"

case "$CLAUDE_MODE" in
  link)
    # Replace ~/.claude/commands with a symlink to SOURCE_DIR (non-destructive unless --force)
    safe_symlink "$SOURCE_DIR" "$CLAUDE_CMDS"
    ;;
  merge)
    ensure_dir "$CLAUDE_CMDS"
    # Link Markdown files only from SOURCE_DIR into ~/.claude/commands (top-level, non-recursive)
    while IFS= read -r -d '' f; do
      # Only .md files
      if [[ -f "$f" ]]; then
        safe_symlink_into_dir "$f" "$CLAUDE_CMDS"
      else
        warn "skip non-file: $f"
      fi
    done < <(find "$SOURCE_DIR" -maxdepth 1 -mindepth 1 -type f -name '*.md' -print0 | sort -z)
    ;;
  *)
    err "invalid --claude-mode: $CLAUDE_MODE (use merge|link)"; exit 2 ;;
esac

log "Done."
