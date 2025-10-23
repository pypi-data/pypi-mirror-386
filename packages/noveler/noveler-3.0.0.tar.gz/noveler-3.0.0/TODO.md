# TODO (Prompt Schema v2 rollout and tooling)

## 🎉 Recently Completed

### MCP Configuration Reliability Fix (2025-10-21)
- [x] **Environment Auto-Detection** - dist-only 本番環境対応
  - [x] `_detect_environment()` 実装
  - [x] dev/prod パス自動判定
  - [x] 13 テスト合格 ✅
- [x] **SSOT Unification** - 設定の唯一の真実源
  - [x] `ensure_mcp_server_entry()` を SSOT 関数化
  - [x] build.py と setup scripts を統一
  - [x] 11 テスト合格 ✅
- [x] **Production Reliability** - sys.executable デフォルト
  - [x] 本番環境で PATH に依存しない
  - [x] python/python3/venv パス対応
  - [x] command パラメータで明示指定対応
- [x] **Tests**: 全 24 テスト合格、100% 環境カバレッジ
- 詳細: コミット `b39aa87`, `0cec424`

### Template Variable Expansion System (2025-10-20)
- [x] **B20 Full Workflow Execution** - Phase 1-5完了
  - Phase 1: Requirements Organization ✅
  - Phase 2: CODEMAP Creation & SOLID Validation ✅
  - Phase 3: Implementation (6 classes, 758 LOC) ✅
  - Phase 4: Contract Testing (68 tests, 100% pass) ✅
  - Phase 5: Review & Output (全成果物完備) ✅
- [x] **SOLID Compliance**: 100% (5/5 principles)
- [x] **Test Coverage**: 公開インターフェース100%
- [x] **Decision Log**: 9決定記録（DEC-001～DEC-009）
- [x] **Deliverables**: 6必須成果物 + 1オプション成果物完備
- 詳細: [b20-outputs/12_final_summary.md](b20-outputs/12_final_summary.md)

---

## 🔄 Active Tasks

- CI: Integrate automatic validation on every PR
  - [ ] Implement `scripts/validate_artifacts.py` to evaluate acceptance_criteria.*
  - [ ] Exit non-zero on failure; emit JSON + Markdown summary to `reports/`.
- Markdown steps (12–15): add minimal meta channel for by_task
  - Decide format: front‑matter (`--- yaml ---`) or HTML comment meta (`<!-- yaml: {...} -->`).
  - Extend validator to parse meta from Markdown when present.
  - Optionally add `by_task` mappings for 12–15 once meta format is finalized.
- CLI: use v2 structured sections for prompt synthesis
  - Prefer `inputs/constraints/tasks/artifacts/acceptance_criteria` over long main_instruction.
  - Enforce "YAML only in fenced code" at output; add retry on validation fail.

## Medium Priority

- **MCP Import Refactor & Retire Namespace Shim** (future phase)
  - Context: `./mcp_servers/__init__.py` is a namespace shim for `from mcp_servers.noveler.*` imports.
    Currently required because `src/mcp_servers/` contains dozens of modules using absolute imports.
    See [mcp_servers/__init__.py:1](mcp_servers/__init__.py) and [src/mcp_servers/noveler/core/async_subprocess_adapter.py:9](src/mcp_servers/noveler/core/async_subprocess_adapter.py).
  - **Keep shim for now** (still anchors import resolution; removal would break all imports until sweeping refactor).
  - **Future steps** (when ready to retire):
    1. [ ] Decide on new import style:
       - Option A: Relative imports (`from .core.async_subprocess_adapter import ...`)
       - Option B: src-explicit layout (`from src.mcp_servers.noveler.core...`)
    2. [ ] Update all `from mcp_servers.*` imports in `src/mcp_servers/**/*.py` and `scripts/`.
    3. [ ] Ensure packaging/test harness exports same dotted path (install package or set PYTHONPATH deterministically).
    4. [ ] Remove `./mcp_servers/__init__.py`.
    5. [ ] Run `/test` to confirm parity.
  - **Tracker**: Track in CI/refactor backlog for next major release.

- STEP1 optional explicit `handover_to_next` key
  - Add to `story_structure` example + `by_task` mapping if we want stricter checks.
- Examples parity
  - Ensure `artifacts.example` contains sample fields referenced by `by_task` (spot check each step).
- Docs
  - templates/README.md: add brief on `id`/`by_task` and validator workflow.
  - A38 docs: note variable convention `{project_root}` (from `{PROJECT_ROOT}`) and code‑fence YAML guidance.
- Arrays addressing in validator (v2.1)
  - Add dotted path with wildcard (e.g., `sections[*].hook`) support.
  - Add numeric aggregations (min/max/avg) for metrics on arrays.

## Nice to Have
- Generator retry policy
  - On `by_task` failures, auto‑compose a delta prompt listing failed IDs and expected rules.
- Rich metrics
  - STEP10 non‑visual sense ratio estimator for raw text (heuristic).
  - STEP15 dialogue ratio estimator on Markdown.
- Telemetry
  - Summarize pass/fail rates per ID across episodes to prioritize template improvements.

- Progressive Check refactor (LangGraph alignment)
  - [ ] Update docs/README to remove `progressive_check.start_session` references and document `get_tasks` flow.
  - [ ] Refactor ProgressiveCheckManager to expose explicit session init helper and include `session_id` in `get_check_tasks` response; verify client compatibility.
  - [ ] Add unit tests ensuring `.noveler/checks/<session_id>/` files and LangGraph workflow logs are created using temp dirs.
  - [ ] Improve CLI error for unsupported progressive_check commands to guide users toward `get_tasks`.
  - [ ] Document LangGraph requirement and workflow logging in guides/CHANGELOG.
  - [ ] Integrate new tests into CI to catch logging regressions.

## Operational Checklist

### Template & Validation System
- [ ] Implement validator script (by_task + checklist + metrics)
- [ ] Wire CI job (`make validate-templates` + `make validate-artifacts`)
- [ ] Decide Markdown meta format for 12–15 and update templates
- [ ] Add by_task mappings for 12–15 after meta support
- [ ] Update templates/README.md with v2 + validator docs
- [ ] (Optional) Add `handover_to_next` key to STEP1 `story_structure`
- [ ] Update A38 excerpts to `{project_root}` examples where applicable
