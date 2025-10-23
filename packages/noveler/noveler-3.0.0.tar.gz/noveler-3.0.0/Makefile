export MCP_LIGHTWEIGHT_DEFAULT ?= 1

.PHONY: specs-sync specs-frontmatter specs-lint specs-index specs-all

specs-sync:
	python3 specs/_scripts/specs_sync.py --apply

specs-frontmatter:
	python3 specs/_scripts/specs_front_matter.py --apply

specs-lint:
	python3 specs/_scripts/specs_lint.py --max-age-days=120

specs-index:
	python3 specs/_scripts/specs_build_search_index.py

specs-all: specs-sync specs-frontmatter specs-lint specs-index

.PHONY: tidy-root
tidy-root:
	@mkdir -p workspace
	@[ -d logs ] && mv logs workspace/ || true
	@[ -d temp ] && mv temp workspace/ || true
	@[ -d outputs ] && mv outputs workspace/ || true
	@[ -d テストプロジェクト ] && mv テストプロジェクト workspace/ || true
	@echo "[tidy-root] Moved: logs/ temp/ outputs/ テストプロジェクト/ -> workspace/"

# ------------------------------
# Local CI helpers
# ------------------------------
.PHONY: build test test-fast test-slow test-suite lint pre-commit impact-audit ci-mcp-dry-run ci-smoke ci help validate-templates

help:
	@echo "Available targets:"
	@echo "  make build             # Build distribution (scripts/build.py)"
	@echo "  make setup-mcp         # Update MCP configs (codex/.mcp/Claude) with backups"
	@echo "  make lint-imports      # Run importlinter contracts if available"
	@echo "  make lint              # Run linters (ruff, mypy if available)"
	@echo "  make test              # Run full pytest suite"
	@echo "  make validate-templates # Schema v2 checks for quality templates"
	@echo "  make test-fast         # Run pytest without slow-marked cases"
	@echo "  make test-slow         # Run only slow-marked tests"
	@echo "  make test-suite        # Alias for full suite (pytest)"
	@echo "  make test-last         # Re-run last failed tests first (-x)"
	@echo "  make test-changed      # Run tests changed in git (fallback to last-failed)"
	@echo "  make pre-commit        # Run pre-commit on all files"
	@echo "  make impact-audit      # Generate B20影響調査レポート (impact_audit.py)"
	@echo "  make ci-mcp-dry-run    # Dry-run validate MCP config updater"
	@echo "  make ci-smoke          # Local CLI smoke runs (MCP tools)"
	@echo "  make ci                # Run lint + test + dry-run + smoke"

build:
	python3 scripts/build.py

setup-mcp:
	./bin/setup_mcp_configs

lint:
	@command -v ruff >/dev/null 2>&1 && ruff check || echo "[skip] ruff not installed"
	@command -v mypy >/dev/null 2>&1 && mypy || echo "[skip] mypy not installed"

# ------------------------------
# Pytest runners (LLM-aware)
# ------------------------------
# Usage examples:
#   make test                           # full suite, quiet
#   make test VV=1                      # verbose (-v)
#   make test FILE=tests/test_api.py    # single file/node
#   make test FILE=tests/t.py::TestX::test_y
#   make test K='user and not slow'     # -k expression
#   make test M='unit'                  # -m marker expression

# User-specified args
FILE ?=
K    ?=
M    ?=
VV   ?=

# Map verbosity
ifeq ($(VV),1)
  PYTEST_VV=-v
else ifeq ($(VV),2)
  PYTEST_VV=-vv
else ifeq ($(VV),3)
  PYTEST_VV=-vvv
else
  PYTEST_VV=
endif

ifneq ($(strip $(K)),)
  PYTEST_K = -k '$(K)'
endif
ifneq ($(strip $(M)),)
  PYTEST_M = -m '$(M)'
endif

# Default to quiet unless user requested verbosity
ifeq ($(strip $(PYTEST_VV)),)
  PYTEST_Q=-q
endif

# LLM reporting defaults (opt-out by LLM_REPORT=0)
export LLM_REPORT      ?= 1
export LLM_REPORT_DIR  ?= reports
export LLM_REPORT_FORMAT ?= jsonl,txt

test:
	@mkdir -p $(LLM_REPORT_DIR)
	python3 scripts/ci/ensure_dist_wrapper.py && \
	python3 scripts/run_pytest.py $(PYTEST_Q) $(PYTEST_VV) $(PYTEST_M) $(PYTEST_K) $(FILE)

test-fast:
	@mkdir -p $(LLM_REPORT_DIR)
	python3 scripts/run_pytest.py -m "not slow" --durations=10 -q

test-slow:
	@mkdir -p $(LLM_REPORT_DIR)
	python3 scripts/run_pytest.py -m slow --maxfail=1 --durations=10 -q

test-suite:
	@mkdir -p $(LLM_REPORT_DIR)
	python3 scripts/ci/ensure_dist_wrapper.py && \
	python3 scripts/run_pytest.py -q

.PHONY: test-last test-changed

# Re-run last failed tests (fast feedback). Falls back gracefully if no cache.
test-last:
	@mkdir -p $(LLM_REPORT_DIR)
	python3 scripts/ci/ensure_dist_wrapper.py && \
	python3 scripts/run_pytest.py -q --last-failed -x $(PYTEST_VV)

# Run tests changed in git. Accepts optional RANGE (e.g., RANGE=origin/main...HEAD).
# If no changed tests are found, falls back to last-failed.
test-changed:
	@mkdir -p $(LLM_REPORT_DIR)
	python3 scripts/run_pytest.py $(PYTEST_Q) $(PYTEST_VV) --changed --range '$(RANGE)'
pre-commit:
	@command -v pre-commit >/dev/null 2>&1 && pre-commit run --all-files || echo "[skip] pre-commit not installed"

impact-audit:
	@mkdir -p temp/ci
	python3 scripts/tools/impact_audit.py --output temp/ci/impact-summary.md

ci-mcp-dry-run:
	@mkdir -p temp/ci
	@echo "[codex]"
	python3 scripts/setup/update_mcp_configs.py --codex --dry-run | tee temp/ci/codex_mcp_dryrun.txt
	@echo "[project .mcp]"
	python3 scripts/setup/update_mcp_configs.py --project --dry-run | tee temp/ci/project_mcp_dryrun.txt
	@echo "[claude]"
	python3 scripts/setup/update_mcp_configs.py --claude --dry-run | tee temp/ci/claude_mcp_dryrun.txt
	@grep -q '"mcpServers"' temp/ci/codex_mcp_dryrun.txt && echo "[ok] codex.mcp.json dry-run" || echo "[warn] codex.mcp.json no mcpServers"
	@grep -q '"noveler"' temp/ci/codex_mcp_dryrun.txt && echo "[ok] codex.mcp.json has noveler" || echo "[warn] codex.mcp.json missing noveler"
	@grep -q '"mcpServers"' temp/ci/project_mcp_dryrun.txt && echo "[ok] .mcp/config.json dry-run" || echo "[warn] .mcp/config.json no mcpServers"
	@grep -q '"noveler"' temp/ci/project_mcp_dryrun.txt && echo "[ok] .mcp/config.json has noveler" || echo "[warn] .mcp/config.json missing noveler"
	@grep -q '"mcpServers"' temp/ci/claude_mcp_dryrun.txt && echo "[ok] claude config dry-run" || echo "[warn] claude config no mcpServers"
	@grep -q '"noveler"' temp/ci/claude_mcp_dryrun.txt && echo "[ok] claude config has noveler" || echo "[warn] claude config missing noveler"

.PHONY: validate-templates
validate-templates:
	LLM_FAST_CLEANUP=1 LLM_REPORT=0 python3 scripts/run_pytest.py -q tests/unit/templates/test_quality_check_schema_v2.py


ci-smoke:
	@mkdir -p temp/ci
	@echo "[smoke] run_quality_checks"
	MCP_STDIO_SAFE=1 NOVEL_PRODUCTION_MODE=1 python3 bin/noveler mcp call run_quality_checks '{"episode_number": 1, "file_path": "README.md", "additional_params": {"format":"summary"}}' | tee temp/ci/run_quality_checks_smoke.json || true
	@echo "[smoke] enhanced_get_writing_tasks"
	MCP_STDIO_SAFE=1 NOVEL_PRODUCTION_MODE=1 python3 bin/noveler mcp call enhanced_get_writing_tasks '{"episode_number": 1}' | tee temp/ci/enhanced_tasks_smoke.json || true
	@echo "[smoke] enhanced_execute_writing_step"
	MCP_STDIO_SAFE=1 NOVEL_PRODUCTION_MODE=1 python3 bin/noveler mcp call enhanced_execute_writing_step '{"episode_number": 1, "step_id": 1, "dry_run": true}' | tee temp/ci/enhanced_step_smoke.json || true
	@echo "[smoke] enhanced_resume_from_partial_failure"
	MCP_STDIO_SAFE=1 NOVEL_PRODUCTION_MODE=1 python3 bin/noveler mcp call enhanced_resume_from_partial_failure '{"episode_number": 1, "recovery_point": 1}' | tee temp/ci/enhanced_resume_smoke.json || true
	@echo "[smoke] polish_manuscript"
	MCP_STDIO_SAFE=1 NOVEL_PRODUCTION_MODE=1 python3 bin/noveler mcp call polish_manuscript '{"episode_number": 1, "file_path": "temp/test_data/40_原稿/第001話_スモークテスト.md", "stages": ["stage2"], "dry_run": true}' | tee temp/ci/polish_manuscript_smoke.json || true
	@echo "[smoke] polish_manuscript_apply"
	MCP_STDIO_SAFE=1 NOVEL_PRODUCTION_MODE=1 python3 bin/noveler mcp call polish_manuscript_apply '{"episode_number": 1, "file_path": "temp/test_data/40_原稿/第001話_スモークテスト.md", "stages": ["stage2", "stage3"], "dry_run": true}' | tee temp/ci/polish_apply_smoke.json || true
	@echo "[smoke] restore_manuscript_from_artifact"
	MCP_STDIO_SAFE=1 NOVEL_PRODUCTION_MODE=1 python3 bin/noveler mcp call restore_manuscript_from_artifact '{"episode_number": 1, "file_path": "temp/test_data/40_原稿/第001話_スモークテスト.md", "artifact_id": "dummy", "dry_run": true}' | tee temp/ci/restore_smoke.json || true
	@echo "[smoke] write"
	MCP_STDIO_SAFE=1 NOVEL_PRODUCTION_MODE=1 python3 bin/noveler mcp call write '{"relative_path": "smoke_write.md", "content": "# スモークテスト\n", "project_root": "temp/ci"}' | tee temp/ci/write_smoke.json || true
	@echo "[smoke] list_artifacts"
	MCP_STDIO_SAFE=1 NOVEL_PRODUCTION_MODE=1 python3 bin/noveler mcp call list_artifacts '{"episode_number": 1}' | tee temp/ci/list_artifacts_smoke.json || true

ci: lint validate-templates test impact-audit ci-mcp-dry-run ci-smoke
	@echo "✅ Local CI completed"

.PHONY: build-dist-wrapper
build-dist-wrapper:
	python3 scripts/ci/ensure_dist_wrapper.py

.PHONY: lint-imports
lint-imports:
	@{ command -v lint-imports >/dev/null 2>&1 && lint-imports; } || \
	python3 -c "import importlib.util as u, sys; print('[lint-imports] not available: skipping') if u.find_spec('importlinter') is None else print('[lint-imports] importlinter installed but CLI not found: install console script to run contracts'); sys.exit(0)"

.PHONY: git-health
git-health:
	python3 scripts/tools/git_repo_health.py --json

.PHONY: test-json
test-json:
	@mkdir -p $(LLM_REPORT_DIR)
	python3 scripts/run_pytest.py --json-only -q $(PYTEST_M) $(PYTEST_K) $(FILE)
