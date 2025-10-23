#!/usr/bin/env python3
# File: scripts/migration/convert_character_to_a24.py
# Purpose: Convert legacy character YAML files to A24 schema format
# Context: Phase 4 migration tool for A24 character schema implementation

"""
A24 Character Schema Migration Tool

Converts legacy character YAML files to the new A24 hierarchical schema format.
Handles automated field mapping and identifies fields requiring manual review.

Usage:
    python scripts/migration/convert_character_to_a24.py --input legacy.yaml --output new.yaml
    python scripts/migration/convert_character_to_a24.py --input legacy.yaml --dry-run
    python scripts/migration/convert_character_to_a24.py --input-dir ./old/ --output-dir ./new/
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class A24CharacterMigrator:
    """Migrates legacy character files to A24 schema format."""

    def __init__(self) -> None:
        self.warnings: list[str] = []
        self.manual_review_required: list[str] = []

    def migrate_character(self, legacy_data: dict[str, Any]) -> dict[str, Any]:
        """
        Migrate a single character from legacy format to A24 format.

        Args:
            legacy_data: Legacy character data dictionary

        Returns:
            A24-formatted character dictionary
        """
        self.warnings.clear()
        self.manual_review_required.clear()

        # Extract legacy character (assume single character in legacy format)
        legacy_char = self._extract_legacy_character(legacy_data)
        if not legacy_char:
            raise ValueError("No character data found in legacy file")

        # Build A24 character
        a24_char = self._build_a24_character(legacy_char)

        # Wrap in character_book structure
        return {
            "character_book": {
                "version": "0.1.0",
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "default_logging": {
                    "root": "<log_root>",
                    "log_file_pattern_by_character": "<log_root>/<character_id>/<YYYYMMDD>_<scene>.md",
                    "template_ref": "docs/log_templates/character_scene_log.md",
                },
                "characters": {
                    "main": [a24_char],
                    "supporting": [],
                    "antagonists": [],
                    "background": [],
                },
            }
        }

    def _extract_legacy_character(self, data: dict[str, Any]) -> dict[str, Any] | None:
        """Extract character data from legacy format."""
        # Try different legacy structures
        if "character" in data:
            return data["character"]
        if "characters" in data and isinstance(data["characters"], list):
            return data["characters"][0] if data["characters"] else None
        if "name" in data:  # Direct character format
            return data
        return None

    def _build_a24_character(self, legacy: dict[str, Any]) -> dict[str, Any]:
        """Build A24 character structure from legacy data."""
        name = legacy.get("name", "<unnamed>")
        character_id = self._generate_character_id(name)

        return {
            "character_id": character_id,
            "display_name": name,
            "status": {
                "lifecycle": "active",
                "last_reviewed": "",
                "reviewer": "",
            },
            "layers": {
                "layer1_psychology": self._migrate_layer1_psychology(legacy),
                "layer2_physical": self._migrate_layer2_physical(legacy),
                "layer3_capabilities_skills": self._migrate_layer3_capabilities(legacy),
                "layer4_social_network": self._migrate_layer4_social(legacy),
                "layer5_expression_behavior": self._migrate_layer5_expression(legacy),
            },
            "narrative_notes": {
                "foreshadowing_hooks": [],
                "unresolved_questions": [],
            },
            "llm_prompt_profile": self._build_llm_prompt_profile(),
            "logging": {
                "character_log_directory": f"<log_root>/{character_id}/",
                "guidance": "命名: <YYYYMMDD>_<scene>.md",
                "last_entry": "",
            },
            "lite_profile_hint": {
                "use_lite": False,
                "minimal_fields": {
                    "lite_scene_goal_copy": "",
                    "lite_values_copy": [],
                    "lite_speech_tone_copy": "",
                    "lite_banned_phrases_copy": [],
                },
            },
            "episode_snapshots": [],
        }

    def _migrate_layer1_psychology(self, legacy: dict[str, Any]) -> dict[str, Any]:
        """Migrate Layer 1: Psychology data."""
        # Handle traits split (CRITICAL - requires manual review)
        traits_positive, traits_negative = self._split_traits(legacy.get("traits", []))

        layer1 = {
            "role": legacy.get("role", ""),
            "hook_summary": legacy.get("hook_summary", ""),
            "values": legacy.get("values", []),
            "core_motivations": {
                "primary": legacy.get("motivation", ""),
                "secondary": [],
            },
            "enduring_fears": legacy.get("fears", []),
            "traumas": legacy.get("traumas", []),
            "psychological_models": self._build_psychological_models(),
            "traits_positive": traits_positive,
            "traits_negative": traits_negative,
            "emotional_patterns": {
                "likes": legacy.get("likes", []),
                "dislikes": legacy.get("dislikes", []),
                "momentary_fears": [],
            },
            "inner_conflicts": legacy.get("inner_conflicts", []),
            # New fields (A24 extended) – auto-generate templates from inner_conflicts
            "conflict_arcs": self._generate_conflict_arcs_template(
                legacy.get("inner_conflicts", [])
            ),
            "growth_vector": {
                "current_arc": "",
                "future_hook": "",
                "short_term_arc": "",
                "long_term_arc": "",
            },
        }

        return layer1

    def _migrate_layer2_physical(self, legacy: dict[str, Any]) -> dict[str, Any]:
        """Migrate Layer 2: Physical appearance data."""
        appearance = legacy.get("appearance", {})

        return {
            "appearance": {
                "height": appearance.get("height", ""),
                "build": appearance.get("build", ""),
                "hair": appearance.get("hair", ""),
                "eyes": appearance.get("eyes", ""),
            },
            "distinguishing_features": appearance.get("distinguishing_features", []),
            "attire": {
                "typical": appearance.get("attire", ""),
                "variants": [],
            },
            # New optional field for symbolism linking appearance to psychology
            "symbolic_features": [],
        }

    def _migrate_layer3_capabilities(self, legacy: dict[str, Any]) -> dict[str, Any]:
        """Migrate Layer 3: Capabilities and skills data."""
        return {
            "combat_skills": legacy.get("combat_skills", []),
            "non_combat_skills": legacy.get("non_combat_skills", []),
            "magical_abilities": legacy.get("magical_abilities", []),
            "technical_assets": {
                "tools": legacy.get("tools", []),
            },
            "limitations": self._migrate_limitations(legacy.get("limitations", [])),
        }

    def _migrate_limitations(self, legacy_limitations: list[Any]) -> list[dict[str, str]]:
        """
        Migrate limitations to A24 typed format (type + detail).

        Args:
            legacy_limitations: Legacy limitations list (strings or dicts)

        Returns:
            List of typed limitation dicts with 'type' and 'detail' fields
        """
        if not legacy_limitations:
            return []

        typed_limitations = []

        for item in legacy_limitations:
            # If already typed (has 'type' and 'detail'), keep as-is
            if isinstance(item, dict) and "type" in item and "detail" in item:
                typed_limitations.append(item)
                continue

            # Convert string to typed format with auto-detection
            if isinstance(item, str):
                limitation_type = self._detect_limitation_type(item)
                typed_limitations.append({
                    "type": limitation_type,
                    "detail": item,
                })
                self.warnings.append(
                    f"Auto-detected limitation type '{limitation_type}' for: {item[:50]}..."
                )
            elif isinstance(item, dict):
                # Handle dict without proper structure
                detail = item.get("detail", str(item))
                limitation_type = item.get("type") or self._detect_limitation_type(detail)
                typed_limitations.append({
                    "type": limitation_type,
                    "detail": detail,
                })

        return typed_limitations

    def _detect_limitation_type(self, text: str) -> str:
        """
        Auto-detect limitation type from text content.

        Supported types: resource, time, social, skill, ethics, law

        Args:
            text: Limitation text

        Returns:
            Detected type (defaults to "skill" if unknown)
        """
        text_lower = text.lower()

        # Resource-related keywords
        if any(keyword in text_lower for keyword in [
            "魔力", "mana", "スタミナ", "stamina", "体力", "energy",
            "金", "資金", "コスト", "cost", "消費", "リソース", "resource"
        ]):
            return "resource"

        # Time-related keywords
        if any(keyword in text_lower for keyword in [
            "時間", "time", "期限", "deadline", "夜", "night", "朝", "morning",
            "疲労", "fatigue", "長期", "長時間", "duration"
        ]):
            return "time"

        # Social-related keywords
        if any(keyword in text_lower for keyword in [
            "評判", "reputation", "関係", "relationship", "信頼", "trust",
            "地位", "status", "身分", "rank", "社会", "social", "人間関係"
        ]):
            return "social"

        # Ethics-related keywords
        if any(keyword in text_lower for keyword in [
            "倫理", "ethics", "道徳", "moral", "良心", "conscience",
            "正義", "justice", "殺せない", "cannot kill"
        ]):
            return "ethics"

        # Law-related keywords
        if any(keyword in text_lower for keyword in [
            "法", "law", "規則", "rule", "違反", "violation",
            "禁止", "forbidden", "制約", "restriction"
        ]):
            return "law"

        # Default to skill if no match
        return "skill"

    def _generate_conflict_arcs_template(
        self, inner_conflicts: list[Any]
    ) -> dict[str, list[dict[str, str]]]:
        """
        Generate conflict_arcs template from inner_conflicts.

        Converts legacy inner_conflicts to structured short_term/long_term arcs
        with trigger, manifestation, and resolution_direction fields.

        Args:
            inner_conflicts: Legacy inner conflicts list

        Returns:
            Conflict arcs dict with short_term and long_term lists
        """
        short_term: list[dict[str, str]] = []
        long_term: list[dict[str, str]] = []

        if not inner_conflicts:
            return {"short_term": short_term, "long_term": long_term}

        # Generate templates from first 2 conflicts (common case)
        for idx, conflict in enumerate(inner_conflicts[:2]):
            conflict_text = conflict if isinstance(conflict, str) else str(conflict)

            # Create short-term arc template
            short_term.append({
                "trigger": f"<Trigger for: {conflict_text[:40]}...>",
                "manifestation": f"<How conflict manifests: {conflict_text[:30]}...>",
                "resolution_direction": "<Short-term resolution approach>"
            })

            # First conflict also gets long-term arc
            if idx == 0:
                long_term.append({
                    "trigger": f"<Long-term trigger: {conflict_text[:40]}...>",
                    "manifestation": f"<Long-term manifestation: {conflict_text[:30]}...>",
                    "resolution_direction": "<Long-term growth direction>"
                })

        if inner_conflicts:
            self.manual_review_required.append(
                f"conflict_arcs: Generated {len(short_term)} short-term and "
                f"{len(long_term)} long-term arc templates from inner_conflicts. "
                "Review and customize placeholders."
            )

        return {"short_term": short_term, "long_term": long_term}

    def _migrate_layer4_social(self, legacy: dict[str, Any]) -> dict[str, Any]:
        """Migrate Layer 4: Social network data."""
        return {
            "affiliations": legacy.get("affiliations", []),
            "relationships": legacy.get("relationships", []),
            "social_position": {
                "public_image": legacy.get("public_image", ""),
                "hidden_value": "",
            },
        }

    def _migrate_layer5_expression(self, legacy: dict[str, Any]) -> dict[str, Any]:
        """Migrate Layer 5: Expression and behavior data."""
        speech = legacy.get("speech_profile", {})

        return {
            "speech_profile": {
                "baseline_tone": speech.get("baseline_tone", speech.get("tone", "")),
                "sentence_endings": speech.get("sentence_endings", {}),
                "personal_pronouns": speech.get("personal_pronouns", {}),
                "catchphrases": speech.get("catchphrases", {}),
                # New optional fields for situation-specific variation
                "modes": {},
                "voice_drift_rules": [],
            },
            "behavioral_patterns": {
                "work_style": legacy.get("work_style", ""),
                "coping_mechanisms": legacy.get("coping_mechanisms", []),
            },
        }

    def _split_traits(self, traits: list[str]) -> tuple[list[str], list[str]]:
        """
        Split traits into positive and negative lists.

        NOTE: This uses heuristic-based classification. Manual review is REQUIRED.
        """
        if not traits:
            return [], []

        # Heuristic classification based on common negative trait keywords
        negative_keywords = [
            "短気",
            "傲慢",
            "臆病",
            "不誠実",
            "怠惰",
            "残酷",
            "冷酷",
            "頑固",
            "疑い深い",
            "わがまま",
            "無責任",
            "不注意",
        ]

        traits_positive = []
        traits_negative = []

        for trait in traits:
            # Check if trait contains negative keywords
            is_negative = any(keyword in trait for keyword in negative_keywords)

            if is_negative:
                traits_negative.append(trait)
            else:
                traits_positive.append(trait)

        # Add warning if traits were split
        if traits_positive or traits_negative:
            self.manual_review_required.append(
                f"CRITICAL: Traits were auto-classified. MANUAL REVIEW REQUIRED!\n"
                f"  Positive: {traits_positive}\n"
                f"  Negative: {traits_negative}\n"
                f"  Original: {traits}"
            )

        return traits_positive, traits_negative

    def _build_psychological_models(self) -> dict[str, Any]:
        """
        Build psychological models structure (empty - requires manual input).
        """
        self.manual_review_required.append(
            "MANUAL INPUT REQUIRED: psychological_models section needs framework, type, and rationale"
        )

        return {
            "primary": {
                "framework": "",
                "type": "",
                "rationale": "",
            },
            "secondary": [],
            "psychological_exceptions": [],
            "summary_bullets": [],
            "decision_flow": {
                "decision_step_perception": "",
                "decision_step_evaluation": "",
                "decision_step_action": "",
                "decision_step_emotional_aftermath": "",
            },
        }

    def _build_llm_prompt_profile(self) -> dict[str, Any]:
        """
        Build LLM prompt profile structure (empty - requires manual input).
        """
        self.manual_review_required.append(
            "MANUAL INPUT REQUIRED: llm_prompt_profile section needs configuration"
        )

        return {
            "default_scene_goal": "",
            "inputs_template": {
                "scene_role_and_goal": "",
                "psych_summary": [],
                "emotional_state": "",
                "constraints": [],
                "deliberate_voice_drift": "",
                "output_format_mode": "",
                "response_style_hint": "",
            },
            "post_review_checklist": {
                "last_run": "",
                "reviewer": "",
                "items": {
                    "values_motivation_alignment": {"status": "pending", "notes": ""},
                    "speech_rule_compliance": {"status": "pending", "notes": ""},
                    "deliberate_voice_drift_alignment": {"status": "pending", "notes": ""},
                    "emotional_flow_alignment": {"status": "pending", "notes": ""},
                    # New checklist item to ensure decision flow appears in output
                    "decision_flow_trace_present": {"status": "pending", "notes": ""},
                },
                "summary": "",
            },
        }

    def _generate_character_id(self, name: str) -> str:
        """Generate character_id from display name."""
        # Simple conversion: remove spaces, lowercase, convert to ASCII-friendly
        char_id = name.strip().lower().replace(" ", "_")
        # For Japanese names, suggest manual review
        if any(ord(c) > 127 for c in char_id):
            self.warnings.append(
                f"Character ID '{char_id}' contains non-ASCII characters. "
                "Consider using romanized version (e.g., 'yamada_taro')"
            )
        return char_id

    def print_summary(self) -> None:
        """Print migration summary with warnings and manual review items."""
        if self.warnings:
            print("\n[WARNING]")
            for warning in self.warnings:
                print(f"  - {warning}")

        if self.manual_review_required:
            print("\n[MANUAL REVIEW REQUIRED]")
            for item in self.manual_review_required:
                print(f"  - {item}")


def main() -> int:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Convert legacy character YAML to A24 schema format"
    )
    parser.add_argument("--input", type=Path, help="Input legacy character YAML file")
    parser.add_argument("--output", type=Path, help="Output A24 character YAML file")
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="Input directory containing legacy character YAML files",
    )
    parser.add_argument(
        "--output-dir", type=Path, help="Output directory for A24 character YAML files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without writing output files",
    )

    args = parser.parse_args()

    # Validate arguments
    if not ((args.input and args.output) or (args.input_dir and args.output_dir)):
        parser.error(
            "Either --input/--output or --input-dir/--output-dir must be specified"
        )

    migrator = A24CharacterMigrator()

    # Single file mode
    if args.input:
        return migrate_single_file(migrator, args.input, args.output, args.dry_run)

    # Batch mode
    if args.input_dir:
        return migrate_directory(
            migrator, args.input_dir, args.output_dir, args.dry_run
        )

    return 0


def migrate_single_file(
    migrator: A24CharacterMigrator, input_path: Path, output_path: Path, dry_run: bool
) -> int:
    """Migrate a single character file."""
    try:
        print(f"Reading legacy file: {input_path}")
        with open(input_path, encoding="utf-8") as f:
            legacy_data = yaml.safe_load(f)

        print("Migrating to A24 format...")
        a24_data = migrator.migrate_character(legacy_data)

        if dry_run:
            print("\n✨ DRY RUN - Preview of migrated data:")
            print(yaml.dump(a24_data, allow_unicode=True, sort_keys=False))
        else:
            print(f"Writing A24 file: {output_path}")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(a24_data, f, allow_unicode=True, sort_keys=False)

        migrator.print_summary()
        print("\n[OK] Migration completed successfully!")
        return 0

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}", file=sys.stderr)
        return 1


def migrate_directory(
    migrator: A24CharacterMigrator,
    input_dir: Path,
    output_dir: Path,
    dry_run: bool,
) -> int:
    """Migrate all YAML files in a directory."""
    if not input_dir.is_dir():
        print(f"❌ Input directory not found: {input_dir}", file=sys.stderr)
        return 1

    yaml_files = list(input_dir.glob("*.yaml")) + list(input_dir.glob("*.yml"))
    if not yaml_files:
        print(f"❌ No YAML files found in: {input_dir}", file=sys.stderr)
        return 1

    print(f"Found {len(yaml_files)} YAML files to migrate\n")

    success_count = 0
    failed_files = []

    for yaml_file in yaml_files:
        output_file = output_dir / yaml_file.name
        print(f"Processing: {yaml_file.name}")

        try:
            with open(yaml_file, encoding="utf-8") as f:
                legacy_data = yaml.safe_load(f)

            a24_data = migrator.migrate_character(legacy_data)

            if not dry_run:
                output_dir.mkdir(parents=True, exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as f:
                    yaml.dump(a24_data, f, allow_unicode=True, sort_keys=False)

            migrator.print_summary()
            print(f"[OK] {yaml_file.name} migrated successfully\n")
            success_count += 1

        except Exception as e:
            print(f"❌ Failed to migrate {yaml_file.name}: {e}\n", file=sys.stderr)
            failed_files.append(yaml_file.name)

    # Summary
    print(f"\n{'='*60}")
    print(f"Migration Summary:")
    print(f"  Total files: {len(yaml_files)}")
    print(f"  Success: {success_count}")
    print(f"  Failed: {len(failed_files)}")

    if failed_files:
        print(f"\nFailed files:")
        for fname in failed_files:
            print(f"  - {fname}")
        return 1

    print("\n[OK] All migrations completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
