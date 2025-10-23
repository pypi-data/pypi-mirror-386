# Diff Gate Failure Playbook

## Symptoms
- `bin/diff-gate` fails with non-zero exit status.
- Output lists files that violate collect-only or encoding guarantees.

## Quick Fix Checklist
1. Run `/test --collect-only` to confirm pytest discovery is stable.
2. Execute `/scan-encoding --exclude docs/archive/** docs/backup/**` and resolve reported U+FFFD characters.
3. Re-run `bin/diff-gate` with the same diff range to verify the gate passes.

## Escalation
- If the gate fails due to new contract expectations, review `tests/contracts/` for schema updates.
- For CI-only failures, capture logs under `reports/gate-results.txt` and note the remediation in TODO.md.

## References
- `docs/guides/diff_gate_usage.md`
- `docs/technical/contract_testing_baseline.md`

