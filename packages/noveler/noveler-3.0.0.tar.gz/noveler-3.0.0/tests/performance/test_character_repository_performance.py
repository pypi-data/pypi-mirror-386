# File: tests/performance/test_character_repository_performance.py
# Purpose: Performance benchmarks for character repository operations
# Context: Phase 5 performance evaluation for A24 schema implementation

"""
Performance Tests for Character Repository

Measures performance of CharacterProfile operations and YamlCharacterRepository
to identify optimization needs.
"""

import time
from pathlib import Path
from typing import Any

import pytest
import yaml

from noveler.infrastructure.repositories.yaml_character_repository import YamlCharacterRepository


@pytest.fixture
def temp_character_file(tmp_path: Path) -> Path:
    """Create a temporary character file with multiple characters."""
    settings_dir = tmp_path / "30_設定集"
    settings_dir.mkdir(parents=True)
    char_file = settings_dir / "キャラクター.yaml"

    # Create a file with 20 characters (mix of new and legacy schema)
    characters: list[dict[str, Any]] = []

    # 10 new schema characters
    for i in range(10):
        characters.append({
            "character_id": f"char_new_{i}",
            "display_name": f"New Character {i}",
            "status": {"lifecycle": "active"},
            "layers": {
                "layer1_psychology": {
                    "role": "protagonist",
                    "traits_positive": ["勇敢", "誠実"],
                    "traits_negative": ["短気"],
                },
                "layer2_physical": {"appearance": {"height": "170cm"}},
                "layer3_capabilities_skills": {},
                "layer4_social_network": {},
                "layer5_expression_behavior": {},
            },
            "narrative_notes": {},
            "llm_prompt_profile": {},
            "logging": {},
            "lite_profile_hint": {},
            "episode_snapshots": [],
        })

    # 10 legacy schema characters
    for i in range(10):
        characters.append({
            "character_id": f"char_legacy_{i}",
            "display_name": f"Legacy Character {i}",
            "role": "supporting",
            "traits": ["優しい", "慎重"],
        })

    data = {
        "character_book": {
            "version": "0.1.0",
            "characters": {
                "main": characters[:5],
                "supporting": characters[5:15],
                "antagonists": characters[15:],
                "background": [],
            },
        }
    }

    with open(char_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)

    return tmp_path


@pytest.mark.performance
class TestCharacterRepositoryPerformance:
    """Performance benchmarks for character repository operations."""

    def test_find_all_performance(self, temp_character_file: Path):
        """Measure find_all_by_project performance."""
        repo = YamlCharacterRepository(temp_character_file)

        start_time = time.perf_counter()
        result = repo.find_all_by_project("test")
        end_time = time.perf_counter()

        elapsed = end_time - start_time
        print(f"\nfind_all_by_project took {elapsed:.4f}s for 20 characters")

        assert len(result) == 20
        assert elapsed < 0.5, f"Loading took {elapsed:.4f}s, may need optimization"

    def test_find_by_name_performance(self, temp_character_file: Path):
        """Measure find_by_name performance."""
        repo = YamlCharacterRepository(temp_character_file)

        start_time = time.perf_counter()
        result = repo.find_by_name("test", "New Character 5")
        end_time = time.perf_counter()

        elapsed = end_time - start_time
        print(f"\nfind_by_name took {elapsed:.4f}s")

        assert result is not None
        assert result.name == "New Character 5"
        assert elapsed < 0.5, f"Lookup took {elapsed:.4f}s, may need optimization"

    def test_multiple_find_by_name_calls(self, temp_character_file: Path):
        """Test performance of multiple find_by_name calls (cache impact)."""
        repo = YamlCharacterRepository(temp_character_file)

        # Measure time for 10 sequential lookups
        names = [f"New Character {i}" for i in range(10)]

        start_time = time.perf_counter()
        for name in names:
            result = repo.find_by_name("test", name)
            assert result is not None
        end_time = time.perf_counter()

        total_time = end_time - start_time

        # Report performance (no assertion, just measurement)
        print(f"\n10 sequential find_by_name calls took {total_time:.4f}s")
        print(f"Average per call: {total_time / 10:.4f}s")

        # Note: Without caching, each call reloads the entire file
        # With caching, this should be much faster

    def test_adapter_overhead(self, temp_character_file: Path):
        """Measure overhead of CharacterProfileAdapter for new schema."""
        repo = YamlCharacterRepository(temp_character_file)

        # Load all characters
        start_time = time.perf_counter()
        characters = repo.find_all_by_project("test")
        end_time = time.perf_counter()

        load_time = end_time - start_time

        # Count new vs legacy characters
        new_schema_count = sum(1 for c in characters if c.has_new_schema_data())
        legacy_count = len(characters) - new_schema_count

        print(f"\nLoaded {len(characters)} characters in {load_time:.4f}s")
        print(f"  New schema: {new_schema_count} characters")
        print(f"  Legacy: {legacy_count} characters")
        print(f"  Average per character: {load_time / len(characters):.5f}s")

        # Rough threshold: if loading takes > 100ms, optimization may be needed
        assert load_time < 1.0, f"Loading took {load_time:.4f}s, may need optimization"


@pytest.mark.performance
class TestCharacterProfileAccessorPerformance:
    """Performance benchmarks for CharacterProfile accessor methods."""

    def test_new_schema_accessor_performance(self, temp_character_file: Path):
        """Measure new schema accessor methods performance."""
        repo = YamlCharacterRepository(temp_character_file)
        characters = repo.find_all_by_project("test")

        # Find a new schema character
        new_char = next(c for c in characters if c.has_new_schema_data())

        # Measure accessor performance
        start_time = time.perf_counter()
        for _ in range(1000):  # Repeat 1000 times for measurable time
            _ = new_char.get_layer("layer1_psychology")
            _ = new_char.get_psychological_summary()
            _ = new_char.get_decision_flow()
            _ = new_char.get_llm_prompt_profile()
            _ = new_char.get_narrative_notes()
        end_time = time.perf_counter()

        elapsed = end_time - start_time
        per_access = elapsed / 1000
        print(f"\n1000 new schema accessor calls took {elapsed:.4f}s")
        print(f"Average per call: {per_access:.6f}s")

        assert elapsed < 1.0, f"Accessor overhead too high: {elapsed:.4f}s"

    def test_legacy_accessor_performance(self, temp_character_file: Path):
        """Measure legacy attribute access performance."""
        repo = YamlCharacterRepository(temp_character_file)
        characters = repo.find_all_by_project("test")

        # Find a legacy character
        legacy_char = next(c for c in characters if not c.has_new_schema_data())

        # Measure accessor performance
        start_time = time.perf_counter()
        for _ in range(1000):  # Repeat 1000 times for measurable time
            _ = legacy_char.attributes.get("role")
            _ = legacy_char.attributes.get("traits")
            _ = legacy_char.attributes.get("category")
        end_time = time.perf_counter()

        elapsed = end_time - start_time
        per_access = elapsed / 1000
        print(f"\n1000 legacy accessor calls took {elapsed:.4f}s")
        print(f"Average per call: {per_access:.6f}s")

        assert elapsed < 1.0, f"Accessor overhead too high: {elapsed:.4f}s"


@pytest.mark.performance
class TestCachingNeed:
    """Tests to determine if caching is needed."""

    def test_repeated_full_loads_without_cache(self, temp_character_file: Path):
        """Measure impact of repeated full file loads (current behavior)."""
        repo = YamlCharacterRepository(temp_character_file)

        # Simulate typical usage: multiple operations requiring character lookups
        operations = [
            ("find_by_name", "New Character 3"),
            ("find_by_name", "Legacy Character 2"),
            ("find_all", None),
            ("find_by_name", "New Character 7"),
            ("find_by_name", "New Character 3"),  # Duplicate lookup
        ]

        start_time = time.perf_counter()
        for op_type, arg in operations:
            if op_type == "find_by_name":
                repo.find_by_name("test", arg)
            else:
                repo.find_all_by_project("test")
        end_time = time.perf_counter()

        total_time = end_time - start_time
        print(f"\n{len(operations)} operations took {total_time:.4f}s without caching")

        # Decision threshold: if > 500ms for 5 operations, caching is beneficial
        if total_time > 0.5:
            print("RECOMMENDATION: Implement caching to improve performance")
        else:
            print("Current performance is acceptable, caching optional")

        # Store result for decision making (don't fail test)
        return total_time
