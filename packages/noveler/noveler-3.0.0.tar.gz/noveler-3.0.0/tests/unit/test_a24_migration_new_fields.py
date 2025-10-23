"""
# File: tests/unit/test_a24_migration_new_fields.py
# Purpose: Verify A24 migration emits new optional fields introduced on 2025-10-06.
# Context: Guards against regressions in scripts/migration/convert_character_to_a24.py
"""

from __future__ import annotations

import runpy
from pathlib import Path


def _load_migrator_class():
    # プロジェクトルートからの絶対パスで解決
    project_root = Path(__file__).parent.parent.parent
    module_path = project_root / "scripts" / "migration" / "convert_character_to_a24.py"
    assert module_path.exists(), f"Missing script: {module_path}"
    mod = runpy.run_path(str(module_path))
    return mod["A24CharacterMigrator"]


def test_migration_outputs_extended_fields():
    Migrator = _load_migrator_class()
    migrator = Migrator()

    legacy = {
        "name": "テスト太郎",
        "traits": ["優しい", "怠惰"],
        "values": ["誠実"],
        "likes": ["紅茶"],
        "dislikes": ["遅刻"],
    }

    data = migrator.migrate_character({"character": legacy})
    book = data["character_book"]
    main = book["characters"]["main"][0]
    layers = main["layers"]

    # Layer1: conflict_arcs and growth_vector (short/long)
    l1 = layers["layer1_psychology"]
    assert "conflict_arcs" in l1 and set(l1["conflict_arcs"].keys()) == {"short_term", "long_term"}
    assert set(l1["growth_vector"].keys()) >= {"current_arc", "future_hook", "short_term_arc", "long_term_arc"}

    # Layer2: symbolic_features present
    l2 = layers["layer2_physical"]
    assert "symbolic_features" in l2 and isinstance(l2["symbolic_features"], list)

    # Layer5: modes and voice_drift_rules present
    l5 = layers["layer5_expression_behavior"]
    speech = l5["speech_profile"]
    assert "modes" in speech and isinstance(speech["modes"], dict)
    assert "voice_drift_rules" in speech and isinstance(speech["voice_drift_rules"], list)

    # LLM review: decision_flow_trace_present added
    llm = main["llm_prompt_profile"]
    assert "decision_flow_trace_present" in llm["post_review_checklist"]["items"]

