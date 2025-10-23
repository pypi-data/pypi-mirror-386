# Phase 2.3 Design Notes: Repository Strict Mode Rollout

**Update Date**: 2025-10-11  
**Owner**: Codex (Phase 2.3 implementation support)

---

## Goals

1. Eliminate implicit repository fallbacks so that storage locations and persisted data remain explicit.
2. Extend strict mode controls to the repository layer by wiring `StrictModeConfig.repository_service`.
3. Provide actionable telemetry (warnings, structured exceptions) to support Phase 3’s full ERROR rollout.

---

## Scope Covered in This Iteration

- `StrictModeConfig` now recognises `NOVELER_STRICT_REPOSITORY`, exposing helpers:
  - `is_repository_strict()`
  - `should_warn_on_repository_fallback()`
- Domain exceptions:
  - `RepositoryFallbackError` when a fallback path would be taken under strict mode.
  - `RepositoryDataError` for malformed JSON/YAML payloads.
- File-based adapters:
  - `file_episode_repository` – explicit `base_dir` requirement, strict-aware logging.
  - `file_outbox_repository` – explicit `base_dir`, validation for required fields, typed fallbacks for WARNING mode.
  - `yaml_project_info_repository` – strict-aware dynamic mapping resolution.
- CLI / MCP wiring updated to pass concrete directories.
- Added unit coverage for strict vs. warning behaviour (`tests/unit/infrastructure/adapters/test_repository_strict_mode.py`).

---

## Outstanding Items (T8)

1. Compile `docs/migration/phase_2.3_completion_report.md` with before/after metrics.
2. Confirm TODO.md status after documentation is finalised.
3. Smoke-run CLI/MCP flows with `NOVELER_STRICT_REPOSITORY=warning` to gather baseline logs.

---

## Risk & Mitigation Summary

| Risk | Mitigation |
|------|------------|
| Legacy tooling instantiates repositories without `base_dir`. | Callers updated; add lint check in Phase 3 to flag new violations. |
| Pre-existing JSON payloads missing optional fields. | WARNING mode logs with fallback; strict mode fails fast with `RepositoryDataError`. |
| Operator awareness of new env var. | `.env.example`, `CLAUDE.md`, and TODO entries updated; add release note in completion report. |

---

## Next Steps

1. Finalise completion report (T8).
2. Observe WARNING-mode logs for one sprint; capture anomalies for cleanup.
3. Prepare CI default switch to `NOVELER_STRICT_REPOSITORY=error` once logs are clean.

