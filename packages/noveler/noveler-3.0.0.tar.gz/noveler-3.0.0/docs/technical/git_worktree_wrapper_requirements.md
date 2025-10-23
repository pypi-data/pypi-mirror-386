# Git Worktree Wrapper Requirements

## Context
- Bare Git repository resides under WSL (e.g., `~/.git-noveler`).
- Working tree is synced via OneDrive on Windows (`C:\Users\bamboocity\OneDrive\Documents\9_小説\00_ガイド`).
- Developers switch between PowerShell on Windows and Bash inside WSL; consistent Git configuration is required to avoid manual `core.worktree` or environment variable edits.

## Goals
1. Automate `core.worktree` configuration for the bare repository.
2. Provide launchers that set `GIT_DIR` / `GIT_WORK_TREE` before invoking Git commands.
3. Verify configuration by running `git status` and reporting the result.
4. Offer symmetric tooling for PowerShell and Bash to support both Windows-native and WSL workflows.

## Deliverables
- PowerShell script (candidate path: `scripts/diagnostics/setup_git_worktree.ps1`).
  - Functions:
    - `Set-GitWorktreeConfig` to set `core.worktree` and optional `core.bare`.
    - `Invoke-GitStatusCheck` to run `git status` and surface exit code + summary.
  - Adds convenience alias (e.g., `Set-NovelerGitContext`) to user profile when run with `-Persist` flag.
- Bash script (candidate path: `scripts/diagnostics/setup_git_worktree.sh`).
  - Equivalent functions using `git config --local` and `git status` validation.
  - Optional symlink into `~/bin` for easy invocation.
- Documentation snippet for README / migration guide describing usage.

## Required Parameters
- Bare repository path (default: `~/.git-noveler`).
- Working tree path (default: `/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド`).
- Optional `--dry-run` to preview commands.

## Validation Steps
1. Confirm the script prints current `core.worktree` before and after changes.
2. Execute `git status` and expose exit code + short summary line (e.g., "clean" vs "changes present").
3. In PowerShell, ensure environment variables are reverted after invocation unless `-PersistEnv` is specified.
4. Provide meaningful error messages when repository or worktree directories are missing.

## Open Questions
- Should we support multiple worktrees (e.g., temp sandboxes)? Potential future enhancement.
- Is there a need to toggle OneDrive sync settings automatically? Currently out of scope; document manual checks instead.
