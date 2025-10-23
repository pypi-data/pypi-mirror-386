**Purpose**
- Unify prompt storage for both Codex and Claude Code by symlinking a single source directory (this repo’s `prompts/`) into each CLI’s default lookup locations.

**Source Directory**
- Repository-managed: `prompts/`
- Absolute example (current repo): `/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/prompts/`
- Format: Markdown files only (`*.md`)

**Targets**
- Codex: `~/.codex/prompts`
- Claude Code: `~/.claude/commands`

**Install**
- Run the setup script (non-destructive by default; add `--force` to replace existing targets with backups):
- `bash scripts/setup/setup_cli_prompts.sh`
- Dry-run: `bash scripts/setup/setup_cli_prompts.sh --dry-run`
- Force: `bash scripts/setup/setup_cli_prompts.sh --force`
- Claude mode:
  - `merge` (default) creates file-level symlinks inside `~/.claude/commands` to preserve existing commands.
  - `link` replaces `~/.claude/commands` with a single symlink to `prompts/` (use `--force` if it exists).
  - Example: `bash scripts/setup/setup_cli_prompts.sh --force --claude-mode link`

**Options**
- `--source-dir <dir>`: Alternative source (defaults to repo `prompts/`).
- `--home-dir <dir>`: Override `$HOME` (useful for tests or sandbox).
- `--dry-run`: Print actions only.
- `--force`: Replace existing targets with a timestamped backup.

**Test (Sandboxed)**
- Runs without touching your real `$HOME`:
- `bash scripts/setup/test_setup_cli_prompts.sh`
- Verifies:
  - `~/.codex/prompts` is a symlink pointing to repo `prompts/`
  - `~/.claude/commands` contains symlinks to Markdown files in repo `prompts/`

**Notes**
- Minimal, reversible changes; no extra dependencies.
- If you already maintain `~/.claude/commands`, prefer `merge` mode to keep existing commands intact.
- If both CLIs are expected to read nested directories, switching Claude to `link` mode is simpler and robust.

**Next Steps**
- If later you want the CLIs to support metadata (frontmatter) and variable injection, consider adding a simple loader in each CLI. This document focuses on unifying the storage path only.
