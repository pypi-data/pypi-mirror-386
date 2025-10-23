# Contract Test Rollout Plan

## Objective
Ensure contract coverage is applied consistently as the Progressive Manager refactor proceeds through Phase C.

## Scope
- Session-oriented services (SessionGenerator, SessionCoordinator).
- State persistence implementations (`IStateRepository`, `FileStateRepository`).
- Additional repositories touched by Phase C split work.

## Rollout Steps
1. Add or update contract suites in `tests/contracts/` before touching shared APIs.
2. Verify `bin/diff-gate origin/main...HEAD` passes to catch schema regressions on staged diffs.
3. Record any intentional schema drift in `docs/technical/contract_testing_baseline.md`.
4. Notify downstream teams via `reports/llm_summary.txt` when contract gates change.

## Tracking
- Use TODO.md follow-up section to mark completed contract wiring tasks.
- Keep `reports/encoding-scan.summary.md` filtered count at zero when contracts add new fixtures.

