"""ruamel.yaml 基盤のYAMLプロンプトリポジトリ実装
仕様: specs/integrated_writing_workflow.spec.md
"""

import asyncio
import io
from pathlib import Path
from typing import Any

import yaml
from ruamel.yaml import YAML

from noveler.domain.entities.a30_guide_content import A30GuideContent
from noveler.domain.repositories.yaml_prompt_repository import (
    TemplateLoadError,
    YamlGenerationError,
    YamlPromptRepository,
    YamlSaveError,
    YamlValidationError,
)
from noveler.domain.value_objects.writing_phase import WritingPhase
from noveler.domain.value_objects.yaml_prompt_content import YamlPromptContent, YamlPromptMetadata
from noveler.infrastructure.factories.a30_guide_service_factory import A30GuideServiceFactory


class RuamelYamlPromptRepository(YamlPromptRepository):
    """ruamel.yaml基盤のYAMLプロンプトリポジトリ実装

    yamllint完全準拠のYAML生成・検証・保存機能を提供
    """

    def __init__(self, guide_template_path: Path) -> None:
        """リポジトリ初期化

        Args:
            guide_template_path: A30執筆ガイドYAMLテンプレートパス
        """
        self.guide_template_path = guide_template_path
        self._guide_template_cache: dict[str, any] = {}
        self._yaml_processor = self._create_yaml_processor()

    def _create_yaml_processor(self) -> YAML:
        """ruamel.yaml プロセッサ作成"""
        yaml_processor = YAML()
        yaml_processor.indent(mapping=4, sequence=4, offset=2)
        yaml_processor.preserve_quotes = True
        yaml_processor.width = 4096
        yaml_processor.map_indent = 2
        yaml_processor.sequence_indent = 4
        return yaml_processor

    async def generate_stepwise_prompt(
        self, metadata: YamlPromptMetadata, custom_requirements: list[str]
    ) -> YamlPromptContent:
        """段階的執筆プロンプト生成"""
        try:
            # ガイドテンプレート読み込み
            guide_data: dict[str, Any] = await self.load_guide_template()

            # YAML構造化データ構築
            yaml_data: dict[str, Any] = self._build_yaml_structure(metadata, custom_requirements, guide_data)

            # ruamel.yaml でフォーマット出力
            yaml_string = self._format_with_ruamel(yaml_data)

            # 検証実行
            validation_result = await self.validate_yaml_format(yaml_string)

            return YamlPromptContent.create_from_yaml_string(
                yaml_content=yaml_string,
                metadata=metadata,
                custom_requirements=custom_requirements,
                validation_passed=validation_result.get("yamllint_passed", False),
            )

        except Exception as e:
            msg = f"YAML生成に失敗しました: {e!s}"
            raise YamlGenerationError(msg) from e

    def _build_yaml_structure(
        self, metadata: YamlPromptMetadata, custom_requirements: list[str], guide_data: dict[str, any]
    ) -> dict[str, any]:
        """YAML構造データ構築"""
        stepwise_system = guide_data.get("stepwise_writing_system", {})
        variables = guide_data.get("prompt_templates", {}).get("basic_writing_request", {}).get("variables", {})

        yaml_structure = {
            "metadata": {
                "title": metadata.title,
                "project": metadata.project,
                "episode_file": metadata.episode_file,
                "genre": metadata.genre,
                "word_count": metadata.word_count,
                "viewpoint": metadata.viewpoint,
                "viewpoint_character": metadata.viewpoint_character,
                "detail_level": metadata.detail_level,
                "methodology": metadata.methodology,
                "generated_at": metadata.generated_at,
            },
            "instructions": {
                "overview": "以下の5段階で小説を執筆してください。各段階を順次実行し、段階的に品質を向上させます。",
                "completion_rule": "各段階完了時に「■ Stage X 完了」と明記してください",
            },
            "required_files": {
                "description": "執筆前に必ず読み込むファイル",
                "files": [
                    {
                        "type": "plot",
                        "path": f"{metadata.project}/20_プロット/{metadata.episode_file}",
                        "priority": "mandatory",
                    },
                    {
                        "type": "world_setting",
                        "path": f"{metadata.project}/30_設定集/世界観.yaml",
                        "priority": "mandatory",
                    },
                    {
                        "type": "character_setting",
                        "path": f"{metadata.project}/30_設定集/キャラクター.yaml",
                        "priority": "mandatory",
                    },
                ],
            },
            "stages": self._build_stages_structure(stepwise_system, variables),
            "final_output": {
                "word_count": metadata.word_count,
                "viewpoint": f"{metadata.viewpoint}（{metadata.viewpoint_character}視点）",
                "genre": metadata.genre,
                "completion_instruction": "全段階を統合した完成原稿を出力してください",
            },
        }

        # カスタム要件追加
        if custom_requirements:
            yaml_structure["custom_requirements"] = {
                "description": "各段階で考慮すべき追加要件",
                "requirements": custom_requirements,
            }

        return yaml_structure

    def _build_stages_structure(self, stepwise_system: dict[str, any], variables: dict[str, any]) -> dict[str, any]:
        """段階構造データ構築"""
        stages = {}

        for stage_key, stage_data in stepwise_system.get("stages", {}).items():
            stage_info = {
                "name": stage_data.get("name", "未定義段階"),
                "objective": stage_data.get("objective", ""),
                "completion_marker": stage_data.get("completion_marker", f"■ {stage_data.get('name', 'Stage')} 完了"),
                "tasks": [],
            }

            # タスク情報構築
            for task in stage_data.get("tasks", []):
                task_info = {
                    "name": task.get("name", ""),
                    "details": task.get("details", ""),
                    "subtasks": task.get("subtasks", []),
                }

                # 特別タスクの処理
                self._process_special_tasks(task, task_info, variables)
                stage_info["tasks"].append(task_info)

            stages[stage_key] = stage_info

        return stages

    def _process_special_tasks(
        self, task: dict[str, any], task_info: dict[str, any], variables: dict[str, any]
    ) -> None:
        """特別タスクの処理"""
        task_id = task.get("id", "")

        if task_id == "expression_cleanup":
            task_info["forbidden_expressions"] = variables.get("forbidden_expressions", [])
        elif task_id == "recommended_expressions":
            task_info["recommended_expressions"] = variables.get("recommended_expressions", [])
        elif task_id == "format_rules":
            task_info["format_rules"] = task.get("rules", [])
        elif task_id == "narou_10_rules":
            task_info["narou_rules"] = task.get("rules", [])
        elif task_id == "opening_golden_rule":
            task_info["golden_rules"] = task.get("rules", [])

    def _format_with_ruamel(self, yaml_data: dict[str, any]) -> str:
        """ruamel.yaml でフォーマット"""
        stream = io.StringIO()
        self._yaml_processor.dump(yaml_data, stream)
        return stream.getvalue()

    async def save_with_validation(self, yaml_content: YamlPromptContent, output_path: Path) -> bool:
        """YAML プロンプト検証付き保存"""
        try:
            # 事前検証
            if not yaml_content.is_validated():
                validation_result = await self.validate_yaml_format(yaml_content.raw_yaml_content)
                if not validation_result.get("yamllint_passed", False):
                    msg = "YAML検証に失敗しました"
                    raise YamlValidationError(msg)

            # ファイル保存
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(yaml_content.raw_yaml_content, encoding="utf-8")

            return True

        except Exception as e:
            msg = f"YAML保存に失敗しました: {e!s}"
            raise YamlSaveError(msg) from e

    async def validate_yaml_format(self, yaml_content: str) -> dict[str, bool]:
        """YAML 形式検証"""
        result = {"syntax_valid": False, "yamllint_passed": False}

        try:
            # 1. YAML構文チェック
            yaml.safe_load(yaml_content)
            result["syntax_valid"] = True

            # 2. yamllint チェック（非同期実行）
            yamllint_result = await self._run_yamllint_async(yaml_content)
            result["yamllint_passed"] = yamllint_result

        except yaml.YAMLError:
            result["syntax_valid"] = False
        except Exception:
            # yamllint 実行失敗時は構文チェックのみ有効
            pass

        return result

    async def _run_yamllint_async(self, yaml_content: str) -> bool:
        """yamllint 非同期実行"""
        try:
            # 一時ファイル作成
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp_file:
                tmp_file.write(yaml_content)
                tmp_file_path = tmp_file.name

            # yamllint 非同期実行
            process = await asyncio.create_subprocess_exec(
                "yamllint", tmp_file_path, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            # 一時ファイル削除
            Path(tmp_file_path).unlink(missing_ok=True)

            return process.returncode == 0

        except Exception:
            return False  # yamllint 実行失敗時は False

    async def load_guide_template(self) -> dict[str, any]:
        """执筆ガイドテンプレート読み込み"""
        if self._guide_template_cache:
            return self._guide_template_cache

        try:
            if not self.guide_template_path.exists():
                msg = f"ガイドテンプレートが存在しません: {self.guide_template_path}"
                raise TemplateLoadError(msg)

            with open(self.guide_template_path, encoding="utf-8") as f:
                template_data: dict[str, Any] = yaml.safe_load(f)

            if not template_data:
                msg = "ガイドテンプレートが空です"
                raise TemplateLoadError(msg)

            # キャッシュに保存
            self._guide_template_cache = template_data
            return template_data

        except Exception as e:
            msg = f"ガイドテンプレート読み込みに失敗: {e!s}"
            raise TemplateLoadError(msg) from e

    async def load_guide_template_for_phase(self, phase: WritingPhase, project_name: str) -> dict[str, any]:
        """段階的A30ガイド読み込み機能統合版テンプレート読み込み

        Args:
            phase: 執筆フェーズ
            project_name: プロジェクト名

        Returns:
            dict[str, any]: 段階的読み込みされたガイドテンプレートデータ

        Raises:
            TemplateLoadError: テンプレート読み込み失敗時
        """
        try:
            # 段階的A30ガイド読み込み実行
            response = A30GuideServiceFactory.load_guide_for_phase(
                phase=phase,
                project_name=project_name,
                guide_root_path=self.guide_template_path.parent,
                use_configuration_service=True,
            )

            if not response.success or not response.guide_content:
                # フォールバック: 従来の単一テンプレート読み込み
                return await self.load_guide_template()

            # A30GuideContentから統合テンプレートデータを構築
            return self._build_integrated_template_data(response.guide_content)

        except Exception:
            # エラー時は従来の読み込み方式にフォールバック
            return await self.load_guide_template()

    def _build_integrated_template_data(self, guide_content: A30GuideContent) -> dict[str, any]:
        """A30GuideContentから統合テンプレートデータを構築

        Args:
            guide_content: 段階的読み込みされたA30ガイドコンテンツ

        Returns:
            dict[str, any]: 統合テンプレートデータ
        """
        # ベースとなるマスターガイドデータ
        template_data: dict[str, Any] = dict(guide_content.master_guide) if guide_content.master_guide else {}

        # 詳細ルールの統合（REFINEMENTフェーズで利用可能）
        if guide_content.detailed_rules:
            detailed_rules = guide_content.detailed_rules

            # 詳細ルールから追加のprompt_templatesを統合
            if "prompt_templates" in detailed_rules:
                if "prompt_templates" not in template_data:
                    template_data["prompt_templates"] = {}
                template_data["prompt_templates"].update(detailed_rules["prompt_templates"])

            # 詳細な段階システムの統合
            if "stepwise_writing_system" in detailed_rules:
                if "stepwise_writing_system" not in template_data:
                    template_data["stepwise_writing_system"] = {}
                template_data["stepwise_writing_system"].update(detailed_rules["stepwise_writing_system"])

        # 品質チェックリストの統合（REFINEMENTフェーズで利用可能）
        if guide_content.quality_checklist:
            quality_data: dict[str, Any] = guide_content.quality_checklist

            # チェックリストデータをtemplate_dataに追加
            template_data["quality_checklist"] = quality_data

            # チェックリスト情報をstepwise_writing_systemに統合
            if "checklist_items" in quality_data:
                if "stepwise_writing_system" not in template_data:
                    template_data["stepwise_writing_system"] = {}
                template_data["stepwise_writing_system"]["quality_checklist"] = quality_data["checklist_items"]

        # トラブルシューティングガイドの統合（TROUBLESHOOTINGフェーズで利用可能）
        if guide_content.troubleshooting_guide:
            template_data["troubleshooting_guide"] = guide_content.troubleshooting_guide

        # フェーズ情報の追加
        if "metadata" not in template_data:
            template_data["metadata"] = {}
        template_data["metadata"]["loading_phase"] = guide_content.phase.value
        template_data["metadata"]["content_types"] = guide_content.get_available_content_types()
        template_data["metadata"]["phase_complete"] = guide_content.is_complete_for_phase()

        return template_data

    async def generate_stepwise_prompt_with_phase(
        self, metadata: YamlPromptMetadata, custom_requirements: list[str], phase: WritingPhase
    ) -> YamlPromptContent:
        """フェーズ対応段階的執筆プロンプト生成

        Args:
            metadata: YAMLプロンプトメタデータ
            custom_requirements: カスタム要件
            phase: 執筆フェーズ

        Returns:
            YamlPromptContent: 段階的プロンプトコンテンツ
        """
        try:
            # フェーズに応じたガイドテンプレート読み込み
            guide_data: dict[str, Any] = await self.load_guide_template_for_phase(phase, metadata.project)

            # YAML構造化データ構築（フェーズ情報を考慮）
            yaml_data: dict[str, Any] = self._build_yaml_structure_with_phase(
                metadata, custom_requirements, guide_data, phase
            )

            # ruamel.yaml でフォーマット出力
            yaml_string = self._format_with_ruamel(yaml_data)

            # 検証実行
            validation_result = await self.validate_yaml_format(yaml_string)

            return YamlPromptContent.create_from_yaml_string(
                yaml_content=yaml_string,
                metadata=metadata,
                custom_requirements=custom_requirements,
                validation_passed=validation_result.get("yamllint_passed", False),
            )

        except Exception as e:
            msg = f"フェーズ対応YAML生成に失敗しました: {e!s}"
            raise YamlGenerationError(msg) from e

    def _build_yaml_structure_with_phase(
        self,
        metadata: YamlPromptMetadata,
        custom_requirements: list[str],
        guide_data: dict[str, any],
        phase: WritingPhase,
    ) -> dict[str, any]:
        """フェーズ情報を考慮したYAML構造データ構築

        Args:
            metadata: YAMLプロンプトメタデータ
            custom_requirements: カスタム要件
            guide_data: ガイドデータ
            phase: 執筆フェーズ

        Returns:
            dict[str, any]: フェーズ対応YAML構造データ
        """
        # ベース構造構築
        yaml_structure = self._build_yaml_structure(metadata, custom_requirements, guide_data)

        # フェーズ情報の追加
        yaml_structure["metadata"]["writing_phase"] = phase.value
        yaml_structure["metadata"]["phase_lightweight"] = phase.is_lightweight()

        # フェーズに応じたインストラクション調整
        if phase == WritingPhase.DRAFT:
            yaml_structure["instructions"]["phase_note"] = (
                "初稿フェーズ: 軽量・高速処理を重視し、基本構造の確立に集中してください"
            )
        elif phase == WritingPhase.REFINEMENT:
            yaml_structure["instructions"]["phase_note"] = (
                "仕上げフェーズ: 詳細ルールと品質チェックリストを活用し、完成度を高めてください"
            )
        elif phase == WritingPhase.TROUBLESHOOTING:
            yaml_structure["instructions"]["phase_note"] = (
                "トラブルシューティングフェーズ: 問題解決に特化した指導を提供します"
            )

        # フェーズ別の追加情報統合
        if phase == WritingPhase.REFINEMENT and "quality_checklist" in guide_data:
            yaml_structure["quality_checklist"] = guide_data["quality_checklist"]

        if phase == WritingPhase.TROUBLESHOOTING and "troubleshooting_guide" in guide_data:
            yaml_structure["troubleshooting_guide"] = guide_data["troubleshooting_guide"]

        return yaml_structure
