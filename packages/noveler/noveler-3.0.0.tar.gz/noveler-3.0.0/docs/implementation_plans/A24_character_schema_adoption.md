# A24 Character Schema Adoption Plan

## Scope
- Apply the newly approved character schema (`docs/A24_キャラクター設定テンプレート_新スキーマ草案.md`) across initialization, prompt workflows, and tooling.

## Objectives
1. Replace legacy minimal `キャラクター.yaml` generation with schema-compliant output.
2. Update A24/A38 prompt templates and downstream services to consume new fields.
3. Provide migration guidance for existing projects and logging assets.
4. Ensure automation/tests validate schema conformity.

## Workstreams
### 1. Initialization Pipeline
- [ ] Update `src/noveler/domain/initialization/services.py::_generate_character_settings` to emit schema nodes.
- [ ] Add unit snapshot for generated YAML (include `lite_profile_hint` defaults).
- [ ] Introduce helper for `<log_root>` resolution shared across services.

### 2. Template Assets
- [ ] Produce canonical YAML template (`templates/character/character_book.yaml`) mirroring schema with placeholders.
- [ ] Provide validation artifact (JSON Schema or pydantic model) under `specs/schemas` for automated checks.
- [ ] Reference the schema in `docs/A24_キャラクター設計ガイド.md` and related guides.

### 3. Prompt Integration
- [ ] Revise A24/A38 prompt instructions to reference renamed layers and new `llm_prompt_profile` keys.
- [ ] Update prompt generator services / MCP tools to read `scene_role_and_goal`, `deliberate_voice_drift`, etc.
- [ ] Ensure Lite mode characters degrade gracefully within prompts.

### 4. Logging & Lite Mode
- [ ] Ship markdown template at `docs/log_templates/character_scene_log.md` mentioned by schema.
- [ ] Document Lite copy semantics (`lite_*_copy` keys) for editors.
- [ ] Update logging helpers to honour `character_log_directory` and root derivation.

### 5. Migration & QA
- [ ] Draft migration checklist to map legacy five-layer YAML onto new schema.
- [ ] Update `docs/A24_キャラクター設定テンプレート_FitGap.md` with resolution status once tasks complete.
- [ ] Add regression tests ensuring character consistency services accept new keys.

## Risks / Considerations
- Downstream consumers might depend on old key names; inventory before rollout.
- `<log_root>` must resolve consistently across Windows/Wsl environments.
- Lite mode should avoid emitting empty sections that break schema consumers.

## Next Steps
1. Create canonical YAML template (Workstream 2).
2. Implement initialization pipeline changes with tests.
3. Begin prompt documentation updates alongside Lite guidance.
