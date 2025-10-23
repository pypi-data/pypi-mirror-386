# File: tests/unit/scripts/migration/test_convert_character_to_a24.py
# Purpose: Unit tests for A24 character migration script
# Context: Phase 4 testing for legacy-to-A24 schema conversion

"""
Tests for A24 Character Migration Tool

Validates automated field mapping, traits classification, and manual review detection.
"""

import pytest

from scripts.migration.convert_character_to_a24 import A24CharacterMigrator


@pytest.fixture
def migrator() -> A24CharacterMigrator:
    """Create a fresh migrator instance for each test."""
    return A24CharacterMigrator()


@pytest.fixture
def legacy_character_minimal() -> dict:
    """Minimal legacy character data."""
    return {"name": "山田太郎", "role": "protagonist"}


@pytest.fixture
def legacy_character_full() -> dict:
    """Full legacy character data with all fields."""
    return {
        "name": "佐藤花子",
        "role": "antagonist",
        "traits": ["勇敢", "短気", "誠実"],
        "values": ["正義", "自由"],
        "motivation": "世界を守る",
        "fears": ["孤独", "裏切り"],
        "likes": ["読書", "コーヒー"],
        "dislikes": ["嘘", "不正"],
        "appearance": {
            "height": "165cm",
            "build": "スリム",
            "hair": "黒髪ロング",
            "eyes": "茶色",
            "attire": "スーツ",
        },
        "combat_skills": ["剣術", "魔法"],
        "non_combat_skills": ["交渉", "医療"],
        "affiliations": ["騎士団"],
        "relationships": [{"name": "田中次郎", "relationship": "親友"}],
        "speech_profile": {
            "tone": "丁寧",
            "sentence_endings": {"normal": "です", "question": "ですか"},
        },
    }


class TestA24CharacterMigrator:
    """Test suite for A24 character migrator."""

    def test_migrate_minimal_character(self, migrator, legacy_character_minimal):
        """Test migration with minimal legacy data."""
        result = migrator.migrate_character(legacy_character_minimal)

        # Check character_book structure
        assert "character_book" in result
        assert result["character_book"]["version"] == "0.1.0"
        assert "characters" in result["character_book"]

        # Check main character
        main_chars = result["character_book"]["characters"]["main"]
        assert len(main_chars) == 1

        char = main_chars[0]
        assert char["display_name"] == "山田太郎"
        assert char["character_id"] == "山田太郎"
        assert char["layers"]["layer1_psychology"]["role"] == "protagonist"

    def test_migrate_full_character(self, migrator, legacy_character_full):
        """Test migration with full legacy data."""
        result = migrator.migrate_character(legacy_character_full)

        char = result["character_book"]["characters"]["main"][0]

        # Layer 1: Psychology
        layer1 = char["layers"]["layer1_psychology"]
        assert layer1["role"] == "antagonist"
        assert layer1["values"] == ["正義", "自由"]
        assert layer1["core_motivations"]["primary"] == "世界を守る"
        assert layer1["enduring_fears"] == ["孤独", "裏切り"]
        assert layer1["emotional_patterns"]["likes"] == ["読書", "コーヒー"]
        assert layer1["emotional_patterns"]["dislikes"] == ["嘘", "不正"]

        # Layer 2: Physical
        layer2 = char["layers"]["layer2_physical"]
        assert layer2["appearance"]["height"] == "165cm"
        assert layer2["appearance"]["hair"] == "黒髪ロング"
        assert layer2["attire"]["typical"] == "スーツ"

        # Layer 3: Capabilities
        layer3 = char["layers"]["layer3_capabilities_skills"]
        assert layer3["combat_skills"] == ["剣術", "魔法"]
        assert layer3["non_combat_skills"] == ["交渉", "医療"]

        # Layer 4: Social
        layer4 = char["layers"]["layer4_social_network"]
        assert layer4["affiliations"] == ["騎士団"]
        assert len(layer4["relationships"]) == 1

        # Layer 5: Expression
        layer5 = char["layers"]["layer5_expression_behavior"]
        assert layer5["speech_profile"]["baseline_tone"] == "丁寧"

    def test_traits_classification(self, migrator, legacy_character_full):
        """Test automatic traits classification into positive/negative."""
        result = migrator.migrate_character(legacy_character_full)

        char = result["character_book"]["characters"]["main"][0]
        layer1 = char["layers"]["layer1_psychology"]

        # "短気" should be classified as negative
        assert "短気" in layer1["traits_negative"]

        # "勇敢" and "誠実" should be classified as positive
        assert "勇敢" in layer1["traits_positive"]
        assert "誠実" in layer1["traits_positive"]

    def test_traits_classification_requires_manual_review(
        self, migrator, legacy_character_full
    ):
        """Test that traits classification triggers manual review warning."""
        migrator.migrate_character(legacy_character_full)

        # Should have manual review warning for traits
        assert any(
            "CRITICAL: Traits were auto-classified" in item
            for item in migrator.manual_review_required
        )

    def test_psychological_models_requires_manual_input(
        self, migrator, legacy_character_minimal
    ):
        """Test that psychological_models section requires manual input."""
        migrator.migrate_character(legacy_character_minimal)

        # Should have manual review warning for psychological models
        assert any(
            "psychological_models" in item for item in migrator.manual_review_required
        )

    def test_llm_prompt_profile_requires_manual_input(
        self, migrator, legacy_character_minimal
    ):
        """Test that llm_prompt_profile section requires manual input."""
        migrator.migrate_character(legacy_character_minimal)

        # Should have manual review warning for LLM prompt profile
        assert any(
            "llm_prompt_profile" in item for item in migrator.manual_review_required
        )

    def test_character_id_generation(self, migrator):
        """Test character_id generation from display name."""
        char_id = migrator._generate_character_id("山田 太郎")
        assert char_id == "山田_太郎"

    def test_character_id_non_ascii_warning(self, migrator):
        """Test warning for non-ASCII character IDs."""
        migrator._generate_character_id("山田太郎")

        # Should have warning about non-ASCII characters
        assert any("non-ASCII" in warning for warning in migrator.warnings)

    def test_new_fields_initialized_empty(self, migrator, legacy_character_minimal):
        """Test that new A24 fields are initialized with empty values."""
        result = migrator.migrate_character(legacy_character_minimal)
        char = result["character_book"]["characters"]["main"][0]

        # New fields should exist but be empty
        assert char["narrative_notes"]["foreshadowing_hooks"] == []
        assert char["narrative_notes"]["unresolved_questions"] == []
        assert char["lite_profile_hint"]["use_lite"] is False
        assert char["episode_snapshots"] == []

        # Layer 1 new fields
        layer1 = char["layers"]["layer1_psychology"]
        assert layer1["growth_vector"]["current_arc"] == ""
        assert layer1["growth_vector"]["future_hook"] == ""
        assert layer1["psychological_models"]["decision_flow"][
            "decision_step_perception"
        ] == ""

    def test_status_initialized_correctly(self, migrator, legacy_character_minimal):
        """Test that status section is initialized with correct defaults."""
        result = migrator.migrate_character(legacy_character_minimal)
        char = result["character_book"]["characters"]["main"][0]

        assert char["status"]["lifecycle"] == "active"
        assert char["status"]["last_reviewed"] == ""
        assert char["status"]["reviewer"] == ""

    def test_logging_configuration_initialized(
        self, migrator, legacy_character_minimal
    ):
        """Test that logging configuration is initialized correctly."""
        result = migrator.migrate_character(legacy_character_minimal)
        char = result["character_book"]["characters"]["main"][0]

        # character_id should be substituted with actual ID
        char_id = char["character_id"]
        assert char_id in char["logging"]["character_log_directory"]
        assert "<log_root>" in char["logging"]["character_log_directory"]
        assert "YYYYMMDD" in char["logging"]["guidance"]

    def test_extract_legacy_character_various_formats(self, migrator):
        """Test extraction from various legacy format structures."""
        # Format 1: Direct character object
        format1 = {"name": "Test1", "role": "hero"}
        char1 = migrator._extract_legacy_character(format1)
        assert char1["name"] == "Test1"

        # Format 2: Wrapped in "character" key
        format2 = {"character": {"name": "Test2", "role": "villain"}}
        char2 = migrator._extract_legacy_character(format2)
        assert char2["name"] == "Test2"

        # Format 3: List in "characters" key
        format3 = {"characters": [{"name": "Test3", "role": "support"}]}
        char3 = migrator._extract_legacy_character(format3)
        assert char3["name"] == "Test3"

    def test_split_traits_empty_list(self, migrator):
        """Test traits splitting with empty list."""
        positive, negative = migrator._split_traits([])
        assert positive == []
        assert negative == []

    def test_split_traits_all_positive(self, migrator):
        """Test traits splitting with all positive traits."""
        positive, negative = migrator._split_traits(["勇敢", "誠実", "優しい"])
        assert len(positive) == 3
        assert len(negative) == 0

    def test_split_traits_all_negative(self, migrator):
        """Test traits splitting with all negative traits."""
        positive, negative = migrator._split_traits(["短気", "傲慢", "臆病"])
        assert len(positive) == 0
        assert len(negative) == 3

    def test_split_traits_mixed(self, migrator):
        """Test traits splitting with mixed traits."""
        positive, negative = migrator._split_traits(["勇敢", "短気", "誠実", "傲慢"])
        assert len(positive) == 2  # 勇敢, 誠実
        assert len(negative) == 2  # 短気, 傲慢

    def test_version_and_last_updated_in_output(
        self, migrator, legacy_character_minimal
    ):
        """Test that version and last_updated are set correctly."""
        result = migrator.migrate_character(legacy_character_minimal)
        book = result["character_book"]

        assert book["version"] == "0.1.0"
        assert book["last_updated"] != ""  # Should have current date


@pytest.mark.integration
class TestA24CharacterMigratorIntegration:
    """Integration tests for migration script."""

    def test_full_migration_workflow(self, migrator, legacy_character_full, tmp_path):
        """Test complete migration workflow from legacy to A24."""
        # Migrate
        result = migrator.migrate_character(legacy_character_full)

        # Verify structure completeness
        char = result["character_book"]["characters"]["main"][0]

        # All 5 layers should exist
        assert "layer1_psychology" in char["layers"]
        assert "layer2_physical" in char["layers"]
        assert "layer3_capabilities_skills" in char["layers"]
        assert "layer4_social_network" in char["layers"]
        assert "layer5_expression_behavior" in char["layers"]

        # All top-level sections should exist
        assert "narrative_notes" in char
        assert "llm_prompt_profile" in char
        assert "logging" in char
        assert "lite_profile_hint" in char
        assert "episode_snapshots" in char

        # Manual review items should be flagged
        assert len(migrator.manual_review_required) >= 2  # At least traits + psych models
