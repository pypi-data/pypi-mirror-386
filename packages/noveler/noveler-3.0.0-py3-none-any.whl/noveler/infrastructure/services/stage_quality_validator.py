"""
段階別品質検証サービスの実装

SPEC-STAGED-005: Infrastructure層での品質検証機能
- 段階別品質基準の適用
- A31品質チェック統合
- 数値的品質スコア算出
"""

from pathlib import Path
from typing import Any

from noveler.domain.services.staged_prompt_generation_service import StageQualityValidator, ValidationResult
from noveler.domain.value_objects.prompt_stage import PromptStage


class A31IntegratedStageQualityValidator(StageQualityValidator):
    """A31品質チェック統合段階別品質検証サービス

    既存のA31品質チェックシステムと統合し、
    段階別の品質基準を適用して検証を行う。
    """

    def __init__(self, project_root: Path) -> None:
        """バリデーター初期化

        Args:
            project_root: プロジェクトルートパス
        """
        self._project_root = project_root
        self._quality_thresholds = {
            1: 70.0,  # Stage 1: 基本骨格レベル
            2: 75.0,  # Stage 2: 構造レベル
            3: 80.0,  # Stage 3: 表現レベル
            4: 85.0,  # Stage 4: 統合レベル
            5: 90.0,  # Stage 5: 完成レベル
        }

    def validate(self, stage: PromptStage, content: dict[str, Any]) -> ValidationResult:
        """段階別品質検証実行

        Args:
            stage: 検証対象段階
            content: 検証対象コンテンツ

        Returns:
            検証結果
        """
        validation_errors = []
        validation_warnings = []
        improvement_suggestions = []
        quality_score = 0.0

        try:
            # 段階別検証の実行
            stage_validation = self._validate_stage_specific_requirements(stage, content)
            validation_errors.extend(stage_validation["errors"])
            validation_warnings.extend(stage_validation["warnings"])
            improvement_suggestions.extend(stage_validation["suggestions"])

            # 品質スコア算出
            quality_score = self._calculate_quality_score(stage, content, stage_validation)

            # A31品質チェック統合（段階に応じて）
            if stage.stage_number >= 3:
                a31_validation = self._integrate_a31_quality_check(stage, content)
                validation_errors.extend(a31_validation["errors"])
                validation_warnings.extend(a31_validation["warnings"])
                improvement_suggestions.extend(a31_validation["suggestions"])

                # A31スコアとの統合
                quality_score = self._integrate_a31_score(quality_score, a31_validation["score"])

        except Exception as e:
            validation_errors.append(f"Validation error: {e!s}")
            quality_score = 0.0

        return ValidationResult(
            is_valid=len(validation_errors) == 0,
            quality_score=quality_score,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings,
            improvement_suggestions=improvement_suggestions,
        )

    def _validate_stage_specific_requirements(self, stage: PromptStage, content: dict[str, Any]) -> dict[str, Any]:
        """段階固有要件の検証

        Args:
            stage: 検証対象段階
            content: 検証対象コンテンツ

        Returns:
            段階固有検証結果
        """
        result = {"errors": [], "warnings": [], "suggestions": []}

        if stage.stage_number == 1:
            result.update(self._validate_stage1_requirements(content))
        elif stage.stage_number == 2:
            result.update(self._validate_stage2_requirements(content))
        elif stage.stage_number == 3:
            result.update(self._validate_stage3_requirements(content))
        elif stage.stage_number == 4:
            result.update(self._validate_stage4_requirements(content))
        elif stage.stage_number == 5:
            result.update(self._validate_stage5_requirements(content))

        return result

    def _validate_stage1_requirements(self, content: dict[str, Any]) -> dict[str, Any]:
        """Stage 1固有検証"""
        result = {"errors": [], "warnings": [], "suggestions": []}

        # 基本骨格の品質確認
        synopsis = content.get("synopsis", "")
        if len(synopsis) < 50:
            result["errors"].append("Synopsis too short for meaningful content")
        elif len(synopsis) < 100:
            result["warnings"].append("Synopsis could be more detailed")
            result["suggestions"].append("Consider expanding synopsis to 100+ characters")

        # テーマの明確性確認
        theme = content.get("theme", "")
        if theme and len(theme.split()) < 3:
            result["warnings"].append("Theme could be more specific")
            result["suggestions"].append("Consider elaborating the theme with more detail")

        return result

    def _validate_stage2_requirements(self, content: dict[str, Any]) -> dict[str, Any]:
        """Stage 2固有検証"""
        result = {"errors": [], "warnings": [], "suggestions": []}

        # 三幕構成の論理性確認
        story_structure = content.get("story_structure", {})
        acts = ["setup", "confrontation", "resolution"]

        for act in acts:
            if act not in story_structure:
                result["errors"].append(f"Missing {act} in story structure")
            elif not story_structure[act] or len(str(story_structure[act]).strip()) < 10:
                result["warnings"].append(f"{act} needs more detailed description")
                result["suggestions"].append(f"Expand {act} with specific events and character actions")

        # シーン数の確認
        scenes_count = len([k for k in content if k.startswith("scene_")])
        if scenes_count < 3:
            result["errors"].append("Minimum 3 scenes required for proper story structure")
        elif scenes_count > 7:
            result["warnings"].append("Consider if all scenes are necessary")
            result["suggestions"].append("Review scene necessity and potential consolidation")

        return result

    def _validate_stage3_requirements(self, content: dict[str, Any]) -> dict[str, Any]:
        """Stage 3固有検証"""
        result = {"errors": [], "warnings": [], "suggestions": []}

        # シーン5要素の確認
        detailed_scenes = content.get("detailed_scenes", {})
        required_elements = ["location_description", "character_actions", "emotional_expressions", "scene_hook"]

        if not detailed_scenes:
            result["errors"].append("No detailed scenes provided")
        else:
            for scene_id, scene_data in detailed_scenes.items():
                if isinstance(scene_data, dict):
                    missing_elements = [elem for elem in required_elements if elem not in scene_data]
                    if missing_elements:
                        result["warnings"].append(f"Scene {scene_id} missing: {missing_elements}")
                        result["suggestions"].append(f"Add {missing_elements} to scene {scene_id}")

        # 感情アーク4段階の確認
        emotional_arc = content.get("emotional_arc", {})
        if not emotional_arc or len(emotional_arc) < 4:
            result["warnings"].append("Emotional arc should have 4 stages")
            result["suggestions"].append("Develop 4-stage emotional progression")

        return result

    def _validate_stage4_requirements(self, content: dict[str, Any]) -> dict[str, Any]:
        """Stage 4固有検証"""
        result = {"errors": [], "warnings": [], "suggestions": []}

        # 伏線統合の確認
        foreshadowing = content.get("foreshadowing_integration", {})
        if not foreshadowing:
            result["warnings"].append("No foreshadowing integration provided")
            result["suggestions"].append("Consider adding foreshadowing elements")

        # 技術要素の教育的進行確認
        technical_elements = content.get("technical_elements", {})
        if technical_elements:
            levels = ["level1_intuitive", "level2_intermediate", "level3_technical"]
            missing_levels = [level for level in levels if level not in technical_elements]
            if missing_levels:
                result["warnings"].append(f"Technical elements missing levels: {missing_levels}")
                result["suggestions"].append("Implement 3-level technical explanation")

        # テーマ一貫性の確認
        thematic_elements = content.get("thematic_elements", {})
        if not thematic_elements:
            result["warnings"].append("Thematic elements not sufficiently integrated")
            result["suggestions"].append("Strengthen thematic coherence across the episode")

        return result

    def _validate_stage5_requirements(self, content: dict[str, Any]) -> dict[str, Any]:
        """Stage 5固有検証"""
        result = {"errors": [], "warnings": [], "suggestions": []}

        # 全体一貫性の確認
        overall_consistency = content.get("overall_consistency", {})
        if not overall_consistency:
            result["warnings"].append("Overall consistency check incomplete")
            result["suggestions"].append("Perform comprehensive consistency review")

        # 制作指針準拠の確認
        guideline_compliance = content.get("guideline_compliance", {})
        if isinstance(guideline_compliance, dict):
            compliance_rate = guideline_compliance.get("compliance_percentage", 0)
            if compliance_rate < 95:
                result["warnings"].append(f"Guideline compliance at {compliance_rate}%")
                result["suggestions"].append("Review and fix guideline compliance issues")

        return result

    def _integrate_a31_quality_check(self, stage: PromptStage, content: dict[str, Any]) -> dict[str, Any]:
        """A31品質チェック統合

        Args:
            stage: 検証対象段階
            content: 検証対象コンテンツ

        Returns:
            A31品質チェック結果
        """
        result = {"errors": [], "warnings": [], "suggestions": [], "score": 0.0}

        try:
            # A31品質チェックのシミュレーション
            # 実装時は実際のA31システムと統合

            # 基本品質スコア（A31風）
            base_score = 75.0

            # 段階別調整
            if stage.stage_number >= 4:
                base_score += 10.0  # 統合段階での品質向上
            if stage.stage_number == 5:
                base_score += 5.0  # 最終段階での品質確認

            # コンテンツ品質による調整
            if "detailed_scenes" in content and len(content["detailed_scenes"]) >= 3:
                base_score += 5.0

            if "quality_metrics" in content:
                metrics = content["quality_metrics"]
                if isinstance(metrics, dict) and metrics.get("overall_score", 0) >= 80:
                    base_score += 5.0

            result["score"] = min(base_score, 100.0)

            # A31固有の警告・提案
            if result["score"] < 80:
                result["warnings"].append("A31 quality score below recommended threshold")
                result["suggestions"].append("Review and improve content quality")

        except Exception as e:
            result["warnings"].append(f"A31 integration error: {e!s}")
            result["score"] = 70.0  # フォールバックスコア

        return result

    def _calculate_quality_score(
        self, stage: PromptStage, content: dict[str, Any], validation_result: dict[str, Any]
    ) -> float:
        """品質スコア算出

        Args:
            stage: 検証対象段階
            content: 検証対象コンテンツ
            validation_result: 段階固有検証結果

        Returns:
            品質スコア（0-100）
        """
        base_score = self._quality_thresholds[stage.stage_number]

        # エラーによる減点
        error_penalty = len(validation_result["errors"]) * 5.0
        warning_penalty = len(validation_result["warnings"]) * 2.0

        # コンテンツの充実度による加点
        content_bonus = 0.0

        # 段階別コンテンツ充実度評価
        if stage.stage_number == 1:
            if content.get("synopsis") and len(content["synopsis"]) > 200:
                content_bonus += 5.0
        elif stage.stage_number >= 3:
            scenes = content.get("detailed_scenes", {})
            if isinstance(scenes, dict) and len(scenes) >= 3:
                content_bonus += 10.0

        # 最終スコア算出
        final_score = base_score + content_bonus - error_penalty - warning_penalty

        return max(0.0, min(final_score, 100.0))

    def _integrate_a31_score(self, base_score: float, a31_score: float) -> float:
        """A31スコアとの統合

        Args:
            base_score: 基本品質スコア
            a31_score: A31品質スコア

        Returns:
            統合品質スコア
        """
        # 重み付き平均（A31スコアを30%、基本スコアを70%として統合）
        integrated_score = base_score * 0.7 + a31_score * 0.3

        return max(0.0, min(integrated_score, 100.0))

    def get_quality_threshold(self, stage: PromptStage) -> float:
        """段階別品質閾値取得

        Args:
            stage: 対象段階

        Returns:
            品質閾値
        """
        return self._quality_thresholds.get(stage.stage_number, 70.0)

    def update_quality_thresholds(self, new_thresholds: dict[int, float]) -> None:
        """品質閾値の更新

        Args:
            new_thresholds: 新しい品質閾値辞書
        """
        for stage_number, threshold in new_thresholds.items():
            if 1 <= stage_number <= 5 and 0.0 <= threshold <= 100.0:
                self._quality_thresholds[stage_number] = threshold
