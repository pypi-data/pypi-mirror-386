"""ProgressiveWriteManagerの外部テンプレート読み込み機能テスト

Schema v2 テンプレート（18ステップ構成）の読み込みと基本挙動を検証する。

主要な検証項目:
1. write_step*.yamlテンプレートファイルの正常読み込み
2. テンプレート変数の適切な置換
3. 段階実行制御メッセージの挿入
4. STEP 0-17の全ステップテンプレート対応
5. テンプレート読み込み失敗時のフォールバック
"""

import copy
import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
import yaml

from noveler.domain.services.progressive_write_manager import ProgressiveWriteManager
from noveler.domain.services.progressive_write_runtime_deps import (
    ProgressiveWriteRuntimeDeps,
)


class TestProgressiveWriteManagerTemplateLoading:
    """外部テンプレート読み込み機能のテストクラス"""

    @pytest.fixture
    def temp_project_dir(self, tmp_path):
        """テスト用の一時プロジェクトディレクトリ"""
        return str(tmp_path)

    @pytest.fixture
    def runtime_deps(self):
        """ProgressiveWriteManager用の簡易依存バンドル"""
        return ProgressiveWriteRuntimeDeps()

    @pytest.fixture
    def templates_dir(self, tmp_path):
        """テスト用テンプレートディレクトリ"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        # 新しい階層構造に対応
        (templates_dir / "writing").mkdir()
        return templates_dir

    @pytest.fixture
    def sample_template_data(self):
        """Schema v2 準拠のサンプルテンプレートデータ"""
        return {
            "metadata": {
                "step_id": 0,
                "step_name": "スコープ定義",
                "phase": "structural_design",
                "version": "2.0.0",
                "last_updated": "2025-09-23",
                "author": "unit-test",
                "description": "エピソードの目的・範囲・文字数目標を明確に定義",
                "estimated_duration": "5-10分",
            },
            "llm_config": {
                "role_messages": {
                    "system": "出力は artifacts の仕様に従った YAML のみ。",
                    "user": "inputs / constraints / tasks を参照して必要事項を満たしてください。",
                }
            },
            "prompt": {
                "main_instruction": "目的は「エピソード{episode_number}のスコープ定義」です。inputs・constraints・tasks を満たし、artifacts の仕様どおりに YAML を出力してください。"
            },
            "inputs": {
                "files": [
                    {
                        "path": "{project_root}/20_プロット/話別プロット/ep{episode_number:03d}.yaml",
                        "required": True,
                        "description": "話別プロット",
                    }
                ],
                "variables": {
                    "episode_number": {"type": "int", "required": True},
                    "project_root": {"type": "path", "required": True},
                },
            },
            "constraints": {
                "hard_rules": [
                    "文字数基準: word_count_min >= 8000",
                    "視点統一ポリシーを宣言する",
                ],
                "soft_targets": ["山場の位置: 後半2/3"],
            },
            "tasks": {
                "bullets": [
                    "scope_definition.story_goal を定義する",
                    "scope_definition.reader_experience を定義する",
                ],
                "details": [
                    {
                        "name": "主要目標の設定",
                        "items": [
                            "物語目標・読者体験・キャラクター成長を1-2行で明記",
                        ],
                    }
                ],
            },
            "artifacts": {
                "format": "yaml",
                "path_template": "{project_root}/60_作業ファイル/EP{episode_number:03d}_step00.yaml",
                "required_fields": ["scope_definition", "constraints", "handover_to_next"],
                "example": "scope_definition:\n  story_goal: '主人公が○○を達成する'\nconstraints:\n  word_count_min: 8000\n"
            },
            "acceptance_criteria": {
                "checklist": ["scope_definition が定義されている"],
                "metrics": [
                    {
                        "name": "spec_completeness",
                        "target": ">= 1.0",
                        "method": "必須キー充足率",
                    }
                ],
            },
            "next": {
                "next_step_id": 1,
                "message_template": "次のステップは execute_writing_step episode_number={episode_number} step_id=1 で実行",
            },
            "variables": [
                "step_id",
                "step_name",
                "episode_number",
                "completed_steps",
                "total_steps",
                "phase",
            ],
            "control_settings": {
                "strict_single_step": True,
                "require_completion_confirm": True,
                "auto_advance_disabled": True,
                "batch_execution_blocked": True,
            },
        }

    @pytest.fixture
    def create_template_file(self, templates_dir, sample_template_data):
        """テンプレートファイルを作成するヘルパー"""
        def _create_file(step_id, step_slug, template_data=None):
            if template_data is None:
                template_data = copy.deepcopy(sample_template_data)

            # step_idをテンプレートデータに反映
            template_data["metadata"]["step_id"] = step_id
            try:
                next_step = step_id + 1 if isinstance(step_id, (int, float)) else step_id
            except TypeError:
                next_step = step_id
            template_data.setdefault("next", {})["next_step_id"] = next_step

            # ProgressiveWriteManagerと同じロジックでファイル名生成
            if float(step_id).is_integer():
                step_token = f"{int(step_id):02d}"
            else:
                step_token = str(step_id).replace(".", "_")
            filename = f"write_step{step_token}_{step_slug}.yaml"

            # 新しい階層構造に対応：writing/サブディレクトリに配置
            template_path = templates_dir / "writing" / filename
            with open(template_path, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, allow_unicode=True, default_flow_style=False)

            return template_path
        return _create_file

    @pytest.mark.spec("SPEC-PROMPT-001-external-templates")
    def test_template_file_loading_success(self, temp_project_dir, create_template_file, runtime_deps):
        """テンプレートファイルの正常読み込みテスト"""
        # セットアップ: テンプレートファイル作成
        create_template_file(0, "scope_definition")

        # テスト対象のインスタンス作成
        manager = ProgressiveWriteManager(temp_project_dir, 1, deps=runtime_deps)

        # テンプレート読み込み実行
        template_data = manager._load_prompt_template(0)

        # 検証: テンプレートデータが正しく読み込まれる
        assert template_data is not None
        assert template_data["metadata"]["step_id"] == 0
        assert template_data["metadata"]["step_name"] == "スコープ定義"
        assert template_data["metadata"]["phase"] == "structural_design"
        assert template_data["metadata"]["version"] == "2.0.0"
        assert "main_instruction" in template_data["prompt"]
        assert "llm_config" in template_data
        assert template_data["artifacts"]["format"] == "yaml"
        assert "control_settings" in template_data

    @pytest.mark.spec("SPEC-PROMPT-001-external-templates")
    def test_template_variable_substitution(self, temp_project_dir, create_template_file, runtime_deps):
        """テンプレート変数置換の正常動作テスト"""
        # セットアップ
        create_template_file(0, "scope_definition")
        manager = ProgressiveWriteManager(temp_project_dir, 1, deps=runtime_deps)

        # テンプレート読み込みと変数準備
        template_data = manager._load_prompt_template(0)
        current_task = manager._get_task_by_id(manager.tasks_config["tasks"], 0)
        variables = manager._prepare_template_variables(0, current_task)

        # 変数置換実行
        main_instruction = template_data["prompt"]["main_instruction"]
        replaced_instruction = manager._replace_variables(main_instruction, variables)

        # 検証: 変数が適切に置換されている
        assert "{step_id}" not in replaced_instruction
        assert "{step_name}" not in replaced_instruction
        assert "{episode_number}" not in replaced_instruction
        assert "{completed_steps}" not in replaced_instruction
        assert "{total_steps}" not in replaced_instruction
        assert "{phase}" not in replaced_instruction

        # 検証: 実際の値が挿入されている
        assert "エピソード1のスコープ定義" in replaced_instruction
        assert "inputs・constraints・tasks" in replaced_instruction

    @pytest.mark.spec("SPEC-PROMPT-001-external-templates")
    def test_llm_instruction_reflects_main_instruction(self, temp_project_dir, create_template_file, runtime_deps):
        """get_writing_tasksで main_instruction が反映されることを確認"""
        create_template_file(0, "scope_definition")
        manager = ProgressiveWriteManager(temp_project_dir, 1, deps=runtime_deps)

        result = manager.get_writing_tasks()
        llm_instruction = result["llm_instruction"]

        assert "エピソード1のスコープ定義" in llm_instruction
        assert "inputs・constraints・tasks" in llm_instruction
        assert "{episode_number}" not in llm_instruction
        assert "{step_id}" not in llm_instruction

    @pytest.mark.spec("SPEC-PROMPT-001-external-templates")
    def test_all_18_steps_template_support(self, temp_project_dir, create_template_file, runtime_deps):
        """18ステップ全てのテンプレート対応テスト"""
        # セットアップ: 全ステップのテンプレートファイル作成
        step_configs = [
            (0, "scope_definition"),
            (1, "chapter_purpose"),
            (2, "section_goals"),
            (2.5, "theme_uniqueness"),  # 小数点ステップ
            (3, "section_balance"),
            (4, "scene_beats"),
            (5, "logic_verification"),
            (6, "character_detail"),
            (7, "dialogue_design"),
            (8, "emotion_curve"),
            (9, "atmosphere_worldview"),
            (10, "foreshadow_placement"),
            (11, "first_draft"),
            (12, "style_adjustment"),
            (13, "description_enhancement"),
            (14, "readability_optimization"),
            (15, "quality_check"),
            (16, "reader_experience"),
            (17, "final_preparation")
        ]

        for step_id, step_slug in step_configs:
            create_template_file(step_id, step_slug)

        manager = ProgressiveWriteManager(temp_project_dir, 1, deps=runtime_deps)

        # 検証: 各ステップのテンプレートが読み込める
        for step_id, _ in step_configs:
            template_data = manager._load_prompt_template(step_id)
            assert template_data is not None, f"STEP {step_id}のテンプレート読み込み失敗"
            assert template_data["metadata"]["step_id"] == step_id

    @pytest.mark.spec("SPEC-PROMPT-001-external-templates")
    def test_template_file_not_found_fallback(self, temp_project_dir, runtime_deps):
        """テンプレートファイル未発見時のフォールバック動作テスト"""
        # テンプレートファイルを作成しない状態でテスト
        manager = ProgressiveWriteManager(temp_project_dir, 1, deps=runtime_deps)

        # テンプレート読み込み試行
        template_data = manager._load_prompt_template(0)

        # 検証: テンプレートファイルがない場合はNoneが返される
        assert template_data is None

        # 検証: get_writing_tasksでフォールバック動作
        result = manager.get_writing_tasks()

        # フォールバック時でも基本的なLLM指示は生成される
        assert "llm_instruction" in result
        assert len(result["llm_instruction"]) > 0
        assert "STEP 0" in result["llm_instruction"]

    @pytest.mark.spec("SPEC-PROMPT-001-external-templates")
    def test_template_file_format_error_handling(self, temp_project_dir, templates_dir, runtime_deps):
        """テンプレートファイル形式エラー時の処理テスト"""
        # セットアップ: 不正なYAMLファイル作成
        invalid_template_path = templates_dir / "write_step00_scope_definition.yaml"
        with open(invalid_template_path, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: content: [\n")  # 不正なYAML

        manager = ProgressiveWriteManager(temp_project_dir, 1, deps=runtime_deps)

        # テンプレート読み込み試行
        template_data = manager._load_prompt_template(0)

        # 検証: 形式エラー時はNoneが返される
        assert template_data is None

    @pytest.mark.spec("SPEC-PROMPT-001-external-templates")
    def test_decimal_step_id_template_loading(self, temp_project_dir, create_template_file, runtime_deps, sample_template_data):
        """小数点ステップIDのテンプレート読み込みテスト"""
        # セットアップ: STEP 2.5のテンプレート作成
        template_data = copy.deepcopy(sample_template_data)
        template_data["metadata"].update({"step_id": 2.5, "step_name": "テーマの独自性", "phase": "content_development"})
        template_data["prompt"]["main_instruction"] = "STEP {step_id}: {step_name} を Schema v2 で実行"
        create_template_file(2.5, "theme_uniqueness", template_data)

        manager = ProgressiveWriteManager(temp_project_dir, 1, deps=runtime_deps)

        # 小数点ステップのテンプレート読み込み
        template_data_loaded = manager._load_prompt_template(2.5)

        # 検証: 小数点ステップIDでも正常に読み込める
        assert template_data_loaded is not None
        assert template_data_loaded["metadata"]["step_id"] == 2.5
        assert template_data_loaded["metadata"]["step_name"] == "テーマの独自性"

    @pytest.mark.spec("SPEC-PROMPT-001-external-templates")
    def test_template_control_settings_application(self, temp_project_dir, create_template_file, runtime_deps, sample_template_data):
        """テンプレート制御設定の適用テスト"""
        # セットアップ: 制御設定を持つテンプレート作成
        template_data = copy.deepcopy(sample_template_data)
        template_data["metadata"].update({"step_id": 0, "step_name": "テスト"})
        template_data["prompt"]["main_instruction"] = "テスト用メインインストラクション"
        template_data["control_settings"].update({
            "strict_single_step": True,
            "require_completion_confirm": True,
            "auto_advance_disabled": True,
            "batch_execution_blocked": True,
        })
        create_template_file(0, "scope_definition", template_data)

        manager = ProgressiveWriteManager(temp_project_dir, 1, deps=runtime_deps)

        # テンプレート読み込み
        loaded_template = manager._load_prompt_template(0)

        # 検証: 制御設定が正しく読み込まれる
        control_settings = loaded_template["control_settings"]
        assert control_settings["strict_single_step"] is True
        assert control_settings["require_completion_confirm"] is True
        assert control_settings["auto_advance_disabled"] is True
        assert control_settings["batch_execution_blocked"] is True

    @pytest.mark.spec("SPEC-PROMPT-001-external-templates")
    def test_by_task_validation_pass_and_fail(self, temp_project_dir, create_template_file, runtime_deps, sample_template_data):
        """by_task 検収の自動バリデータを確認する"""
        template_data = copy.deepcopy(sample_template_data)
        template_data["metadata"].update({"step_id": 0, "step_name": "スコープ定義"})
        template_data.setdefault("artifacts", {}).update({"format": "yaml"})
        template_data.setdefault("control_settings", {}).update({
            "by_task": [
                {"id": "scope.story_goal", "field": "scope_definition.story_goal", "rule": "nonempty"},
                {"id": "constraints.word_count", "field": "constraints.word_count_min", "range": "8000-90000"},
            ]
        })
        template_data.setdefault("tasks", {}).setdefault("details", [
            {
                "name": "テスト",
                "items": [
                    {"id": "scope.story_goal", "text": "story goal"},
                    {"id": "constraints.word_count", "text": "word count"},
                ],
            }
        ])
        create_template_file(0, "scope_definition", template_data)

        manager = ProgressiveWriteManager(temp_project_dir, 1, deps=runtime_deps)
        loaded_template = manager._load_prompt_template(0)

        execution_result = {
            "content": yaml.safe_dump(
                {
                    "scope_definition": {"story_goal": "目標を達成する"},
                    "constraints": {"word_count_min": 9000, "pov_policy": "one_pov_per_scene"},
                    "handover_to_next": {"notes": "OK"},
                }
            ),
            "metadata": {"success_criteria_met": True},
        }

        validation = manager._apply_by_task_validation(loaded_template, execution_result)
        assert execution_result["metadata"]["success_criteria_met"] is True
        assert validation["success"] is True
        statuses = {item["id"]: item["status"] for item in validation["by_task"]}
        assert statuses["scope.story_goal"] == "pass"
        assert statuses["constraints.word_count"] == "pass"

        execution_result_fail = {
            "content": yaml.safe_dump(
                {
                    "scope_definition": {"story_goal": "目標を達成する"},
                    "constraints": {"word_count_min": 7000},
                }
            ),
            "metadata": {"success_criteria_met": True},
        }

        validation_fail = manager._apply_by_task_validation(loaded_template, execution_result_fail)
        assert execution_result_fail["metadata"]["success_criteria_met"] is False
        assert validation_fail["success"] is False
        statuses_fail = {item["id"]: item["status"] for item in validation_fail["by_task"]}
        assert statuses_fail["constraints.word_count"] == "fail"

    @pytest.mark.spec("SPEC-PROMPT-001-external-templates")
    def test_template_metadata_validation(self, temp_project_dir, create_template_file, runtime_deps):
        """テンプレートメタデータの検証テスト"""
        # セットアップ
        create_template_file(0, "scope_definition")
        manager = ProgressiveWriteManager(temp_project_dir, 1, deps=runtime_deps)

        # テンプレート読み込み
        template_data = manager._load_prompt_template(0)

        # 検証: 必須メタデータフィールドの存在
        metadata = template_data["metadata"]
        required_fields = [
            "step_id",
            "step_name",
            "phase",
            "version",
            "last_updated",
            "author",
            "description",
            "estimated_duration",
        ]

        for field in required_fields:
            assert field in metadata, f"テンプレートメタデータに必須フィールドが不足: {field}"

    @pytest.mark.spec("SPEC-PROMPT-001-external-templates")
    def test_get_writing_tasks_with_external_template_integration(self, temp_project_dir, create_template_file, runtime_deps):
        """get_writing_tasksでの外部テンプレート統合テスト"""
        # セットアップ
        create_template_file(0, "scope_definition")
        manager = ProgressiveWriteManager(temp_project_dir, 1, deps=runtime_deps)

        # get_writing_tasks実行
        result = manager.get_writing_tasks()

        # 検証: 外部テンプレートが統合されている
        llm_instruction = result["llm_instruction"]

        # 外部テンプレート由来の内容確認
        assert "エピソード1のスコープ定義" in llm_instruction
        assert "inputs・constraints・tasks" in llm_instruction
        assert "{episode_number}" not in llm_instruction

        # 検証: 基本的なレスポンス構造は維持されている
        assert result["episode_number"] == 1
        assert result["current_step"] == 0
        assert "current_task" in result
        assert "progress" in result

    @pytest.mark.spec("SPEC-PROMPT-001-external-templates")
    def test_template_directory_path_configuration(self, temp_project_dir, runtime_deps):
        """テンプレートディレクトリパス設定テスト"""
        manager = ProgressiveWriteManager(temp_project_dir, 1, deps=runtime_deps)

        # 検証: テンプレートディレクトリが正しく設定される
        expected_template_dir = Path(temp_project_dir) / "templates"
        assert manager.prompt_templates_dir == expected_template_dir

        # 検証: _get_step_slugメソッドの動作
        assert manager._get_step_slug(0) == "scope_definition"
        assert manager._get_step_slug(1) == "chapter_purpose"
        assert manager._get_step_slug(2.5) == "theme_uniqueness"
        assert manager._get_step_slug(17) == "final_preparation"


class TestTemplateFileNamingConvention:
    """テンプレートファイル命名規則のテストクラス"""

    @pytest.mark.spec("SPEC-PROMPT-001-external-templates")
    def test_write_command_template_naming(self):
        """writeコマンド用テンプレートの命名規則テスト"""
        from noveler.domain.services.progressive_write_manager import ProgressiveWriteManager
        from noveler.domain.services.progressive_write_runtime_deps import ProgressiveWriteRuntimeDeps

        # テスト用のダミーインスタンス
        manager = ProgressiveWriteManager(".", 1, deps=ProgressiveWriteRuntimeDeps())

        # 検証: write_step*形式の命名規則
        test_cases = [
            (0, "write_step00_scope_definition.yaml"),
            (1, "write_step01_chapter_purpose.yaml"),
            (2.5, "write_step2_5_theme_uniqueness.yaml"),
            (10, "write_step10_foreshadow_placement.yaml"),
            (17, "write_step17_final_preparation.yaml")
        ]

        for step_id, expected_filename in test_cases:
            step_slug = manager._get_step_slug(step_id)
            # ProgressiveWriteManagerと同じロジック
            if float(step_id).is_integer():
                step_token = f"{int(step_id):02d}"
            else:
                step_token = str(step_id).replace(".", "_")
            actual_filename = f"write_step{step_token}_{step_slug}.yaml"

            assert actual_filename == expected_filename, f"STEP {step_id}のファイル名が期待値と異なる"
