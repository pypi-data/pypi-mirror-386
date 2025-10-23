# File: tests/unit/domain/value_objects/test_character_profile_new_schema_accessors.py
# Purpose: Unit tests for CharacterProfile A24 new schema accessors
# Context: Validates new accessor methods for hierarchical layers

"""Unit tests for CharacterProfile A24 new schema accessor methods.

Tests cover:
- get_layer() - Layer access
- get_llm_prompt_profile() - LLM prompt configuration
- get_narrative_notes() - Narrative hooks and questions
- has_new_schema_data() - Schema detection
- get_psychological_summary() - Psychological model summary
- get_decision_flow() - Decision-making process
"""

import pytest

from noveler.domain.value_objects.character_profile import CharacterProfile


@pytest.fixture
def new_schema_profile() -> CharacterProfile:
    """Create a CharacterProfile with A24 new schema data."""
    attributes = {
        "character_id": "protagonist",
        "category": "active",
        # Legacy attributes
        "personality": "直感 → 価値観→ 仲間確認 → 行動 → 皮肉で締める",
        "traits": ["分析的", "仲間思い", "皮肉屋"],
        # Raw new schema data
        "_raw_layers": {
            "layer1_psychology": {
                "role": "主人公",
                "values": ["効率重視", "正義感"],
                "character_goals": {
                    "external": "いじめから逃れる",
                    "internal": "黒雪姫を助ける",
                    "integration_type": "synergy",
                },
                "psychological_models": {
                    "summary_bullets": [
                        "直感 → 価値観→ 仲間確認 → 行動 → 皮肉で締める",
                        "拒絶に敏感、回復は早い",
                    ],
                    "decision_flow": {
                        "decision_step_perception": "ログで状況把握",
                        "decision_step_evaluation": "価値観/効率基準でスコア付け",
                        "decision_step_action": "最小工数で実行",
                        "decision_step_emotional_aftermath": "皮肉・諦観でカバー",
                    },
                },
            },
            "layer2_physical": {
                "appearance": {"height": "165cm", "hair": "黒髪・寝癖", "eyes": "黒"},
            },
            "layer5_expression_behavior": {
                "speech_profile": {"baseline_tone": "標準語・皮肉混じり"},
            },
        },
        "_raw_status": {"lifecycle": "active", "reviewer": "", "last_reviewed": ""},
        "_raw_llm_prompt_profile": {
            "default_scene_goal": "仲間を鼓舞して問題を解決",
            "inputs_template": {
                "scene_role_and_goal": "",
                "psych_summary": ["直感 → 価値観→ 仲間確認 → 行動 → 皮肉で締める"],
            },
        },
        "_raw_narrative_notes": {
            "foreshadowing_hooks": ["The Architectとの和解"],
            "unresolved_questions": ["ログの正体は?"],
        },
        "_raw_logging": {
            "character_log_directory": "<log_root>/protagonist/",
            "guidance": "命名: <YYYYMMDD>_<scene>.md",
            "last_entry": "",
        },
        "_raw_lite_profile_hint": {
            "use_lite": False,
            "minimal_fields": {
                "lite_scene_goal_copy": "",
                "lite_values_copy": [],
                "lite_speech_tone_copy": "",
                "lite_banned_phrases_copy": [],
            },
        },
        "_raw_episode_snapshots": [
            {
                "episode_id": "ep001",
                "moment": "図書塔の初対面",
                "notes": "決断ルールに『信頼の試し』を追加",
            }
        ],
    }

    return CharacterProfile(name="虫取 直人", attributes=attributes)


@pytest.fixture
def legacy_profile() -> CharacterProfile:
    """Create a CharacterProfile with legacy schema (no _raw_layers)."""
    attributes = {
        "personality": "勇敢で正義感が強い",
        "hair_color": "金髪",
        "speech_style": "丁寧語",
    }

    return CharacterProfile(name="レガシー勇者", attributes=attributes)


# ========================================
# get_layer() tests
# ========================================


def test_get_layer_returns_layer_data(new_schema_profile: CharacterProfile):
    """Test get_layer returns specified layer data."""
    layer1 = new_schema_profile.get_layer("layer1_psychology")

    assert layer1["role"] == "主人公"
    assert layer1["values"] == ["効率重視", "正義感"]


def test_get_layer_returns_empty_dict_for_missing_layer(new_schema_profile: CharacterProfile):
    """Test get_layer returns empty dict for non-existent layer."""
    layer99 = new_schema_profile.get_layer("layer99_nonexistent")

    assert layer99 == {}


def test_get_layer_returns_empty_dict_for_legacy_profile(legacy_profile: CharacterProfile):
    """Test get_layer returns empty dict for legacy profile (no _raw_layers)."""
    layer1 = legacy_profile.get_layer("layer1_psychology")

    assert layer1 == {}


# ========================================
# get_llm_prompt_profile() tests
# ========================================


def test_get_llm_prompt_profile_returns_profile_data(new_schema_profile: CharacterProfile):
    """Test get_llm_prompt_profile returns LLM configuration."""
    llm_profile = new_schema_profile.get_llm_prompt_profile()

    assert llm_profile["default_scene_goal"] == "仲間を鼓舞して問題を解決"
    assert "psych_summary" in llm_profile["inputs_template"]


def test_get_llm_prompt_profile_returns_empty_dict_for_legacy(legacy_profile: CharacterProfile):
    """Test get_llm_prompt_profile returns empty dict for legacy profile."""
    llm_profile = legacy_profile.get_llm_prompt_profile()

    assert llm_profile == {}


# ========================================
# get_narrative_notes() tests
# ========================================


def test_get_narrative_notes_returns_notes_data(new_schema_profile: CharacterProfile):
    """Test get_narrative_notes returns narrative hooks and questions."""
    notes = new_schema_profile.get_narrative_notes()

    assert "The Architectとの和解" in notes["foreshadowing_hooks"]
    assert "ログの正体は?" in notes["unresolved_questions"]


def test_get_narrative_notes_returns_empty_dict_for_legacy(legacy_profile: CharacterProfile):
    """Test get_narrative_notes returns empty dict for legacy profile."""
    notes = legacy_profile.get_narrative_notes()

    assert notes == {}


# ========================================
# has_new_schema_data() tests
# ========================================


def test_has_new_schema_data_returns_true_for_new_schema(new_schema_profile: CharacterProfile):
    """Test has_new_schema_data returns True for new schema profile."""
    assert new_schema_profile.has_new_schema_data() is True


def test_has_new_schema_data_returns_false_for_legacy(legacy_profile: CharacterProfile):
    """Test has_new_schema_data returns False for legacy profile."""
    assert legacy_profile.has_new_schema_data() is False


# ========================================
# get_psychological_summary() tests
# ========================================


def test_get_psychological_summary_returns_summary_bullets(new_schema_profile: CharacterProfile):
    """Test get_psychological_summary returns summary_bullets."""
    summary = new_schema_profile.get_psychological_summary()

    assert len(summary) == 2
    assert "直感 → 価値観→ 仲間確認 → 行動 → 皮肉で締める" in summary
    assert "拒絶に敏感、回復は早い" in summary


def test_get_psychological_summary_returns_empty_list_for_legacy(legacy_profile: CharacterProfile):
    """Test get_psychological_summary returns empty list for legacy profile."""
    summary = legacy_profile.get_psychological_summary()

    assert summary == []


def test_get_psychological_summary_handles_missing_summary_bullets():
    """Test get_psychological_summary handles missing summary_bullets gracefully."""
    attributes = {
        "_raw_layers": {
            "layer1_psychology": {
                "role": "主人公",
                # psychological_models missing
            }
        }
    }
    profile = CharacterProfile(name="不完全", attributes=attributes)

    summary = profile.get_psychological_summary()

    assert summary == []


# ========================================
# get_decision_flow() tests
# ========================================


def test_get_decision_flow_returns_decision_steps(new_schema_profile: CharacterProfile):
    """Test get_decision_flow returns decision-making process."""
    flow = new_schema_profile.get_decision_flow()

    assert flow["decision_step_perception"] == "ログで状況把握"
    assert flow["decision_step_evaluation"] == "価値観/効率基準でスコア付け"
    assert flow["decision_step_action"] == "最小工数で実行"
    assert flow["decision_step_emotional_aftermath"] == "皮肉・諦観でカバー"


def test_get_decision_flow_returns_empty_dict_for_legacy(legacy_profile: CharacterProfile):
    """Test get_decision_flow returns empty dict for legacy profile."""
    flow = legacy_profile.get_decision_flow()

    assert flow == {}


def test_get_decision_flow_handles_missing_decision_flow():
    """Test get_decision_flow handles missing decision_flow gracefully."""
    attributes = {
        "_raw_layers": {
            "layer1_psychology": {
                "psychological_models": {
                    "summary_bullets": ["要約のみ"]
                    # decision_flow missing
                }
            }
        }
    }
    profile = CharacterProfile(name="不完全", attributes=attributes)

    flow = profile.get_decision_flow()

    assert flow == {}


# ========================================
# get_status() tests
# ========================================


def test_get_status_returns_status(new_schema_profile: CharacterProfile):
    """Test get_status returns lifecycle metadata."""
    status = new_schema_profile.get_status()

    assert status["lifecycle"] == "active"


def test_get_status_returns_empty_for_legacy(legacy_profile: CharacterProfile):
    """Test get_status returns empty dict for legacy profile."""
    assert legacy_profile.get_status() == {}


# ========================================
# get_logging_settings() tests
# ========================================


def test_get_logging_settings_returns_config(new_schema_profile: CharacterProfile):
    """Test get_logging_settings returns logging configuration."""
    logging_cfg = new_schema_profile.get_logging_settings()

    assert logging_cfg["guidance"].startswith("命名")


def test_get_logging_settings_returns_empty_for_legacy(legacy_profile: CharacterProfile):
    """Test get_logging_settings returns empty dict for legacy profile."""
    assert legacy_profile.get_logging_settings() == {}


# ========================================
# get_lite_profile_hint() tests
# ========================================


def test_get_lite_profile_hint_returns_hint(new_schema_profile: CharacterProfile):
    """Test get_lite_profile_hint returns lite profile data."""
    hint = new_schema_profile.get_lite_profile_hint()

    assert hint["use_lite"] is False


def test_get_lite_profile_hint_returns_empty_for_legacy(legacy_profile: CharacterProfile):
    """Test get_lite_profile_hint returns empty dict for legacy profile."""
    assert legacy_profile.get_lite_profile_hint() == {}


# ========================================
# get_episode_snapshots() tests
# ========================================


def test_get_episode_snapshots_returns_snapshots(new_schema_profile: CharacterProfile):
    """Test get_episode_snapshots returns list of episode deltas."""
    snapshots = new_schema_profile.get_episode_snapshots()

    assert snapshots and snapshots[0]["episode_id"] == "ep001"


def test_get_episode_snapshots_returns_empty_for_legacy(legacy_profile: CharacterProfile):
    """Test get_episode_snapshots returns empty list for legacy profile."""
    assert legacy_profile.get_episode_snapshots() == []


# ========================================
# get_character_goals() tests
# ========================================


def test_get_character_goals_returns_goals(new_schema_profile: CharacterProfile):
    """Test get_character_goals returns dual motive configuration."""
    goals = new_schema_profile.get_character_goals()

    assert goals["integration_type"] == "synergy"


def test_get_character_goals_returns_empty_for_legacy(legacy_profile: CharacterProfile):
    """Test get_character_goals returns empty dict for legacy profile."""
    assert legacy_profile.get_character_goals() == {}


# ========================================
# Integration test: Multiple accessors
# ========================================


def test_multiple_accessors_work_together(new_schema_profile: CharacterProfile):
    """Test multiple new schema accessors can be used together."""
    # Check schema type
    assert new_schema_profile.has_new_schema_data()

    # Access layer
    layer1 = new_schema_profile.get_layer("layer1_psychology")
    assert layer1["role"] == "主人公"

    # Access psychological info
    summary = new_schema_profile.get_psychological_summary()
    assert len(summary) > 0

    flow = new_schema_profile.get_decision_flow()
    assert "decision_step_perception" in flow

    # Access LLM profile
    llm_profile = new_schema_profile.get_llm_prompt_profile()
    assert "default_scene_goal" in llm_profile

    # Access narrative notes
    notes = new_schema_profile.get_narrative_notes()
    assert "foreshadowing_hooks" in notes

    # Access additional helpers
    assert new_schema_profile.get_status()["lifecycle"] == "active"
    assert new_schema_profile.get_logging_settings()
    assert isinstance(new_schema_profile.get_character_goals(), dict)
