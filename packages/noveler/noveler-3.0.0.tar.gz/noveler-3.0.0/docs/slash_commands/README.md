# Slash Commands Reference

**WARNING: AUTO-GENERATED**: Do not edit manually. Regenerate with `python scripts/setup/build_slash_commands.py`

**Last Updated**: 2025-10-16 22:14:48

## Available Commands

### Quality

#### `/noveler-quality`

Noveler quality checking and auto-fix

**Type**: MCP-based command

**MCP Tools**:
- `mcp__noveler__run_quality_checks`
- `mcp__noveler__fix_quality_issues`
- `mcp__noveler__improve_quality_until`
- `mcp__noveler__export_quality_report`

**Global Definition**: [~/.claude/commands/noveler-quality.md](~/.claude/commands/noveler-quality.md)

**Tags**: `noveler`, `quality`, `check`, `mcp`

---

### Testing

#### `/test`

Run pytest with LLM-friendly output

**Tags**: `testing`, `pytest`

---

#### `/test-failed`

Re-run only failed tests from last run

**Tags**: `testing`, `pytest`, `failed`

---

#### `/test-changed`

Run tests for changed files (git diff based)

**Tags**: `testing`, `pytest`, `git`

---

### Workflow

#### `/b20-workflow`

B20 Development Workflow (5 phases: requirements, design, implement, test, review)

**Arguments**: `scripts/workflows/b20_workflow.py` `{phase}` `{prompt}`

**Tags**: `b20`, `workflow`, `development`

---

### Writing

#### `/noveler-write`

Noveler writing workflow - 18-step system with A28 templates

**Type**: MCP-based command

**MCP Tools**:
- `mcp__noveler__enhanced_get_writing_tasks`
- `mcp__noveler__enhanced_execute_writing_step`
- `mcp__noveler__polish_manuscript`
- `mcp__noveler__polish_manuscript_apply`

**Global Definition**: [~/.claude/commands/noveler-write.md](~/.claude/commands/noveler-write.md)

**Tags**: `noveler`, `write`, `a28`, `mcp`

---

#### `/noveler-polish`

Noveler manuscript polishing - A40 integrated workflow

**Type**: MCP-based command

**MCP Tools**:
- `mcp__noveler__polish_manuscript`
- `mcp__noveler__polish_manuscript_apply`
- `mcp__noveler__restore_manuscript_from_artifact`

**Global Definition**: [~/.claude/commands/noveler-polish.md](~/.claude/commands/noveler-polish.md)

**Tags**: `noveler`, `polish`, `a40`, `mcp`

---
