# File: tests/unit/domain/adapters/test_character_profile_adapter.py
# Purpose: Unit tests for CharacterProfileAdapter
# Context: Validates A24 new schema → CharacterProfile conversion

"""Unit tests for CharacterProfileAdapter.

Tests cover:
- Layer1 (psychology) → personality, traits, goals, likes, dislikes, fears
- Layer2 (physical) → appearance attributes
- Layer5 (expression) → speech attributes
- Raw layers preservation for direct access
- Edge cases: empty layers, missing fields, fallback behavior
"""

import pytest

from noveler.domain.adapters.character_profile_adapter import (
    CharacterBookEntry,
    CharacterProfileAdapter,
    _extract_catchphrase,
    _extract_dislikes,
    _extract_facial_features,
    _extract_fears,
    _extract_goals,
    _extract_likes,
    _extract_nested,
    _extract_personality,
    _extract_speech_style,
    _extract_traits,
)


# ========================================
# Layer1: Psychology tests
# ========================================


def test_extract_personality_from_summary_bullets():
    """Test personality extraction from summary_bullets (priority)."""
    layer1 = {
        "psychological_models": {
            "summary_bullets": ["直感 → 価値観→ 仲間確認 → 行動 → 皮肉で締める", "拒絶に敏感、回復は早い"]
        },
        "traits_positive": ["分析的"],
        "traits_negative": ["皮肉屋"],
    }

    result = _extract_personality(layer1)

    assert "直感 → 価値観" in result
    assert "拒絶に敏感" in result
    assert "分析的" not in result  # summary_bulletsを優先するため、traitsは含まれない


def test_extract_personality_fallback_to_traits():
    """Test personality extraction falls back to traits when summary_bullets is empty."""
    layer1 = {
        "psychological_models": {},  # No summary_bullets
        "traits_positive": ["勇敢", "優しい"],
        "traits_negative": ["短気"],
    }

    result = _extract_personality(layer1)

    assert "Positive: 勇敢, 優しい" in result
    assert "Negative: 短気" in result


def test_extract_personality_empty():
    """Test personality extraction with empty layer1."""
    layer1 = {}
    result = _extract_personality(layer1)
    assert result == ""


def test_extract_traits():
    """Test traits extraction (positive + negative combined)."""
    layer1 = {
        "traits_positive": ["分析的", "仲間思い"],
        "traits_negative": ["皮肉屋", "怠惰"],
    }

    result = _extract_traits(layer1)

    assert result == ["分析的", "仲間思い", "皮肉屋", "怠惰"]


def test_extract_likes():
    """Test likes extraction from emotional_patterns."""
    layer1 = {"emotional_patterns": {"likes": ["効率化", "自動化"]}}

    result = _extract_likes(layer1)

    assert result == ["効率化", "自動化"]


def test_extract_dislikes():
    """Test dislikes extraction from emotional_patterns."""
    layer1 = {"emotional_patterns": {"dislikes": ["レガシーコード", "残業"]}}

    result = _extract_dislikes(layer1)

    assert result == ["レガシーコード", "残業"]


def test_extract_fears_combined():
    """Test fears extraction (enduring + momentary combined, duplicates removed)."""
    layer1 = {
        "enduring_fears": ["デスマーチ", "再び中間管理職"],
        "emotional_patterns": {"momentary_fears": ["強制残業", "デスマーチ"]},  # "デスマーチ" は重複
    }

    result = _extract_fears(layer1)

    # 重複排除、enduring優先順
    assert result == ["デスマーチ", "再び中間管理職", "強制残業"]


def test_extract_fears_only_enduring():
    """Test fears extraction with only enduring_fears."""
    layer1 = {"enduring_fears": ["トラウマA", "トラウマB"]}

    result = _extract_fears(layer1)

    assert result == ["トラウマA", "トラウマB"]


def test_extract_goals():
    """Test goals extraction from core_motivations."""
    layer1 = {
        "core_motivations": {"primary": "ログを制御して平穏に生きる", "secondary": ["仲間を守る", "技術探究"]}
    }

    result = _extract_goals(layer1)

    assert result == ["ログを制御して平穏に生きる", "仲間を守る", "技術探究"]


def test_extract_goals_only_primary():
    """Test goals extraction with only primary motivation."""
    layer1 = {"core_motivations": {"primary": "世界を救う"}}

    result = _extract_goals(layer1)

    assert result == ["世界を救う"]


# ========================================
# Layer2: Physical tests
# ========================================


def test_extract_facial_features():
    """Test facial features extraction from distinguishing_features."""
    layer2 = {"distinguishing_features": ["眉間に皺", "猫背", "鋭い目つき"]}  # 顔関連  # 顔以外  # 顔関連

    result = _extract_facial_features(layer2)

    assert "眉間に皺" in result
    assert "鋭い目つき" in result
    assert "猫背" not in result  # 顔以外は除外


def test_extract_facial_features_empty():
    """Test facial features extraction with no distinguishing_features."""
    layer2 = {}
    result = _extract_facial_features(layer2)
    assert result == ""


# ========================================
# Layer5: Expression tests
# ========================================


def test_extract_speech_style():
    """Test speech style extraction from baseline_tone."""
    layer5 = {"speech_profile": {"baseline_tone": "標準語・皮肉混じり"}}

    result = _extract_speech_style(layer5)

    assert result == "標準語・皮肉混じり"


def test_extract_catchphrase():
    """Test catchphrase extraction with situational context."""
    layer5 = {"speech_profile": {"catchphrases": {"frustration": "やれやれ", "surprise": "マジか"}}}

    result = _extract_catchphrase(layer5)

    assert "frustration: やれやれ" in result
    assert "surprise: マジか" in result
    assert ";" in result  # セパレータ確認


def test_extract_catchphrase_empty():
    """Test catchphrase extraction with no catchphrases."""
    layer5 = {"speech_profile": {}}
    result = _extract_catchphrase(layer5)
    assert result == ""


# ========================================
# Utility function tests
# ========================================


def test_extract_nested_success():
    """Test nested value extraction with valid path."""
    data = {"appearance": {"hair": "黒髪・寝癖", "eyes": "黒"}}

    assert _extract_nested(data, "appearance.hair") == "黒髪・寝癖"
    assert _extract_nested(data, "appearance.eyes") == "黒"


def test_extract_nested_missing_key():
    """Test nested value extraction with missing key."""
    data = {"appearance": {"hair": "黒髪"}}

    assert _extract_nested(data, "appearance.eyes") is None
    assert _extract_nested(data, "missing.path") is None


def test_extract_nested_non_dict():
    """Test nested value extraction when intermediate value is not dict."""
    data = {"appearance": "string_value"}

    assert _extract_nested(data, "appearance.hair") is None


# ========================================
# Full adapter tests
# ========================================


def test_adapter_converts_full_entry():
    """Test full CharacterBookEntry conversion to CharacterProfile."""
    entry = CharacterBookEntry(
        character_id="protagonist",
        display_name="虫取 直人",
        status={"lifecycle": "active", "last_reviewed": "2025-01-01"},
        layers={
            "layer1_psychology": {
                "role": "主人公",
                "values": ["効率重視", "正義感"],
                "character_goals": {
                    "external": "いじめから逃れる",
                    "internal": "黒雪姫を助ける",
                    "integration_type": "synergy",
                },
                "traits_positive": ["分析的", "仲間思い"],
                "traits_negative": ["皮肉屋", "怠惰"],
                "core_motivations": {"primary": "ログを制御して平穏に生きる", "secondary": ["仲間を守る"]},
                "enduring_fears": ["デスマーチ"],
                "emotional_patterns": {"likes": ["効率化"], "dislikes": ["レガシーコード"], "momentary_fears": ["強制残業"]},
                "psychological_models": {"summary_bullets": ["直感 → 価値観→ 仲間確認 → 行動 → 皮肉で締める"]},
            },
            "layer2_physical": {
                "appearance": {"height": "165cm", "build": "中肉中背", "hair": "黒髪・寝癖", "eyes": "黒"},
                "distinguishing_features": ["眉間に皺", "猫背"],
                "attire": {"typical": "学園ローブ"},
            },
            "layer5_expression_behavior": {
                "speech_profile": {"baseline_tone": "標準語・皮肉混じり", "catchphrases": {"frustration": "やれやれ"}}
            },
        },
        llm_prompt_profile={"default_scene_goal": "仲間を鼓舞して問題を解決"},
        logging={
            "character_log_directory": "records/characters/protagonist/",
            "guidance": "命名: <YYYYMMDD>_<scene>.md",
            "last_entry": "",
        },
        lite_profile_hint={
            "use_lite": False,
            "minimal_fields": {
                "lite_scene_goal_copy": "",
                "lite_values_copy": [],
                "lite_speech_tone_copy": "",
                "lite_banned_phrases_copy": [],
            },
        },
        episode_snapshots=[
            {
                "episode_id": "ep001",
                "moment": "図書塔の初対面",
                "notes": "決断ルールに『信頼の試し』を追加",
            }
        ],
    )

    profile = CharacterProfileAdapter.from_character_book_entry(entry)

    # Name
    assert profile.name == "虫取 直人"

    # Meta
    assert profile.get_attribute("character_id") == "protagonist"
    assert profile.get_attribute("category") == "active"

    # Layer1: Psychology
    assert "直感 → 価値観" in profile.get_attribute("personality")
    assert profile.get_attribute("traits") == ["分析的", "仲間思い", "皮肉屋", "怠惰"]
    assert profile.get_attribute("goals") == ["ログを制御して平穏に生きる", "仲間を守る"]
    assert profile.get_attribute("likes") == ["効率化"]
    assert profile.get_attribute("dislikes") == ["レガシーコード"]
    assert profile.get_attribute("fears") == ["デスマーチ", "強制残業"]

    # Layer2: Physical
    assert profile.get_attribute("hair_color") == "黒髪・寝癖"
    assert profile.get_attribute("eye_color") == "黒"
    assert profile.get_attribute("height") == "165cm"
    assert profile.get_attribute("build") == "中肉中背"
    assert "眉間に皺" in profile.get_attribute("facial_features")
    assert profile.get_attribute("clothing_style") == "学園ローブ"

    # Layer5: Expression
    assert profile.get_attribute("speech_style") == "標準語・皮肉混じり"
    assert "frustration: やれやれ" in profile.get_attribute("catchphrase")

    # Deprecated attributes (empty)
    assert profile.get_attribute("dialect") == ""
    assert profile.get_attribute("verbal_tics") == []
    assert profile.get_attribute("formality_level") == ""

    # Raw layers preserved
    assert profile.has_attribute("_raw_layers")
    assert profile.get_attribute("_raw_layers")["layer1_psychology"]["role"] == "主人公"
    assert profile.has_attribute("_raw_llm_prompt_profile")
    assert profile.get_attribute("_raw_llm_prompt_profile")["default_scene_goal"] == "仲間を鼓舞して問題を解決"
    assert profile.get_status()["lifecycle"] == "active"
    assert profile.get_logging_settings()["guidance"].startswith("命名")
    assert profile.get_lite_profile_hint()["use_lite"] is False
    assert profile.get_episode_snapshots()[0]["episode_id"] == "ep001"
    assert profile.get_character_goals()["integration_type"] == "synergy"


def test_adapter_handles_empty_layers():
    """Test adapter handles empty layers gracefully."""
    entry = CharacterBookEntry(
        character_id="minimal",
        display_name="ミニマルキャラ",
        status={"lifecycle": "pending"},
        layers={},  # Empty layers
    )

    profile = CharacterProfileAdapter.from_character_book_entry(entry)

    assert profile.name == "ミニマルキャラ"
    assert profile.get_attribute("personality") == ""
    assert profile.get_attribute("traits") == []
    assert profile.get_attribute("goals") == []


def test_adapter_to_character_book_entry_not_implemented():
    """Test reverse conversion raises NotImplementedError."""
    from noveler.domain.value_objects.character_profile import CharacterProfile

    profile = CharacterProfile(name="Test", attributes={})

    with pytest.raises(NotImplementedError, match="Reverse conversion.*not yet implemented"):
        CharacterProfileAdapter.to_character_book_entry(profile)


# ========================================
# Edge case tests
# ========================================


def test_adapter_handles_missing_nested_fields():
    """Test adapter handles missing nested fields without crashing."""
    entry = CharacterBookEntry(
        character_id="incomplete",
        display_name="不完全データ",
        status={},
        layers={
            "layer1_psychology": {
                "traits_positive": ["勇敢"]
                # core_motivations, emotional_patterns など欠損
            },
            "layer2_physical": {
                "appearance": {}  # 全て欠損
            },
        },
    )

    profile = CharacterProfileAdapter.from_character_book_entry(entry)

    # 欠損フィールドは空値を返す
    assert profile.get_attribute("goals") == []
    assert profile.get_attribute("likes") == []
    assert profile.get_attribute("hair_color") is None
    assert profile.get_attribute("speech_style") == ""
