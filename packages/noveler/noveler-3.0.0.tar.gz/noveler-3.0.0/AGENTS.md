# AGENTS.md

**Motto:** “Small, clear, safe steps — always grounded in real docs.”

---

## Principles

* Keep every change minimal, reversible, and easy to roll back.
* Favour clarity over cleverness; simplicity over complexity.
* Avoid introducing new dependencies unless absolutely necessary; prune unused ones whenever possible.

---

## Knowledge & Libraries

* When in doubt, pause and ask for clarification before proceeding.

---

## Workflow

### Slash Commands (LLM helpers)

The following chat slash commands are mapped to project scripts. When a user types these in Codex CLI or Claude Code, resolve them to shell execution of the corresponding script (arguments are forwarded):

- `/test …` → run `bin/test …` (delegates to `scripts/run_pytest.py`)
- `/test-failed …` → run `bin/test-failed …`
- `/test-changed [--range RANGE] …` → run `bin/test-changed …` (uses git diff; falls back to last-failed)

Environment is normalized by the runner; prefer these over raw `python -m pytest` to keep outputs consistent.

* **Plan:** Present a concise plan before any non-trivial work and keep it updated until completion.
* **Read:** Identify all relevant files and read them completely before editing.
* **Verify:** Check assumptions against the docs; after modifications, re-read the affected code to confirm syntax and formatting.
* **Implement:** Keep scope tight, aiming for modular, single-purpose changes.
* **Test & Docs:** For each change, add at least one test and update the relevant documentation so behaviour stays aligned with business logic.
* **Reflect:** Address root causes and consider adjacent risks to prevent regressions.
* ログレベルと出力方針の詳細は `docs/guides/logging_guidelines.md` を参照。

---

## Code Style & Limits

* Target ≤ 300 lines per file; keep modules focused on a single responsibility.
* Comments: open each file with a short header (where/what/why). Subsequent comments should explain **intent (Why)**, **purpose (What)**, or **higher-level design decisions**—avoid restating obvious code.
* Commenting habit: capture rationale, assumptions, and trade-offs so future readers understand the reasoning.
* Docstrings: write all module/class/function docstrings in English, using sections such as Args / Returns / Raises when they improve clarity.

### Comment & Docstring Standards

* Every Python module must open with an English header comment that captures the file context. Use the following template and adjust the wording as needed:

```
# File: <relative/path.py>
# Purpose: <summarise the module's responsibility and why it exists>
# Context: <note key dependencies, domain constraints, or consumers>
```

* Module, class, and function docstrings must provide enough detail to generate a specification. Each docstring should clearly cover:
  * Purpose: what the callable or object is responsible for.
  * Inputs: parameters and expected types (document under `Args:` when helpful).
  * Outputs: return values and their meaning (document under `Returns:` when helpful).
  * Preconditions and assumptions that must hold before execution.
  * Side effects or external interactions (I/O, state changes, emitted events).
  * Exceptions raised intentionally (document under `Raises:` when helpful).

* Keep comments concise and factual; favour intent and decision rationale over restating code.
* Before committing, verify compliance by running `python scripts/comment_header_audit.py` and addressing any reported files.
* Configuration: centralise tunables in `config.py`; avoid hard-coded magic numbers in code and tests. Pull defaults from config when wiring dependencies.
* Simplicity: implement exactly what is requested—no unsolicited features.

---

## Collaboration & Accountability

* Escalate immediately when requirements are ambiguous, security-sensitive, or when UX/API contracts would change.
* Be transparent about confidence: if confidence falls below 80%, state it and request help. Honesty scores 0 points; incorrect changes cost –4; correct outcomes score +1.
* Optimise for correctness over speed—preventing a bad change is worth more than shipping quickly.

---

## Quick Checklist

Plan → Read → Verify → Implement → Test & Docs → Reflect

---

## LLM-Friendly Tests (pytest)

- 推奨: `make test` を使用すると、LLM向け要約が常に生成されます。
- レポート出力: `reports/llm_summary.{jsonl,txt}`。STDOUTには `LLM:BEGIN ... LLM:END` で囲まれた要約も出力。

Examples:
- フル実行（静かめ）: `make test`
- 詳細表示: `make test VV=1`
- 個別ノード: `make test FILE=tests/test_api.py::TestUser::test_create`
- `-k`式: `make test K='user and not slow'`
- マーカー: `make test M='unit'`
- 直pytestでも同等出力: `pytest -q --llm-report` または `LLM_REPORT=1 pytest -q`
- 直近失敗の再実行: `make test-last`
- 変更分のテスト（git差分）: `make test-changed` または `make test-changed RANGE=origin/main...HEAD`

Notes:
- 出力ディレクトリは `LLM_REPORT_DIR=out` で変更可能（make/pytestどちらでも）。
- 出力フォーマットは既定 `jsonl,txt`。`LLM_REPORT_FORMAT=txt` などで変更可能。
