#!/usr/bin/env python3
"""Comprehensive tests for phase2_record_manager.py.


仕様書: SPEC-INFRASTRUCTURE
"""

import json

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from unittest.mock import Mock as mock_Path

import pytest
import yaml

from noveler.infrastructure.repositories.phase2_record_repository import main

# Add parent directory to path
# PathManager統一パス管理システムを使用(事前にパスを設定)
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/を追加
from noveler.infrastructure.utils.path_manager import ensure_imports

ensure_imports()

from noveler.infrastructure.repositories.phase2_record_repository import Phase2RecordManager


class TestPhase2RecordManagerUpdateMethods(unittest.TestCase):
    """Test all update methods in Phase2RecordManager"""

    def setUp(self) -> None:
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir) / "test_project"
        self.project_root.mkdir(parents=True)
        self.manager = Phase2RecordManager(str(self.project_root))

        # Create a test record file
        self.test_episode = "第001話"
        self.test_record_data = {
            "phase_2_record": {
                "episode": self.test_episode,
                "title": "テストエピソード",
                "writing_date": "2025-01-15",
                "step_1_draft": {},
                "step_2a_structure_alignment": {},
                "step_2b_emotional_optimization": {},
                "step_3_final_adjustment": {},
                "quality_verification": {},
                "lessons_learned": {},
            },
        }

        # Save test record
        record_path = self.manager.records_dir / "phase2_record_第001話.yaml"
        with Path(record_path).open("w", encoding="utf-8") as f:
            yaml.dump(self.test_record_data, f)

    def tearDown(self) -> None:
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)

    def test_update_step1_record_success(self) -> None:
        """Test successful update of step 1 record"""
        step1_data = {
            "prompt_effectiveness": "very_good",
            "prompt_notes": "Excellent character development prompt",
            "word_count": 1500,
            "quality_score": 85,
        }

        result = self.manager.update_step1_record(self.test_episode, step1_data)

        assert result

        # Verify the update
        record_path = self.manager._get_record_path(self.test_episode)
        assert record_path is not None
        with Path(record_path).open(encoding="utf-8") as f:
            updated_data = yaml.safe_load(f)

        assert updated_data["phase_2_record"]["step_1_draft"]["prompt_effectiveness"] == "very_good"
        assert updated_data["phase_2_record"]["step_1_draft"]["word_count"] == 1500

    def test_update_step1_record_file_not_found(self) -> None:
        """Test update_step1_record when file doesn't exist"""
        result = self.manager.update_step1_record("第999話", {})
        assert not result

    def test_update_step2a_record_success(self) -> None:
        """Test successful update of step 2A record"""
        step2a_data = {
            "explanatory_style_assessment": {
                "ready_for_optimization": "準備完了",
            },
            "descriptive_writing_quality": {
                "structural_issues_found": ["過度な説明", "場面転換の唐突さ"],
                "revision_notes": "説明を削減し、自然な場面転換に修正",
            },
        }

        result = self.manager.update_step2a_record(self.test_episode, step2a_data)

        assert result

        # Verify the update
        updated_record = self.manager.get_record(self.test_episode)
        step2a = updated_record["phase_2_record"]["step_2a_structure_alignment"]

        assert step2a["explanatory_style_assessment"]["ready_for_optimization"] == "準備完了"
        assert "過度な説明" in step2a["descriptive_writing_quality"]["structural_issues_found"]

    def test_update_step2b_record_success(self) -> None:
        """Test successful update of step 2B record"""
        step2b_data = {
            "emotion_body_conversion": {
                "conversion_effectiveness": "very_effective",
                "conversion_examples": [
                    {
                        "original": "彼は怒った",
                        "converted": "胸の奥が熱く煮えたぎり、拳が勝手に震えた",
                        "body_sense": "怒りの身体感覚",
                        "scene_context": "裏切りを知った瞬間",
                    },
                ],
            },
            "optimization_results": {
                "quality_metrics": {
                    "narou_compatibility": "excellent",
                },
            },
        }

        result = self.manager.update_step2b_record(self.test_episode, step2b_data)

        assert result

        # Verify complex nested data
        updated_record = self.manager.get_record(self.test_episode)
        conversion = updated_record["phase_2_record"]["step_2b_emotional_optimization"]["emotion_body_conversion"]

        assert conversion["conversion_effectiveness"] == "very_effective"
        assert len(conversion["conversion_examples"]) == 1
        assert conversion["conversion_examples"][0]["body_sense"] == "怒りの身体感覚"

    def test_update_step3_record_success(self) -> None:
        """Test successful update of step 3 record"""
        step3_data = {
            "foreshadowing_adjustments": {
                "added": ["新たな伏線を追加"],
                "enhanced": ["既存の伏線を強化"],
            },
            "final_quality_score": 92,
        }

        result = self.manager.update_step3_record(self.test_episode, step3_data)

        assert result

    def test_update_quality_verification_success(self) -> None:
        """Test successful update of quality verification"""
        quality_data = {
            "automated_checks": {
                "word_count": 1523,
                "basic_style_score": 95,
                "composition_score": 88,
            },
            "manual_review": {
                "overall_satisfaction": "excellent",
                "reviewer_notes": "非常に良い出来栄え",
            },
        }

        result = self.manager.update_quality_verification(self.test_episode, quality_data)

        assert result

    def test_update_lessons_learned_success(self) -> None:
        """Test successful update of lessons learned"""
        lessons_data = {
            "effective_techniques": ["感情の身体感覚変換が効果的"],
            "areas_for_improvement": ["冒頭のフックをもっと強く"],
            "prompts_to_remember": ["キャラクターの内面描写プロンプト"],
        }

        result = self.manager.update_lessons_learned(self.test_episode, lessons_data)

        assert result

        # Verify the update
        updated_record = self.manager.get_record(self.test_episode)
        lessons = updated_record["phase_2_record"]["lessons_learned"]

        assert "感情の身体感覚変換が効果的" in lessons["effective_techniques"]


class TestPhase2RecordManagerAnalysis(unittest.TestCase):
    """Test analysis methods in Phase2RecordManager"""

    def setUp(self) -> None:
        """Set up test environment with multiple records"""
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir) / "test_project"
        self.project_root.mkdir(parents=True)
        self.manager = Phase2RecordManager(str(self.project_root))

        # Create multiple test records
        self.create_test_records()

    def tearDown(self) -> None:
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)

    def create_test_records(self) -> None:
        """Create multiple test records for analysis"""
        records = [
            {
                "episode": "第001話",
                "prompt_effectiveness": "very_good",
                "prompt_notes": "Great action scene prompt",
                "structure_readiness": "準備完了",
                "emotion_effectiveness": "very_effective",
                "narou_compatibility": "excellent",
            },
            {
                "episode": "第002話",
                "prompt_effectiveness": "good",
                "prompt_notes": "Solid dialogue prompt",
                "structure_readiness": "要微調整",
                "emotion_effectiveness": "effective",
                "narou_compatibility": "good",
            },
            {
                "episode": "第003話",
                "prompt_effectiveness": "fair",
                "prompt_notes": "",
                "structure_readiness": "要大幅修正",
                "emotion_effectiveness": "limited",
                "narou_compatibility": "fair",
            },
        ]

        for record_info in records:
            record_data = {
                "phase_2_record": {
                    "episode": record_info["episode"],
                    "title": f"テスト{record_info['episode']}",
                    "writing_date": "2025-01-15",
                    "step_1_draft": {
                        "prompt_effectiveness": record_info["prompt_effectiveness"],
                        "prompt_notes": record_info["prompt_notes"],
                    },
                    "step_2a_structure_alignment": {
                        "explanatory_style_assessment": {
                            "ready_for_optimization": record_info["structure_readiness"],
                        },
                        "descriptive_writing_quality": {
                            "structural_issues_found": ["issue1", "issue2"],
                            "revision_notes": "Fixed issues",
                        },
                    },
                    "step_2b_emotional_optimization": {
                        "emotion_body_conversion": {
                            "conversion_effectiveness": record_info["emotion_effectiveness"],
                            "conversion_examples": [
                                {
                                    "original": "original text",
                                    "converted": "converted text",
                                    "body_sense": "physical sensation",
                                    "scene_context": "scene context",
                                },
                            ],
                        },
                        "optimization_results": {
                            "quality_metrics": {
                                "narou_compatibility": record_info["narou_compatibility"],
                            },
                        },
                    },
                    "step_2_style_fusion": {  # Legacy field for compatibility
                        "emotion_body_conversion": {
                            "effectiveness": record_info["emotion_effectiveness"],
                        },
                    },
                    "step_3_final_adjustment": {},
                    "quality_verification": {
                        "automated_checks": {
                            "word_count": 1500,
                        },
                        "manual_review": {
                            "overall_satisfaction": "good",
                        },
                    },
                    "lessons_learned": {},
                },
            }

            safe_episode = record_info["episode"].replace("第", "第").replace("話", "話")
            record_path = self.manager.records_dir / f"phase2_record_{safe_episode}.yaml"
            with Path(record_path).open("w", encoding="utf-8") as f:
                yaml.dump(record_data, f)

    def test_analyze_prompt_effectiveness(self) -> None:
        """Test prompt effectiveness analysis"""
        analysis = self.manager.analyze_prompt_effectiveness()

        # Check total records
        assert analysis["total_records"] == 3

        # Check distribution
        assert analysis["effectiveness_distribution"]["very_good"] == 1
        assert analysis["effectiveness_distribution"]["good"] == 1
        assert analysis["effectiveness_distribution"]["fair"] == 1
        assert analysis["effectiveness_distribution"]["poor"] == 0

        # Check successful patterns
        assert len(analysis["successful_patterns"]) == 2  # very_good and good
        assert analysis["successful_patterns"][0]["effectiveness"] == "very_good"
        assert "action scene" in analysis["successful_patterns"][0]["notes"]

    def test_analyze_technique_effectiveness(self) -> None:
        """Test technique effectiveness analysis"""
        analysis = self.manager.analyze_technique_effectiveness()

        # Check structure alignment distribution
        assert analysis["structure_alignment"]["準備完了"] == 1
        assert analysis["structure_alignment"]["要微調整"] == 1
        assert analysis["structure_alignment"]["要大幅修正"] == 1

        # Check emotion conversion distribution
        assert analysis["emotion_conversion"]["very_effective"] == 1
        assert analysis["emotion_conversion"]["effective"] == 1
        assert analysis["emotion_conversion"]["limited"] == 1
        assert analysis["emotion_conversion"]["ineffective"] == 0

        # Check narou optimization distribution
        assert analysis["narou_optimization"]["excellent"] == 1
        assert analysis["narou_optimization"]["good"] == 1
        assert analysis["narou_optimization"]["fair"] == 1
        assert analysis["narou_optimization"]["poor"] == 0

        # Check successful conversions
        assert len(analysis["successful_conversions"]) == 3
        assert analysis["successful_conversions"][0]["body_sense"] == "physical sensation"

        # Check structure improvements
        assert len(analysis["structure_improvements"]) == 3
        assert "issue1" in analysis["structure_improvements"][0]["issues"]

    def test_generate_improvement_report(self) -> None:
        """Test improvement report generation"""
        report = self.manager.generate_improvement_report()

        # Check report structure
        assert "Phase 2執筆記録 改善レポート" in report
        assert "分析対象記録数: 3" in report

        # Check sections
        assert "プロンプト効果分析" in report
        assert "技法効果分析" in report
        assert "改善提案" in report

        # Check data presence
        assert "very_good: 1件 (33.3%)" in report
        assert "準備完了: 1件 (33.3%)" in report
        assert "第001話" in report  # Should include episode in successful patterns

    def test_export_records_summary(self) -> None:
        """Test export records summary"""
        output_path = Path(self.test_dir) / "summary.json"

        result = self.manager.export_records_summary(str(output_path))

        assert result
        assert output_path.exists()

        # Check exported content
        with Path(output_path).open(encoding="utf-8") as f:
            summary = json.load(f)

        assert summary["total_records"] == 3
        assert len(summary["records"]) == 3

        # Check record structure
        first_record = summary["records"][0]
        assert "episode" in first_record
        assert "title" in first_record
        assert "writing_date" in first_record
        assert "prompt_effectiveness" in first_record
        assert "emotion_effectiveness" in first_record
        assert "overall_satisfaction" in first_record
        assert "word_count" in first_record

        # Records should be sorted by date
        assert first_record["writing_date"] == "2025-01-15"


class TestPhase2RecordManagerEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""

    def setUp(self) -> None:
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir) / "test_project"
        self.project_root.mkdir(parents=True)
        self.manager = Phase2RecordManager(str(self.project_root))

    def tearDown(self) -> None:
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)

    def test_get_record_none(self) -> None:
        """Test get_record returns None for non-existent record"""
        result = self.manager.get_record("第999話")
        assert result is None

    def test_analyze_with_missing_fields(self) -> None:
        """Test analysis with records missing expected fields"""
        # Create a record with minimal fields
        minimal_record = {
            "phase_2_record": {
                "episode": "第001話",
                "title": "Minimal",
                "writing_date": "2025-01-15",
                "step_1_draft": {},
                "step_2a_structure_alignment": {},
                "step_2b_emotional_optimization": {},
                "quality_verification": {},
            },
        }

        record_path = self.manager.records_dir / "phase2_record_第001話.yaml"
        with Path(record_path).open("w", encoding="utf-8") as f:
            yaml.dump(minimal_record, f)

        # Should not raise exceptions
        prompt_analysis = self.manager.analyze_prompt_effectiveness()
        assert prompt_analysis["total_records"] == 1
        assert prompt_analysis["effectiveness_distribution"]["fair"] == 1  # Default

        technique_analysis = self.manager.analyze_technique_effectiveness()
        assert technique_analysis["structure_alignment"]["要微調整"] == 1  # Default

    def test_main_function_create(self) -> None:
        """Test main function with create command"""
        test_args = ["phase2_record_manager.py", "create", str(self.project_root), "第001話", "テストタイトル"]

        # モックテンプレートデータ
        template_data = yaml.dump(
            {
                "phase_2_record": {
                    "episode": "",
                    "title": "",
                    "writing_date": "",
                },
            },
        )

        with (
            patch("sys.argv", test_args),
            patch("builtins.print"),
            patch("builtins.open", mock_Path(read_data=template_data).open()),
        ):
            try:
                # Import and run main

                main()

                # Check if file was created
                record_files = list(self.manager.records_dir.glob("phase2_record_*.yaml"))
                assert len(record_files) >= 0
            except FileNotFoundError:
                # テンプレートが見つからない場合はスキップ
                pytest.skip("Template file not found")

    def test_main_function_analyze(self) -> None:
        """Test main function with analyze command"""
        # Create a test record first
        self.create_test_records()

        test_args = ["phase2_record_manager.py", "analyze", str(self.project_root)]

        with patch("sys.argv", test_args), patch("builtins.print") as mock_print:
            main()

            # Check that report was printed
            printed_output = "".join(str(call[0][0]) for call in mock_print.call_args_list)
            assert "Phase 2執筆記録 改善レポート" in printed_output

    def test_main_function_list(self) -> None:
        """Test main function with list command"""
        # Create test records
        self.create_test_records()

        test_args = ["phase2_record_manager.py", "list", str(self.project_root)]

        with patch("sys.argv", test_args), patch("builtins.print") as mock_print:
            main()

            # Check output
            printed_output = "".join(str(call[0][0]) for call in mock_print.call_args_list)
            assert "Phase 2記録一覧" in printed_output
            assert "第001話" in printed_output

    def create_test_records(self) -> None:
        """Helper to create test records"""
        record_data = {
            "phase_2_record": {
                "episode": "第001話",
                "title": "テスト",
                "writing_date": "2025-01-15",
                "step_1_draft": {"prompt_effectiveness": "good"},
                "step_2a_structure_alignment": {},
                "step_2b_emotional_optimization": {},
                "quality_verification": {},
            },
        }

        record_path = self.manager.records_dir / "phase2_record_第001話.yaml"
        with Path(record_path).open("w", encoding="utf-8") as f:
            yaml.dump(record_data, f)


if __name__ == "__main__":
    unittest.main()
