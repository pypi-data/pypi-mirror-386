# A24 Character Schema Migration Checklist

## Overview

This document provides a step-by-step checklist for migrating legacy character files to the A24 character schema format.

## Migration Required Changes

### 1. Schema Version
- [ ] Add `version: "0.1.0"` to `character_book`
- [ ] Add `last_updated` field with current date

### 2. Character ID and Display Name
- [ ] Rename `name` → `display_name`
- [ ] Add `character_id` (lowercase, underscore-separated)

### 3. Status Tracking
- [ ] Add `status` section:
  - `lifecycle: "active"`
  - `last_reviewed: ""`
  - `reviewer: ""`

### 4. Layer 1: Psychology Restructuring

#### Traits Split (CRITICAL)
- [ ] **Split `traits` into `traits_positive` and `traits_negative`**
  - Example: `["勇敢", "短気"]` → `traits_positive: ["勇敢"]`, `traits_negative: ["短気"]`
  - Use semantic analysis or manual review to classify

#### New Required Fields
- [ ] Add `hook_summary` (one-line character hook)
- [ ] Add `psychological_models` section:
  - `primary.framework` (e.g., "maslow_hierarchy", "attachment_theory")
  - `primary.type` (e.g., "secure", "achievement_driven")
  - `primary.rationale` (why this model fits)
  - `secondary: []`
  - `psychological_exceptions: []`
  - `summary_bullets: []`
  - `decision_flow` (4 steps: perception, evaluation, action, aftermath)
  - `conflict_arcs: { short_term: [], long_term: [] }`

#### Emotional Patterns Enhancement
- [ ] Expand `emotional_patterns`:
  - Keep `likes`, `dislikes`
  - Add `momentary_fears: []`

#### Growth Vector
- [ ] Add `growth_vector`:
  - `current_arc: ""`
  - `future_hook: ""`
  - `short_term_arc: ""`
  - `long_term_arc: ""`

### 5. Layer 2: Physical Appearance
- [ ] Move `appearance` data under `layer2_physical.appearance`
- [ ] Ensure structure: `height`, `build`, `hair`, `eyes`
- [ ] Add `distinguishing_features: []`
- [ ] Add `attire` section:
  - `typical: ""`
  - `variants: []`
- [ ] Add `symbolic_features: []` (link visual motifs to psychology)

### 6. Layer 3: Capabilities & Skills
- [ ] Keep existing structure under `layer3_capabilities_skills`
- [ ] Ensure all fields present:
  - `combat_skills: []`
  - `non_combat_skills: []`
  - `magical_abilities: []`
  - `technical_assets.tools: []`
  - `limitations: []`
- [ ] Prefer typed limitations: each item includes a `type` (e.g., `resource`, `time`, `social`) and a concrete `detail`.

### 7. Layer 4: Social Network
- [ ] Keep existing structure under `layer4_social_network`
- [ ] Add `social_position` if missing:
  - `public_image: ""`
  - `hidden_value: ""`

### 8. Layer 5: Expression & Behavior
- [ ] Move speech data under `layer5_expression_behavior.speech_profile`
- [ ] Ensure structure:
  - `baseline_tone: ""`
  - `sentence_endings: {}`
  - `personal_pronouns: {}`
  - `catchphrases: {}`
- [ ] Add `speech_profile.modes: {}` and `voice_drift_rules: []` for situation-specific variation
- [ ] Add `behavioral_patterns`:
  - `work_style: ""`
  - `coping_mechanisms: []`

### 9. Narrative Notes (NEW)
- [ ] Add `narrative_notes` section:
  - `foreshadowing_hooks: []`
  - `unresolved_questions: []`

### 10. LLM Prompt Profile (NEW)
- [ ] Add `llm_prompt_profile` section:
  - `default_scene_goal: ""`
  - `inputs_template` (7 fields: scene_role_and_goal, psych_summary, etc.)
  - `post_review_checklist` with 4 items:
    - `values_motivation_alignment`
    - `speech_rule_compliance`
    - `deliberate_voice_drift_alignment`
    - `emotional_flow_alignment`
    - `decision_flow_trace_present`

### 11. Logging Configuration
- [ ] Add `logging` section:
  - `character_log_directory: "<log_root>/<character_id>/"`
  - `guidance: "命名: <YYYYMMDD>_<scene>.md"`
  - `last_entry: ""`

### 12. Lite Profile Hint (NEW)
- [ ] Add `lite_profile_hint`:
  - `use_lite: false`
  - `minimal_fields` (4 lite copies)

### 13. Episode Snapshots
- [ ] Add `episode_snapshots: []`

## Automated vs Manual Steps

### Can Be Automated
- Schema version addition
- Field renaming (`name` → `display_name`)
- Structure reorganization (moving fields to layers)
- Empty field initialization

### Requires Manual Review
- **Traits classification** (`traits` → `traits_positive`/`traits_negative`)
- Psychological model selection and rationale
- Decision flow definition (4 steps)
- Hook summary writing
- LLM prompt profile configuration

## Migration Script Usage

```bash
# Convert a single legacy character file
python scripts/migration/convert_character_to_a24.py \
  --input legacy_character.yaml \
  --output character_book.yaml

# Dry run (preview changes without writing)
python scripts/migration/convert_character_to_a24.py \
  --input legacy_character.yaml \
  --dry-run

# Batch conversion (all files in directory)
python scripts/migration/convert_character_to_a24.py \
  --input-dir ./legacy_characters/ \
  --output-dir ./migrated_characters/
```

## Post-Migration Validation

- [ ] Run validation script: `python scripts/migration/validate_a24_schema.py`
- [ ] Check all required fields are populated (not just empty strings)
- [ ] Verify traits are correctly classified
- [ ] Review psychological model assignments
- [ ] Test with CharacterProfileAdapter (Phase 1)
- [ ] Test accessor methods (Phase 2)
- [ ] Run consistency checks (Phase 3)

## Common Migration Issues

### Issue 1: Missing Traits Classification
**Problem**: Script cannot auto-classify `traits` into positive/negative

**Solution**: Manual review required. Use semantic understanding:
- Positive: 勇敢, 誠実, 優しい, 賢い, etc.
- Negative: 短気, 傲慢, 臆病, 不誠実, etc.

### Issue 2: Empty Psychological Models
**Problem**: No guidance on selecting framework/type

**Solution**: Refer to `docs/A24_psychological_models_guide.md` (if exists) or use:
- Framework: maslow_hierarchy, attachment_theory, trait_theory, cognitive_behavioral
- Type: depends on character's core driver

### Issue 3: Decision Flow Undefined
**Problem**: Decision flow requires understanding character's decision-making style

**Solution**: Analyze character behavior in existing episodes:
- Perception: How do they notice problems? (logical, intuitive, emotional)
- Evaluation: How do they weigh options? (efficiency, relationships, principles)
- Action: How do they execute? (planned, impulsive, collaborative)
- Aftermath: How do they reflect? (analytical, emotional, dismissive)

## References

- A24 Schema Specification: `docs/A24_character_schema_phase3_integration.md`
- Adapter Implementation: `docs/A24_キャラクタースキーマ_アダプター実装完了報告.md`
- Template: `templates/character/character_book.yaml`
