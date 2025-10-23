"""
段階別プロンプトテンプレートリポジトリの実装

SPEC-STAGED-004: Infrastructure層での段階別テンプレート管理
- YAMLファイルベースのテンプレート管理
- 段階別テンプレートの読み込み・検証
- CommonPathService統合
"""

from pathlib import Path
from typing import Any

import yaml

from noveler.domain.services.staged_prompt_generation_service import StagedPromptTemplateRepository
from noveler.domain.value_objects.prompt_stage import PromptStage


class YamlStagedPromptTemplateRepository(StagedPromptTemplateRepository):
    """YAML形式での段階別プロンプトテンプレートリポジトリ実装

    A24段階的ワークフローガイドに基づいた軽量テンプレートを
    段階ごとに管理し、プロンプト生成に提供する。
    """

    def __init__(self, template_directory: Path, logger_service=None, console_service=None) -> None:
        """リポジトリの初期化

        Args:
            template_directory: テンプレートディレクトリパス
        """
        self._template_directory = template_directory
        self._template_cache: dict[int, str] = {}
        self._context_keys_cache: dict[int, list[str]] = {}

        if not template_directory.exists():
            msg = f"Template directory does not exist: {template_directory}"
            raise ValueError(msg)

        self.logger_service = logger_service
        self.console_service = console_service
    def find_template_by_stage(self, stage: PromptStage) -> str | None:
        """段階別テンプレート取得

        Args:
            stage: 対象段階

        Returns:
            テンプレート文字列（見つからない場合None）
        """
        stage_number = stage.stage_number

        # キャッシュから取得
        if stage_number in self._template_cache:
            return self._template_cache[stage_number]

        # 段階別テンプレートファイルの読み込み
        template_file_patterns = [
            f"A24_stage{stage_number}_{stage.stage_name.replace('・', '_')}テンプレート.yaml",
            f"stage{stage_number}_{stage.stage_name.replace('・', '_')}テンプレート.yaml",
            f"stage{stage_number}_template.yaml",
            f"stage_{stage_number}.yaml",
        ]

        for pattern in template_file_patterns:
            template_file = self._template_directory / pattern
            if template_file.exists():
                try:
                    template_content = self._load_template_file(template_file)
                    if template_content:
                        self._template_cache[stage_number] = template_content
                        return template_content
                except Exception as e:
                    # ログ出力を想定（実装ではloggerを使用）
                    self.console_service.print(f"Warning: Failed to load template {template_file}: {e}")
                    continue

        return None

    def get_template_context_keys(self, stage: PromptStage) -> list[str]:
        """テンプレート必須コンテキストキー取得

        Args:
            stage: 対象段階

        Returns:
            必須コンテキストキーのリスト
        """
        stage_number = stage.stage_number

        # キャッシュから取得
        if stage_number in self._context_keys_cache:
            return self._context_keys_cache[stage_number]

        # 基本必須キー（共通）
        base_keys = ["episode_number", "project_name"]

        # 段階固有の必須キー（Stage5を除去、プロット作成はStage1-4まで）
        stage_specific_keys = {
            1: ["title", "chapter", "theme", "purpose", "synopsis"],
            2: ["story_structure", "chapter_plot"],
            3: ["detailed_scenes", "character_details", "emotional_arc"],
            4: ["foreshadowing_data", "technical_elements", "thematic_elements"],
        }

        all_keys = base_keys + stage_specific_keys.get(stage_number, [])
        self._context_keys_cache[stage_number] = all_keys

        return all_keys

    def _load_template_file(self, template_file: Path) -> str | None:
        """テンプレートファイルの読み込み

        Args:
            template_file: テンプレートファイルパス

        Returns:
            テンプレート文字列（失敗時None）
        """
        try:
            with open(template_file, encoding="utf-8") as f:
                template_data: dict[str, Any] = yaml.safe_load(f)

            # YAMLテンプレートから文字列テンプレートを生成
            return self._convert_yaml_to_template_string(template_data)

        except Exception as e:
            self.console_service.print(f"Error loading template file {template_file}: {e}")
            return None

    def _convert_yaml_to_template_string(self, template_data: dict[str, Any]) -> str:
        """YAMLデータからテンプレート文字列を生成

        Args:
            template_data: YAMLから読み込んだデータ

        Returns:
            テンプレート文字列
        """
        # 段階的プロンプト生成用のテンプレート文字列を構築
        template_sections = []

        # ヘッダー部分
        template_sections.append("# 段階的プロンプト生成テンプレート")
        template_sections.append("")

        # 基本情報セクション
        if "episode_number" in template_data or "{episode_number}" in str(template_data):
            template_sections.append("## エピソード情報")
            template_sections.append("- エピソード番号: {episode_number}")
            template_sections.append("- プロジェクト名: {project_name}")
            template_sections.append("")

        # 段階固有セクション
        if "stage_info" in str(template_data):
            template_sections.append("## 段階情報")
            template_sections.append("- 現在段階: {stage_info[current_stage]}")
            template_sections.append("- 段階名: {stage_info[stage_name]}")
            template_sections.append("- 推定時間: {stage_info[estimated_duration]}分")
            template_sections.append("")

        # YAMLデータの主要部分をテンプレート化
        for key in template_data:
            if key not in ["stage_progress", "completion_check"]:
                template_sections.append(f"## {key}")
                template_sections.append(f"{{{key}}}")
                template_sections.append("")

        return "\n".join(template_sections)

    def reload_templates(self) -> None:
        """テンプレートキャッシュの再読み込み"""
        self._template_cache.clear()
        self._context_keys_cache.clear()

    def get_available_stages(self) -> list[int]:
        """利用可能な段階番号のリスト取得

        Returns:
            利用可能な段階番号のリスト
        """
        available_stages = []

        for stage_number in range(1, 5):  # Stage1-4まで
            stage = PromptStage.STAGE_1  # 仮の段階（実際には段階番号で判定）
            if stage_number == 2:
                stage = PromptStage.STAGE_2
            elif stage_number == 3:
                stage = PromptStage.STAGE_3
            elif stage_number == 4:
                stage = PromptStage.STAGE_4

            if self.find_template_by_stage(stage) is not None:
                available_stages.append(stage_number)

        return available_stages

    def validate_template_integrity(self) -> dict[str, Any]:
        """テンプレートの整合性検証

        Returns:
            検証結果辞書
        """
        validation_results = {"is_valid": True, "missing_stages": [], "invalid_templates": [], "warnings": []}

        # 各段階のテンプレート存在確認（Stage1-4まで）
        for stage_number in range(1, 5):
            try:
                from noveler.domain.value_objects.prompt_stage import get_stage_by_number

                stage = get_stage_by_number(stage_number)
                template = self.find_template_by_stage(stage)

                if template is None:
                    validation_results["missing_stages"].append(stage_number)
                    validation_results["is_valid"] = False

            except Exception as e:
                validation_results["invalid_templates"].append({"stage": stage_number, "error": str(e)})
                validation_results["is_valid"] = False

        # 警告の生成
        if len(validation_results["missing_stages"]) > 0:
            validation_results["warnings"].append(
                f"Missing templates for stages: {validation_results['missing_stages']}"
            )

        return validation_results
