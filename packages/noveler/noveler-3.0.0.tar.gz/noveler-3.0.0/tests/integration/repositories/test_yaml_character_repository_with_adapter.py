# File: tests/integration/repositories/test_yaml_character_repository_with_adapter.py
# Purpose: Integration tests for YamlCharacterRepository with CharacterProfileAdapter
# Context: Validates A24 new schema loading through repository layer

"""Integration tests for YamlCharacterRepository with A24 schema adapter.

Tests verify:
- A24 new schema (with layers) is correctly loaded via adapter
- Legacy schemas continue to work
- Adapter failure doesn't crash repository
- Raw layers are preserved for direct access
"""

import pytest
from pathlib import Path

from noveler.infrastructure.repositories.yaml_character_repository import YamlCharacterRepository


def test_repository_loads_a24_new_schema(tmp_path: Path):
    """Test repository loads A24 new schema using adapter."""
    # Setup: Create character YAML with A24 new schema
    settings_dir = tmp_path / "30_設定集"
    settings_dir.mkdir(parents=True)

    character_yaml = settings_dir / "キャラクター.yaml"
    character_yaml.write_text(
        """
character_book:
  version: "0.1.0"
  last_updated: "2025-01-01"
  characters:
    main:
      - character_id: "protagonist"
        display_name: "虫取 直人"
        status:
          lifecycle: "active"
        layers:
          layer1_psychology:
            role: "主人公"
            values: ["効率重視"]
            traits_positive: ["分析的"]
            traits_negative: ["皮肉屋"]
            core_motivations:
              primary: "ログを制御して平穏に生きる"
              secondary: []
            enduring_fears: []
            emotional_patterns:
              likes: ["効率化"]
              dislikes: ["レガシーコード"]
              momentary_fears: []
            psychological_models:
              summary_bullets:
                - "直感 → 価値観→ 仲間確認 → 行動 → 皮肉で締める"
          layer2_physical:
            appearance:
              height: "165cm"
              hair: "黒髪・寝癖"
              eyes: "黒"
            distinguishing_features:
              - "眉間に皺"
          layer5_expression_behavior:
            speech_profile:
              baseline_tone: "標準語・皮肉混じり"
              catchphrases:
                frustration: "やれやれ"
        llm_prompt_profile:
          default_scene_goal: "仲間を鼓舞して問題を解決"
    supporting: []
    antagonists: []
    background: []
""",
        encoding="utf-8",
    )

    # Execute
    repo = YamlCharacterRepository(tmp_path)
    profiles = repo.find_all_by_project("test_project")

    # Verify
    assert len(profiles) == 1

    profile = profiles[0]
    assert profile.name == "虫取 直人"

    # Verify converted attributes
    assert profile.get_attribute("character_id") == "protagonist"
    # category comes from status.lifecycle, not the character_book.characters.main key
    assert profile.get_attribute("category") == "active"

    # Layer1 attributes
    assert "直感 → 価値観" in profile.get_attribute("personality")
    assert profile.get_attribute("traits") == ["分析的", "皮肉屋"]
    assert profile.get_attribute("goals") == ["ログを制御して平穏に生きる"]
    assert profile.get_attribute("likes") == ["効率化"]
    assert profile.get_attribute("dislikes") == ["レガシーコード"]

    # Layer2 attributes
    assert profile.get_attribute("hair_color") == "黒髪・寝癖"
    assert profile.get_attribute("height") == "165cm"

    # Layer5 attributes
    assert profile.get_attribute("speech_style") == "標準語・皮肉混じり"
    assert "frustration: やれやれ" in profile.get_attribute("catchphrase")

    # Raw layers preserved
    assert profile.has_attribute("_raw_layers")
    assert profile.get_attribute("_raw_layers")["layer1_psychology"]["role"] == "主人公"
    assert profile.has_attribute("_raw_llm_prompt_profile")
    assert profile.get_attribute("_raw_llm_prompt_profile")["default_scene_goal"] == "仲間を鼓舞して問題を解決"


def test_repository_handles_legacy_character_book_schema(tmp_path: Path):
    """Test repository handles legacy character_book schema (no layers)."""
    settings_dir = tmp_path / "30_設定集"
    settings_dir.mkdir(parents=True)

    character_yaml = settings_dir / "キャラクター.yaml"
    character_yaml.write_text(
        """
character_book:
  characters:
    main:
      - character_id: "legacy_hero"
        display_name: "レガシー勇者"
        personality: "勇敢で正義感が強い"
        hair_color: "金髪"
    supporting: []
    antagonists: []
    background: []
""",
        encoding="utf-8",
    )

    repo = YamlCharacterRepository(tmp_path)
    profiles = repo.find_all_by_project("test_project")

    assert len(profiles) == 1
    profile = profiles[0]
    assert profile.name == "レガシー勇者"
    assert profile.get_attribute("personality") == "勇敢で正義感が強い"
    assert profile.get_attribute("hair_color") == "金髪"


def test_repository_handles_legacy_array_schema(tmp_path: Path):
    """Test repository handles legacy array schema (characters: [])."""
    settings_dir = tmp_path / "30_設定集"
    settings_dir.mkdir(parents=True)

    character_yaml = settings_dir / "キャラクター.yaml"
    character_yaml.write_text(
        """
characters:
  - name: "配列勇者"
    attributes:
      personality: "陽気"
      goals: ["世界を救う"]
""",
        encoding="utf-8",
    )

    repo = YamlCharacterRepository(tmp_path)
    profiles = repo.find_all_by_project("test_project")

    assert len(profiles) == 1
    profile = profiles[0]
    assert profile.name == "配列勇者"
    assert profile.get_attribute("personality") == "陽気"


def test_repository_handles_mixed_schemas(tmp_path: Path):
    """Test repository handles mixed new and legacy schemas."""
    settings_dir = tmp_path / "30_設定集"
    settings_dir.mkdir(parents=True)

    character_yaml = settings_dir / "キャラクター.yaml"
    character_yaml.write_text(
        """
character_book:
  characters:
    main:
      - character_id: "new_hero"
        display_name: "新スキーマ勇者"
        status:
          lifecycle: "active"
        layers:
          layer1_psychology:
            traits_positive: ["勇敢"]
      - character_id: "legacy_hero"
        display_name: "旧スキーマ勇者"
        personality: "慎重"
    supporting: []
    antagonists: []
    background: []
""",
        encoding="utf-8",
    )

    repo = YamlCharacterRepository(tmp_path)
    profiles = repo.find_all_by_project("test_project")

    assert len(profiles) == 2

    # New schema character
    new_profile = next(p for p in profiles if p.name == "新スキーマ勇者")
    assert new_profile.get_attribute("traits") == ["勇敢"]
    assert new_profile.has_attribute("_raw_layers")

    # Legacy character
    legacy_profile = next(p for p in profiles if p.name == "旧スキーマ勇者")
    assert legacy_profile.get_attribute("personality") == "慎重"
    assert not legacy_profile.has_attribute("_raw_layers")


def test_repository_handles_malformed_new_schema_gracefully(tmp_path: Path):
    """Test repository falls back to legacy extraction if adapter fails."""
    settings_dir = tmp_path / "30_設定集"
    settings_dir.mkdir(parents=True)

    character_yaml = settings_dir / "キャラクター.yaml"
    character_yaml.write_text(
        """
character_book:
  characters:
    main:
      - character_id: "malformed"
        display_name: "不正データ"
        layers:
          # Intentionally malformed, but should not crash
          layer1_psychology: "this should be a dict, not a string"
    supporting: []
    antagonists: []
    background: []
""",
        encoding="utf-8",
    )

    repo = YamlCharacterRepository(tmp_path)
    profiles = repo.find_all_by_project("test_project")

    # Should still load (fallback to legacy extraction)
    assert len(profiles) == 1
    profile = profiles[0]
    assert profile.name == "不正データ"


def test_repository_handles_empty_yaml(tmp_path: Path):
    """Test repository handles empty YAML file."""
    settings_dir = tmp_path / "30_設定集"
    settings_dir.mkdir(parents=True)

    character_yaml = settings_dir / "キャラクター.yaml"
    character_yaml.write_text("", encoding="utf-8")

    repo = YamlCharacterRepository(tmp_path)
    profiles = repo.find_all_by_project("test_project")

    assert len(profiles) == 0


def test_repository_handles_missing_file(tmp_path: Path):
    """Test repository handles missing character file."""
    repo = YamlCharacterRepository(tmp_path)
    profiles = repo.find_all_by_project("test_project")

    assert len(profiles) == 0


def test_repository_ignores_unknown_keys_in_new_schema(tmp_path: Path):
    """Test repository ignores extra fields while preserving new schema data."""
    settings_dir = tmp_path / "30_設定集"
    settings_dir.mkdir(parents=True)

    character_yaml = settings_dir / "キャラクター.yaml"
    character_yaml.write_text(
        """
character_book:
  version: "0.1.0"
  characters:
    main:
      - character_id: "protagonist"
        display_name: "虫取 直人"
        status:
          lifecycle: "active"
        layers:
          layer1_psychology:
            character_goals:
              external: "いじめから逃れる"
              internal: "黒雪姫を助ける"
              integration_type: "synergy"
            psychological_models:
              summary_bullets:
                - "直感 → 価値観→ 仲間確認 → 行動 → 皮肉で締める"
          layer5_expression_behavior:
            speech_profile:
              baseline_tone: "標準語・皮肉混じり"
        logging:
          character_log_directory: "records/characters/protagonist/"
          guidance: "命名: <YYYYMMDD>_<scene>.md"
        lite_profile_hint:
          use_lite: false
          minimal_fields:
            lite_scene_goal_copy: ""
            lite_values_copy: []
            lite_speech_tone_copy: ""
            lite_banned_phrases_copy: []
        episode_snapshots:
          - episode_id: "ep001"
            moment: "図書塔の初対面"
        extra_metadata:
          note: "ignored field"
    supporting: []
    antagonists: []
    background: []
""",
        encoding="utf-8",
    )

    repo = YamlCharacterRepository(tmp_path)
    profiles = repo.find_all_by_project("test_project")

    assert len(profiles) == 1
    profile = profiles[0]
    assert profile.get_character_goals()["integration_type"] == "synergy"
    assert profile.get_logging_settings()["guidance"].startswith("命名")
    assert profile.get_episode_snapshots()[0]["episode_id"] == "ep001"
