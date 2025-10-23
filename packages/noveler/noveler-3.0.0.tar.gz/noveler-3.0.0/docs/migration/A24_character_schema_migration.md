# A24 Character Schema Migration Checklist

## Prerequisites
- Legacy `キャラクター.yaml` backed up.
- New schema template available at `templates/character/character_book.yaml`.
- Decide `<log_root>` location for the project.

## Step-by-Step
1. **Create Working Copy**
   - Duplicate legacy file to `30_設定集/キャラクター.yaml.bak` before editing.
2. **Inject Root Wrapper**
   - Add `character_book` root node with metadata + logging defaults.
3. **Map Existing Layers**
   - Legacy Layer1..Layer5 → map to `layer1_psychology` ... `layer5_expression_behavior`.
   - Move ability blocks to `layer3_capabilities_skills` (`combat/non_combat/magical_abilities`).
4. **Populate Psychological Models**
   - Translate existing personality descriptors into `values`, `core_motivations`, `summary_bullets`.
   - Record MBTI/Enneagram data under `psychological_models` when available.
5. **Update Speech & Behavior**
   - Convert legacy speech dictionaries to nested `speech_profile` keys (tone/endings/pronouns/catchphrases).
6. **Add Prompt Profile**
   - For each main character, craft `llm_prompt_profile.inputs_template` from prompt docs.
   - Seed `post_review_checklist` statuses with `pending`.
7. **Configure Logging**
   - Set `<log_root>` and confirm directory structure `records/characters/<character_id>/` exists.
8. **Lite Mode Decision**
   - For minor characters, set `use_lite: true` and copy minimal fields into `lite_*_copy` keys.
9. **Validate**
   - Run schema validation (pending tool) or manual checks ensuring required keys present.
   - Spot-check prompts using new data.
10. **Finalize**
    - Remove backup once verified, update `docs/A24_キャラクター設定テンプレート_FitGap.md` status.

## Notes
- Keep `episode_snapshots` empty until per-episode data is ported.
- If psychological models are unknown, leave framework/type blank but keep placeholders.
