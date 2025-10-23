"""Domain.services.a28_template_loader_service
Where: Domain service for loading and processing A28 turning point templates.
What: Loads YAML templates, validates structure, and provides typed access.
Why: Ensures A28 templates are correctly loaded and validated before use.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.interfaces.logger_interface import ILogger, NullLogger


@dataclass
class A28TurningPointData:
    """A28 turning point data structure.

    Turning point structure data loaded from A28 template.
    """
    title: str
    timing: str
    trigger_event: str
    catalyst: str
    before_state: str
    transformation_moment: str
    after_state: str
    emotional_journey: list[dict[str, Any]]
    structural_function: dict[str, Any]


@dataclass
class A28SceneData:
    """A28 scene data structure."""
    scene_id: str
    scene_purpose: str
    act_position: str
    importance_rank: str
    estimated_words: int
    key_moments: list[str]
    emotional_design: dict[str, Any]
    dialogue_highlights: list[str] | None = None
    五感トリガー: list[dict[str, Any]] | None = None
    避けるべき表現: list[str] | None = None


@dataclass
class A28TemplateData:
    """A28 complete template data.

    Holds all data loaded from YAML template.
    """
    metadata: dict[str, Any]
    turning_point: A28TurningPointData
    five_elements_checklist: dict[str, Any]
    scenes: list[A28SceneData]
    emotion_tech_fusion: dict[str, Any] | None = None
    eighteen_step_mapping: dict[str, Any] | None = None
    post_apply_review: dict[str, Any] | None = None


class A28TemplateLoaderService:
    """A28 template loader service.

    Loads A28 template files in YAML format and converts them
    to type-safe data structures.
    """

    def __init__(self, logger: ILogger | None = None):
        """Initialize.

        Args:
            logger: Logger instance (Null Object pattern)
        """
        self.logger = logger if logger is not None else NullLogger()

    def load_template(self, template_path: Path) -> A28TemplateData:
        """Load template file.

        Args:
            template_path: Path to template YAML file

        Returns:
            A28TemplateData: Loaded template data

        Raises:
            FileNotFoundError: Template file does not exist
            yaml.YAMLError: YAML parsing error
            ValueError: Required fields are missing
        """
        if not template_path.exists():
            raise FileNotFoundError(f"A28 template not found: {template_path}")

        self.logger.debug(f"Loading A28 template from: {template_path}")

        try:
            with template_path.open("r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.logger.error(f"YAML parsing error: {e}")
            raise

        # Validate required fields
        self._validate_required_fields(raw_data)

        # Convert to data structure
        template_data = self._convert_to_template_data(raw_data)

        self.logger.info(f"A28 template loaded successfully: {template_data.metadata.get('pattern_type')}")
        return template_data

    def _validate_required_fields(self, data: dict[str, Any]) -> None:
        """Validate existence of required fields.

        Args:
            data: Loaded raw data

        Raises:
            ValueError: Required fields are missing
        """
        required_top_level = ["metadata", "turning_point", "five_elements_checklist", "scene_structure"]
        missing_fields = [field for field in required_top_level if field not in data]

        if missing_fields:
            raise ValueError(f"Missing required fields in A28 template: {missing_fields}")

        # Validate turning_point section
        tp = data["turning_point"]
        required_tp_fields = ["title", "timing", "trigger_event", "catalyst", "protagonist"]
        missing_tp_fields = [field for field in required_tp_fields if field not in tp]

        if missing_tp_fields:
            raise ValueError(f"Missing required fields in turning_point: {missing_tp_fields}")

        # Validate protagonist section
        prot = tp["protagonist"]
        required_prot_fields = ["before_state", "transformation_moment", "after_state"]
        missing_prot_fields = [field for field in required_prot_fields if field not in prot]

        if missing_prot_fields:
            raise ValueError(f"Missing required fields in protagonist: {missing_prot_fields}")

    def _convert_to_template_data(self, raw_data: dict[str, Any]) -> A28TemplateData:
        """Convert raw data to typed data structure.

        Args:
            raw_data: Raw data loaded from YAML

        Returns:
            A28TemplateData: Converted data
        """
        # Convert turning_point section
        tp_raw = raw_data["turning_point"]
        prot = tp_raw["protagonist"]

        turning_point = A28TurningPointData(
            title=tp_raw["title"],
            timing=tp_raw["timing"],
            trigger_event=tp_raw["trigger_event"],
            catalyst=tp_raw["catalyst"],
            before_state=prot["before_state"],
            transformation_moment=prot["transformation_moment"],
            after_state=prot["after_state"],
            emotional_journey=tp_raw.get("emotional_journey", []),
            structural_function=tp_raw.get("structural_function", {}),
        )

        # Convert scene_structure section
        scenes_raw = raw_data.get("scene_structure", {}).get("scenes", [])
        scenes = [
            A28SceneData(
                scene_id=scene["scene_id"],
                scene_purpose=scene["scene_purpose"],
                act_position=scene["act_position"],
                importance_rank=scene["importance_rank"],
                estimated_words=scene["estimated_words"],
                key_moments=scene.get("key_moments", []),
                emotional_design=scene.get("emotional_design", {}),
                dialogue_highlights=scene.get("dialogue_highlights"),
                五感トリガー=scene.get("五感トリガー"),
                避けるべき表現=scene.get("避けるべき表現"),
            )
            for scene in scenes_raw
        ]

        return A28TemplateData(
            metadata=raw_data.get("metadata", {}),
            turning_point=turning_point,
            five_elements_checklist=raw_data.get("five_elements_checklist", {}),
            scenes=scenes,
            emotion_tech_fusion=raw_data.get("emotion_tech_fusion"),
            eighteen_step_mapping=raw_data.get("eighteen_step_mapping"),
            post_apply_review=raw_data.get("post_apply_review"),
        )

    def load_default_turning_point_template(self) -> A28TemplateData:
        """Load default turning point template.

        Returns:
            A28TemplateData: Default template data
        """
        # Relative path from project root
        default_template = Path(__file__).parent.parent / "templates" / "a28_turning_point_template.yaml"
        return self.load_template(default_template)

    def generate_prompt_from_template(self, template_data: A28TemplateData) -> str:
        """Generate prompt from template data.

        Args:
            template_data: Template data

        Returns:
            str: Generated prompt string
        """
        prompt_parts = []

        # Header
        prompt_parts.append("# A28 転機型導入パターンによるエピソードプロット生成")
        prompt_parts.append(f"## パターンタイプ: {template_data.metadata.get('pattern_type')}")
        prompt_parts.append(f"## 参考作品: {template_data.metadata.get('reference_work')}")
        prompt_parts.append("")

        # Turning point structure
        tp = template_data.turning_point
        prompt_parts.append("## 転機構造")
        prompt_parts.append(f"### タイトル: {tp.title}")
        prompt_parts.append(f"### タイミング: {tp.timing}")
        prompt_parts.append(f"### トリガー: {tp.trigger_event}")
        prompt_parts.append(f"### 触媒: {tp.catalyst}")
        prompt_parts.append("")

        prompt_parts.append("### キャラクター変化")
        prompt_parts.append(f"**Before State:**\n{tp.before_state}")
        prompt_parts.append("")
        prompt_parts.append(f"**Transformation Moment:**\n{tp.transformation_moment}")
        prompt_parts.append("")
        prompt_parts.append(f"**After State:**\n{tp.after_state}")
        prompt_parts.append("")

        # Emotional journey
        if tp.emotional_journey:
            prompt_parts.append("### 感情の旅程")
            for journey in tp.emotional_journey:
                stage = journey.get("stage", "")
                level = journey.get("emotion_level", 0)
                desc = journey.get("description", "")
                prompt_parts.append(f"- **{stage}** (Level {level}): {desc}")
            prompt_parts.append("")

        # Scene composition
        prompt_parts.append("## シーン構成")
        for scene in template_data.scenes:
            prompt_parts.append(f"### {scene.scene_id}: {scene.scene_purpose}")
            prompt_parts.append(f"- **重要度**: {scene.importance_rank}")
            prompt_parts.append(f"- **推定文字数**: {scene.estimated_words}字")
            prompt_parts.append(f"- **幕位置**: {scene.act_position}")

            if scene.key_moments:
                prompt_parts.append("- **重要瞬間**:")
                for moment in scene.key_moments:
                    prompt_parts.append(f"  - {moment}")

            if scene.emotional_design:
                ed = scene.emotional_design
                prompt_parts.append("- **感情設計**:")
                if "starting_emotion" in ed:
                    prompt_parts.append(f"  - 開始: {ed['starting_emotion']} (Level {ed.get('starting_level', 'N/A')})")
                if "ending_emotion" in ed:
                    prompt_parts.append(f"  - 終了: {ed['ending_emotion']} (Level {ed.get('ending_level', 'N/A')})")

            prompt_parts.append("")

        # 5 elements checklist
        prompt_parts.append("## 5要素チェックリスト")
        checklist = template_data.five_elements_checklist
        for element_key, element_data in checklist.items():
            if isinstance(element_data, dict):
                target = element_data.get("target_scene", "N/A")
                rank = element_data.get("importance_rank", "N/A")
                prompt_parts.append(f"### {element_key} (対象: {target}, 重要度: {rank})")

                if "required_content" in element_data:
                    prompt_parts.append("**必須内容:**")
                    for content in element_data["required_content"]:
                        prompt_parts.append(f"- {content}")

                if "validation_criteria" in element_data:
                    prompt_parts.append("**検証基準:**")
                    for criteria in element_data["validation_criteria"]:
                        prompt_parts.append(f"- {criteria}")

                prompt_parts.append("")

        return "\n".join(prompt_parts)
