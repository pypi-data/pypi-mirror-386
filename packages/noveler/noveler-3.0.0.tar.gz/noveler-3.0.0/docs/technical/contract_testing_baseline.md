# Contract Testing Baseline

## Overview
- Establishes baseline contract coverage for `SessionGenerator` and file-based state repositories.
- Guards destructive API changes by asserting required keys and types in generated session payloads.
- Extends repository contracts to ensure persistence schema consistency during refactors.

## Tests
- `tests/contracts/test_session_generator_contract.py`
- `tests/contracts/test_state_repository_contract.py`

## Usage
1. Run `bin/diff-gate` or `scripts/ci/diff_gate.sh` before committing cross-layer changes.
2. Contract tests run automatically with `/test --collect-only` because they live under `tests/contracts/`.
3. When adding new components, copy the helper patterns to assert schema invariants early.

## Maintenance
- Update `REQUIRED_SESSION_KEYS` when the session schema evolves intentionally.
- Re-run `/scan-encoding` after editing contract fixtures to keep UTF-8 gate satisfied.
- Document new contract suites here to keep the baseline inventory in sync.
