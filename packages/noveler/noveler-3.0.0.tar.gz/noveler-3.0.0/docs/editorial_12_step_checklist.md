# File: docs/editorial_12_step_checklist.md
# Purpose: Define the editorial 12-step manual review suite (IDs L12-01〜12) with fixed acceptance criteria.
# Context: Serves as Tier-2 human-in-the-loop checks layered on top of automated Tier-0/1 quality tools (rhythm/readability/grammar/style). The items here are non-destructive and focus on narrative intent and structure.

## Editorial 12-Step Checklist

Formerly called the "L12 suite"; the identifier prefix (L12-01〜12) remains for continuity.

Each item yields findings as notes/suggestions; no auto-fix. Use alongside automated reports. IDs are stable.

- L12-01 — Point of View Consistency
  - Goal: Narrative POV and tense are consistent within scenes.
  - Evidence: Passages where camera/voice drifts unintentionally.
  - Output: Locations + short rationale + suggested rewrite focus.

- L12-02 — Scene GCD (Goal–Conflict–Decision)
  - Goal: Each scene has a clear purpose, active conflict, and outcome.
  - Evidence: Scenes that stall or resolve off-page.
  - Output: Scene list with missing G/C/D tags.

- L12-03 — Character Voice Separation
  - Goal: Distinct speech/thought patterns per character.
  - Evidence: Interchangeable lines; tonal uniformity.
  - Output: Speaker pairs that blur; exemplar lines.

- L12-04 — Foreshadowing & Payoff
  - Goal: Teased elements resurface; setups track to payoffs.
  - Evidence: Chekhov’s guns un-fired; payoffs without setup.
  - Output: Setup→Payoff matrix with gaps.

- L12-05 — Redundancy & Over-Explanation
  - Goal: Remove repetitive beats; trust the reader.
  - Evidence: Repeated exposition, echoed metaphors.
  - Output: Duplicate clusters with keep/drop recommendation.

- L12-06 — Information Flow & Clarity
  - Goal: Reader always knows who/where/why.
  - Evidence: Ambiguous referents, broken blocking.
  - Output: Confusion hotspots and clarifying cues.

- L12-07 — Pacing & Scene Rhythm
  - Goal: Variation of sentence/scene length matches intent.
  - Evidence: Monotone pacing, abrupt transitions.
  - Output: Pacing notes per sequence; merge/split suggestions.

- L12-08 — Emotional Arc Coherence
  - Goal: Beats escalate plausibly toward turn points.
  - Evidence: Mood whiplash without cause.
  - Output: Beat list with cause→effect links.

- L12-09 — Worldbuilding Continuity
  - Goal: Rules, names, and facts remain stable.
  - Evidence: Canon mismatches, timeline slips.
  - Output: Continuity ledger entries to reconcile.

- L12-10 — Show/Tell Balance
  - Goal: Use telling strategically; show decisive moments.
  - Evidence: Summary where dramatization is needed.
  - Output: Candidate moments to dramatize/condense.

- L12-11 — Stakes & Motivation Visibility
  - Goal: What can be lost, and why it matters, is clear.
  - Evidence: Tasks without consequence; fuzzy motives.
  - Output: Stakes ladder per protagonist thread.

- L12-12 — Line-Level Polish Focus Map
  - Goal: Identify paragraphs that most benefit from polish.
  - Evidence: High-friction sentences (diction, imagery, logic).
  - Output: Top N hotspots with quick wins.

## Reporting Schema (manual)

Use the following fields when compiling notes into reports or tickets:

- id, title, severity (advisory/major/critical), message, location, evidence, suggestion

## Usage

- Run automated core checks first (bin/check-core), then open this checklist for manual review.
- Optionally generate a templated editorial 12-step checklist via `bin/check-editorial-checklist`.
- After annotating statuses, run `bin/check-editorial-status --file reports/editorial_checklist.md` to summarize Gate C results (JSON/text, configurable via `--format`).
