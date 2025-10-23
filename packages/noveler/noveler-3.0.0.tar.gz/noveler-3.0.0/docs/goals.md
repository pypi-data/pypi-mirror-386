# File: docs/goals.md
# Purpose: Project-level goal template for writing and quality gates.
# Context: Authors define per-work goals before drafting. The values here are referenced by check runners and reports.

## Goal Template

- Work Title: <title>
- Objective: <e.g., Complete rough draft of Chapter N>
- Deadline: <YYYY-MM-DD>
- Quality Gates:
  - Gate A (Formatting): headers/style checks pass
  - Gate B (Automated): rhythm ≥ 80, readability ≥ 80, grammar ≥ 90 — enforced by `bin/check-core` / `run_quality_checks_ndjson.py` (fails fast when thresholds are missed)
  - Gate C (Editorial): Editorial 12-step checklist cleared or exceptions documented
- Notes: <risks, assumptions>

## Example (fill-in)

- Work Title: Example Novel
- Objective: Chapter 3 rough draft lock
- Deadline: 2025-10-15
- Quality Gates:
  - Gate A: pass
  - Gate B: rhythm 82 / readability 84 / grammar 91
  - Gate C: Editorial 12-step exceptions: L12-05 (redundancy) deferred — ticket DOC-123
- Notes: pacing risk in mid-section
