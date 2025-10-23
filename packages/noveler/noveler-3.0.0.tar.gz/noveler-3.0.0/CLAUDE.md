# CLAUDE.md

## Scope

* This document defines **additional contracts specific to Claude Code + MCP environment**.
* Fundamental principles, workflow, comments, and testing rules are governed by **@AGENTS.md**.
* If any conflict arises between this document and AGENTS.md, both must be updated together to maintain consistency.

---

## Language & Output

* **All responses to users must be in Japanese.**
* Use Japanese only for explanations, errors, and reports. English words are allowed only as technical terms.
* Default output is lightweight (B20 policy). Use `issue_id`, `file_hash`, `line_hash`, `block_hash` instead of embedding full content.

---

## MCP Operations

* **Entry point**: Use `noveler mcp call <tool>`. CLI may be referenced only as historical documentation.
* **Server startup**: Use `noveler mcp-server` (Claude Code configuration via `codex.mcp.json`).
* **Configuration file priority**:

  1. `codex.mcp.json` (repository root) - Noveler MCP only
  2. `.mcp/config.json` (inside project `.mcp/`) - Noveler MCP only
  3. `.codex/mcp.json` - Multi-server config (manual management)
* **Automatic update**: Run `./bin/setup_mcp_configs` to safely back up and merge Noveler configurations (`--dry-run` supported).
* **SSOT management**: `scripts/setup/update_mcp_configs.py::ensure_mcp_server_entry()` is the **single source of truth**.
  * This function auto-detects environment (dev vs dist-only production) and generates correct paths.
  * Used by both setup scripts and `scripts/build.py` to ensure consistency.
  * See `docs/mcp/config_management.md` for detailed environment detection logic.

---

## Implementation Rules

* **Imports**:

  * Must use `noveler.` prefix.
  * Relative imports prohibited; wildcard imports prohibited; one import per line.
* **Shared components**: Must use existing shared utilities (e.g. `noveler.presentation.cli.shared_utilities.console`).

  * Direct instantiation of `Console`, `import logging`, or hardcoded paths are strictly forbidden.
* **Service calls**: Must go through the **Use Case layer** or **MessageBus pattern** (SPEC-901). Dependency direction must follow DDD (Domain → Application → Infrastructure).
* **MessageBus usage**: For new features, prefer MessageBus commands/events over direct UseCase calls. Use `UseCaseBusAdapter` for legacy integration.
* **Path management**: Path Service is mandatory. Any fallback triggers a CI failure under strict mode.
* **Configuration management**: Only use `get_configuration_manager()` for environment and path access. Direct calls like `os.getenv(...)` are prohibited.
* **Naming conventions**:

  * Functions/variables: `snake_case`
  * Classes: `PascalCase`
  * Constants: `SCREAMING_SNAKE_CASE`

---

## Testing & Quality

* New features must follow the sequence: **Specification → Test (`@pytest.mark.spec('SPEC-…')`) → Implementation → Refactor**.
* Every change must include at least one test and corresponding documentation update.
* **Quality checks**: `run_quality_checks` is the unified entry point.

  * Output formats: `summary` or `ndjson`
  * Weighted average scoring supported
  * `.novelerrc.yaml` `fail_on` must be respected
* **Auto-fix**: `fix_quality_issues` (default `dry_run: true`).
* **Iterative improvement**: Use `improve_quality_until` until target score (default 80) is reached.
* **Path handling**: Under strict mode, any fallback detection is a CI failure condition.

### LLM-Friendly Test Output (Contract)

### LLM-Friendly Test Output (Contract)

* Preferred runners: `scripts/run_pytest.py` / `bin/test` / `make test`.
* For minimal LLM output, use `--json-only` or `/bin/test-json` to print only the final summary JSON.
* CI default: fail-only NDJSON streaming is enabled (set `LLM_REPORT_STREAM_FAIL=0` to disable locally).
* Outputs: `reports/llm_summary.jsonl` and `reports/llm_summary.txt`; NDJSON fail stream under `reports/stream/`.
* Purpose: provide concise, machine-readable results with stable contracts.


---

## Change Policy

* CLAUDE.md may only be edited for **contract additions or modifications**.
* Background explanations or procedures must be added to referenced documents instead.
* Always prefer updating/reusing referenced documents (e.g. `docs/runbooks`, `CODEMAP.yaml`).


## レイヤリング原則（必須）
- Domainは Presentation/Infrastructure を静的importしない（importlinter 契約で検査）。
- Consoleは `noveler.domain.utils.domain_console.get_console()` を使用。
- Loggerは `ILogger/NullLogger`（または ILoggerService/NullLoggerService）を使用し、未注入時はNull既定。
- Infra機能は importlib 遅延参照または manager/proxy 経由でアクセスする。
