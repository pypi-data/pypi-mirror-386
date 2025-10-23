# A24 Character Schema Phase 3 Integration Guide

**Date**: 2025-10-03
**Status**: Complete
**Phase**: 3 (Existing Feature Integration)

---

## Overview

Phase 3 integrates A24 new character schema into existing features:
- **Character Consistency Service**: Enhanced with decision flow and psychological model checks
- **Enhanced Prompt Generator**: Leverages LLM prompt profile for specialized prompts

---

## Enhanced Character Consistency Service

### File
[src/noveler/domain/services/character_consistency_service.py](src/noveler/domain/services/character_consistency_service.py)

### New Checks

#### 1. Decision Flow Consistency (`_check_decision_flow`)

Validates character decision-making patterns against `decision_flow` schema:

```python
decision_flow = character.get_decision_flow()
# {
#   "decision_step_perception": "Log analysis for situational awareness",
#   "decision_step_evaluation": "Score by values/efficiency criteria",
#   "decision_step_action": "Execute with minimum effort",
#   "decision_step_emotional_aftermath": "Cover with sarcasm/resignation"
# }
```

**Violation Examples**:
- Analytical character uses intuitive markers (e.g., "by gut feeling")
- Efficiency-focused character makes emotion-based evaluations

#### 2. Psychological Model Consistency (`_check_psychological_model`)

Validates behavior against `psychological_models.summary_bullets`:

```python
psych_summary = character.get_psychological_summary()
# ["Intuition → Values → Team Check → Action → Sarcasm"]
```

**Violation Examples**:
- Team-oriented character makes solo decisions without team consultation
- Character acts without following expected psychological pattern

### Integration Strategy

**Option B Implementation**: Existing methods enhanced with new schema detection

```python
if hasattr(character, 'has_new_schema_data') and character.has_new_schema_data():
    violations.extend(self._check_decision_flow(line, line_num, character, context))
    violations.extend(self._check_psychological_model(line, line_num, character, context))
```

**Benefits**:
- Backward compatible with legacy characters
- Automatic enhancement when new schema available
- No changes to existing API

---

## Enhanced Prompt Generator

### File
[src/noveler/domain/services/enhanced_prompt_generator.py](src/noveler/domain/services/enhanced_prompt_generator.py)

### New Features

#### 1. Enhanced Analysis Points (`_build_enhanced_analysis_points`)

Extracts specialized analysis points from new schema:

```python
# Decision Flow Analysis
if decision_flow:
    points.append(f"5. {profile.name}'s decision process: {perception}")

# Psychological Model Analysis
if psych_summary:
    points.append(f"6. {profile.name}'s psychological consistency: {psych_summary[0]}")

# LLM-Specific Checks
if llm_profile:
    checklist = llm_profile.get("post_review_checklist", [])
    points.append(f"7. {profile.name}'s special checks: {', '.join(checklist[:2])}")
```

#### 2. Character Consistency Prompt Enhancement

New schema characters receive specialized prompts:

**Standard Prompt** (legacy):
```
1. Speech style consistency
2. Behavioral pattern alignment
3. Personality expression consistency
4. Character relationship naturalness
```

**Enhanced Prompt** (new schema):
```
1-4. (Same as standard)
5. Yamada Taro's decision process: Log analysis → Value scoring → Min effort execution
6. Yamada Taro's psychological consistency: Intuition → Values → Team → Action → Sarcasm
7. Yamada Taro's special checks: Logical thinking consistency, Sarcasm appropriateness
```

---

## Test Coverage

### File
[tests/unit/domain/services/test_character_consistency_service_new_schema.py](tests/unit/domain/services/test_character_consistency_service_new_schema.py)

**12 tests** covering:
- Decision flow violation detection (2 tests)
- Psychological model violation detection (2 tests)
- Legacy character compatibility (2 tests)
- Mixed new/legacy character handling (1 test)
- Accessor method validation (5 tests)

**Results**: ✅ 12 passed in 0.19s

---

## Usage Examples

### Example 1: Consistency Check with New Schema

```python
# Character with A24 new schema
profile = CharacterProfile(
    name="Yamada",
    attributes={
        "_raw_layers": {
            "layer1_psychology": {
                "psychological_models": {
                    "decision_flow": {
                        "decision_step_perception": "Log analysis",
                        "decision_step_evaluation": "Efficiency scoring"
                    }
                }
            }
        }
    }
)

# Episode content with violation
episode = Episode(
    number=EpisodeNumber(1),
    content="Yamada made an intuitive decision."  # Violates analytical pattern
)

# Run consistency check
service = CharacterConsistencyService(repo)
violations = service.analyze_consistency(episode, [profile])

# Result: decision_flow_perception violation detected
```

### Example 2: Enhanced Prompt Generation

```python
context = PromptContext(
    project_name="MyNovel",
    episode_number=1,
    episode_content="...",
    character_profiles=[new_schema_profile],  # Has LLM prompt profile
    target_category=A31EvaluationCategory.CHARACTER_CONSISTENCY
)

generator = EnhancedPromptGenerator()
prompt = generator.generate_category_prompt(context)

# Result: prompt includes character-specific analysis points
# from decision_flow, psychological_summary, and post_review_checklist
```

---

## Migration Notes

### For Existing Projects

1. **No Action Required**: Legacy characters continue using existing checks
2. **Gradual Migration**: Update to A24 schema when ready
3. **Automatic Enhancement**: New schema benefits applied automatically

### For New Projects

1. Use A24 character templates from [templates/character/](templates/character/)
2. Define `decision_flow` and `psychological_models`
3. Add `llm_prompt_profile` for specialized prompt generation
4. Run consistency checks to validate schema completeness

---

## API Reference

### CharacterProfile New Methods

```python
# Check if profile has new schema data
has_new_schema_data() -> bool

# Get decision flow (4-step process)
get_decision_flow() -> dict[str, str]

# Get psychological model summary bullets
get_psychological_summary() -> list[str]

# Get LLM-specific prompt configuration
get_llm_prompt_profile() -> dict[str, Any]

# Get narrative notes (foreshadowing, unresolved questions)
get_narrative_notes() -> dict[str, Any]

# Get specific layer data
get_layer(layer_name: str) -> dict[str, Any]
```

### CharacterConsistencyService Enhanced Checks

```python
# Internal methods (called automatically)
_check_decision_flow(line, line_num, character, context) -> list[ConsistencyViolation]
_check_psychological_model(line, line_num, character, context) -> list[ConsistencyViolation]
```

### EnhancedPromptGenerator Enhanced Methods

```python
# Internal helper (called automatically)
_build_enhanced_analysis_points(character_profiles) -> str
```

---

## Performance Impact

- **Minimal**: New checks only run for new schema characters
- **Backward Compatible**: Legacy characters use existing code path
- **No Breaking Changes**: Existing API unchanged

---

## Future Enhancements

### Phase 4: Project Migration
- Migrate existing character.yaml files to A24 schema
- Migration validation tools
- Bulk update scripts

### Phase 5: Advanced Analysis
- Narrative arc consistency tracking (using `narrative_notes`)
- Character growth pattern validation
- Relationship dynamics analysis

---

## Related Documents

- [A24 Adapter Implementation Report](docs/A24_キャラクタースキーマ_アダプター実装完了報告.md)
- [A24 Design Proposal](docs/proposals/a24-character-profile-adapter-design.md)
- [Character Template Guide](templates/character/README.md)
- [CLAUDE.md MCP/CLI Serialization](CLAUDE.md#MCP/CLI境界でのPath JSONシリアライズ原則)

---

**Next Steps**: Run `/noveler check 1` to test enhanced consistency checks with new schema characters
