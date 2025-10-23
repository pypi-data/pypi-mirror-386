# Git Workflow Guide

**Version**: 1.0
**Last Updated**: 2025-10-12
**Status**: Active

## Purpose

This guide defines the Git workflow standards for the Noveler project to ensure:
- Clean and readable commit history
- Easy code review and debugging
- Safe rollback capabilities
- Consistent collaboration practices

---

## Commit Separation Policy

### Principle: One Commit = One Logical Change

Each commit should represent a single, atomic, logical change that can be:
- Understood independently
- Reviewed in isolation
- Reverted without side effects
- Cherry-picked to other branches

### Examples

#### ✅ Good: Separated Commits

```bash
# Commit 1: Test additions (no production code changes)
git commit -m "test: Add P3/P4 coverage for Anemic Domain Detection"

# Commit 2: Refactoring (no test changes)
git commit -m "refactor(arch): Remove unused Infrastructure Integration code"

# Commit 3: Documentation (no code changes)
git commit -m "docs(changelog): Add Infrastructure Integration cleanup entry"
```

#### ❌ Bad: Mixed Commits

```bash
# DON'T: Mix test additions and refactoring
git commit -m "test: Add tests and refactor Infrastructure Integration"
# Problem: Impossible to review test changes separately from refactoring
```

---

## Branch Strategy

### Main Branches

- **`master`**: Production-ready code
  - All commits must pass CI
  - Protected branch (no force push)
  - All changes via feature branches

### Feature Branches

Use separate branches for unrelated changes:

```bash
# Pattern: <type>/<short-description>
feature/anemic-detection-tests
refactor/infra-cleanup
fix/yaml-backward-compat
docs/workflow-guide
```

### Workflow

```bash
# 1. Create feature branch from master
git checkout master
git pull origin master
git checkout -b feature/my-feature

# 2. Make changes and commit atomically
git add <files>
git commit -m "feat: Implement feature X"

# 3. Keep branch up-to-date
git fetch origin
git rebase origin/master

# 4. Push and create PR
git push -u origin feature/my-feature
# Create PR via GitHub/GitLab UI

# 5. After PR approval, merge to master
# (GitHub: "Squash and merge" or "Rebase and merge" depending on commits)
```

---

## Commit Message Conventions

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Usage | Example |
|------|-------|---------|
| `feat` | New feature | `feat(quality): Add Service Logic Smell detection` |
| `fix` | Bug fix | `fix(domain): Add backward-compatible yaml_content property` |
| `refactor` | Code restructuring (no behavior change) | `refactor(arch): Remove unused Infrastructure Integration code` |
| `test` | Test additions/modifications (no code changes) | `test: Add P3/P4 coverage for Anemic Domain Detection` |
| `docs` | Documentation updates | `docs(workflow): Create Git Workflow Guide` |
| `style` | Code formatting (no logic changes) | `style(domain): Format with ruff` |
| `perf` | Performance improvements | `perf(cache): Optimize ServiceLocator cache lookup` |
| `build` | Build system changes | `build(deps): Update pytest to 8.3.0` |
| `ci` | CI/CD changes | `ci(github): Add xdist parallelization` |
| `chore` | Maintenance tasks | `chore(deps): Update pre-commit hooks` |

### Scopes

Common scopes in Noveler project:
- `domain`, `application`, `infrastructure`, `presentation`
- `quality`, `testing`, `docs`
- `mcp`, `cli`, `di`
- `arch` (architecture-wide changes)

### Subject Line Rules

- Use imperative mood ("Add" not "Added" or "Adds")
- Keep under 72 characters
- No period at the end
- Capitalize first letter

### Body (Optional but Recommended)

- Explain **why** (not what - code shows what)
- Wrap at 72 characters
- Separate from subject with blank line
- Use bullet points for multiple items

### Footer (Required for Breaking Changes)

```
BREAKING CHANGE: Description of breaking change

Closes #123
```

### Full Example

```
feat(quality): Add Service Logic Smell detection

Implement Tell Don't Ask and Direct Mutation anti-pattern detection
to improve domain model quality.

Features:
- AST-based code analysis
- CLI integration via `noveler check --service-logic-smell`
- Pre-commit hook with WARNING mode
- 26/26 tests passing (core: 24/24, integration: 2 xfail)

Closes #456

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Commit Atomicity Guidelines

### Rule 1: Separate Test Changes from Implementation

**Reason**: Tests should be reviewable independently to verify coverage.

```bash
# Step 1: Add tests (possibly with @pytest.mark.xfail)
git add tests/
git commit -m "test: Add Service Logic Smell detection tests"

# Step 2: Implement feature
git add src/
git commit -m "feat(quality): Implement Service Logic Smell detection"

# Step 3: Update docs
git add docs/ CHANGELOG.md
git commit -m "docs(quality): Add Service Logic Smell documentation"
```

### Rule 2: Separate Refactoring from Feature Work

**Reason**: Refactoring should not change behavior; mixing with features makes review difficult.

```bash
# DON'T: Mix refactoring and feature
git commit -m "feat: Add caching and refactor ServiceLocator"

# DO: Separate commits
git commit -m "refactor(di): Extract cache logic to separate method"
git commit -m "feat(di): Add xdist worker cache isolation"
```

### Rule 3: Separate Deletion from Addition

**Reason**: Deletions are easier to review when not mixed with additions.

```bash
# Step 1: Remove old code
git add -u  # Stage deletions only
git commit -m "refactor(arch): Remove unused Infrastructure Integration code"

# Step 2: Add new code (if replacing)
git add src/
git commit -m "feat(arch): Implement new Infrastructure Integration design"
```

### Rule 4: Keep Documentation Updates Separate

**Reason**: Documentation changes are often low-risk and can be reviewed quickly.

```bash
# Implementation commit
git commit -m "feat(quality): Add retry metrics recording"

# Documentation commit
git commit -m "docs(changelog): Add entry for retry metrics feature"
```

---

## Code Review Workflow

### Before Requesting Review

1. **Self-review**: Read your own diff as if you were a reviewer
2. **Run tests**: Ensure `make test` passes
3. **Check formatting**: Run `ruff check` and `ruff format`
4. **Update docs**: CHANGELOG.md, relevant guides
5. **Rebase on master**: Ensure no conflicts

### Creating a Pull Request

```bash
# 1. Push branch
git push -u origin feature/my-feature

# 2. Create PR (via CLI or UI)
# Title: Same as commit message (if single commit)
# Description: Summarize changes, link to issues

# 3. Self-review checklist
- [ ] All tests pass
- [ ] CHANGELOG.md updated
- [ ] Docs updated (if needed)
- [ ] Commit messages follow conventions
- [ ] Commits are atomic and well-separated
```

### Addressing Review Feedback

```bash
# Option A: Fixup commits (for small changes)
git add <files>
git commit --fixup=<commit-sha>
git rebase -i --autosquash origin/master

# Option B: New commits (for substantial changes)
git add <files>
git commit -m "review: Address feedback on error handling"

# Push updates
git push --force-with-lease origin feature/my-feature
```

---

## Advanced Techniques

### Interactive Rebase for Cleanup

```bash
# Split a mixed commit into separate commits
git rebase -i HEAD~3

# In editor, change "pick" to "edit" for the commit to split
# Then:
git reset HEAD^
git add tests/
git commit -m "test: Add tests"
git add src/
git commit -m "feat: Implement feature"
git rebase --continue
```

### Cherry-Picking

```bash
# Apply a single commit to another branch
git checkout target-branch
git cherry-pick <commit-sha>
```

### Amending Last Commit

```bash
# Add forgotten files to last commit
git add forgotten-file.py
git commit --amend --no-edit

# Change last commit message
git commit --amend -m "New commit message"
```

---

## Anti-Patterns to Avoid

### ❌ "WIP" or "fix" Commits

```bash
# DON'T
git commit -m "WIP"
git commit -m "fix"
git commit -m "temp"
```

**Solution**: Use interactive rebase to clean up before pushing:

```bash
git rebase -i HEAD~5  # Squash/reword WIP commits
```

### ❌ Mixing Unrelated Changes

```bash
# DON'T
git commit -m "feat: Add feature X and fix bug Y and update docs"
```

**Solution**: Create separate commits:

```bash
git add feature-x-files
git commit -m "feat: Add feature X"
git add bug-y-files
git commit -m "fix: Fix bug Y"
git add docs/
git commit -m "docs: Update documentation"
```

### ❌ Commit Message Lacks Context

```bash
# DON'T
git commit -m "Update code"
git commit -m "Fix issue"
```

**Solution**: Provide clear, specific descriptions:

```bash
git commit -m "refactor(di): Extract cache logic to _get_worker_cache() method"
git commit -m "fix(domain): Add backward-compatible yaml_content property"
```

---

## Emergency Procedures

### Undo Last Commit (Not Pushed)

```bash
# Keep changes in working directory
git reset --soft HEAD^

# Discard changes completely
git reset --hard HEAD^
```

### Undo Last Commit (Already Pushed)

```bash
# Create revert commit
git revert HEAD
git push origin master
```

### Fix Commit Message (Not Pushed)

```bash
git commit --amend -m "New message"
```

### Fix Commit Message (Already Pushed)

```bash
# DON'T change public history
# Instead, add clarification in next commit or PR description
```

---

## CI/CD Integration

### Pre-Commit Hooks

Configured in `.pre-commit-config.yaml`:
- Ruff linting and formatting
- MyPy type checking
- Encoding guard (U+FFFD detection)
- Root structure policy check
- Service Logic Smell check (WARNING mode)

**Bypass when needed** (use sparingly):

```bash
git commit --no-verify -m "..."
```

### Post-Commit Hooks

Automatic actions after commit:
- CODEMAP update
- Pre-push checks (background)

---

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Best Practices](https://git-scm.com/book/en/v2)
- [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/)
- Project-specific: [CLAUDE.md](../../CLAUDE.md), [AGENTS.md](../../AGENTS.md)

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-10-12 | 1.0 | Initial version based on code review recommendations |

---

**Maintained by**: Development Team
**Review Cycle**: Quarterly
**Feedback**: Create issue with label `process-improvement`
