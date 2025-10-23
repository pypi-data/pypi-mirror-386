# A24 Character Template Fit & Gap Analysis

## Current Artifacts

### Initialization Output (`src/noveler/domain/initialization/services.py:338-354`)
- Canonical `character_book` root emitted from `templates/character/character_book.yaml`（A24スキーマ準拠）。
- 層別心理・身体・社会構造、LLMプロンプトプロファイル、ログメタデータ、Lite向けヒントまで含む完全版テンプレート。

### Legacy Prompt Template (`docs/archive/A24_legacy/A24_話別プロット作成ガイド.yaml`)
- Stage3 output spec: `characters.main_character/supporting_character` with `starting_state/arc/ending_state/key_moments/dialogue_highlights`.
- Focused on per-episode arcs rather than persistent 5-layer profile; no explicit psychological model fields.

### Real Project Sample (`30_設定集/キャラクター.yaml` in 10_Fランク...)
- Uses five layers (basic profile, physical, psychology, social, behavior) with rich sub-fields.
- Integrates speech dictionaries, ability breakdowns, and lore-specific metadata.
- Still lacks structured psychological model summary (MBTI etc.) and post-review markers defined in updated guide.

## New Guide Requirements (docs/A24_キャラクター設計ガイド.md)
- Layer 1 memo must include `主要モデル/補助モデル/例外ポイント/要約手順` plus example formatting (lines 33-98).
- Step2 mandates storing decision flow and allows lite template for minor characters (lines 81-98).
- Step3 introduces LLM prompt inputs with `出力形式/応答スタイル` and post-generation review checklist (lines 99-131).
- Efficiency section defines logging path `records/characters/<name>/<YYYYMMDD>_<scene>.md` with markdown template (lines 233-252).

## Fit vs Gap

| Theme | Current State | Gap |
| --- | --- | --- |
| Base Structure | Sample YAML already in 5-layer layout | Canonical initialization template (A24スキーマ) now in place; monitor downstream adoption |
| Psych Models | Not present in any artifact | Add structured fields under Layer1 with priority rules and summary slots |
| Decision Flow & Lite Template | Sample lacks explicit decision-flow bullet, lite template absent | Introduce dedicated sub-sections for `decision_flow` and `lite_profile` markers |
| LLM Prompt Inputs | No persistent storage | Add `llm_prompt_profile` block capturing the new template inputs |
| Post Review Checklist | Not tracked | Include `post_review`/`status` section referencing checklist outcomes |
| Logging Guidance | Not encoded in YAML | Add `logging` metadata and align with `records/characters/...` naming |
| Episode-Specific Fields | Legacy Stage3 covers arc/moments | Determine whether to embed `episode_snapshots[]` or reference external per-episode logs |

## Decision Points
1. Unify initialization + prompt workflow around single YAML schema (5-layer + new sections).
2. Provide optional lite-profile rendering for minor characters, referencing `lite_template` guidance.
3. Decide placement of episode-level arc data: either embed `episode_snapshots[]` or document pointer to separate prompt outputs.
