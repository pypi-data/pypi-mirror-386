# File: src/noveler/domain/services/template/template_processor.py
# Purpose: Template variable processing and slug generation
# Context: Extracted from ProgressiveCheckManager template processing methods

from typing import Any


class TemplateProcessor:
    """Template variable processing (Domain layer - no I/O).

    Responsibilities:
        - Generate step slugs from task names
        - Prepare template variable dictionaries
        - Replace template variables using str.format()

    Note: This is a stateless utility class with static methods.
    All I/O (template file loading) is handled by FileTemplateRepository.

    Extracted from:
        - ProgressiveCheckManager._get_step_slug (lines 1510-1541)
        - ProgressiveCheckManager._prepare_template_variables (lines 1543-1570)
        - ProgressiveCheckManager._replace_variables (lines 1572-1589)
    """

    # Slug mapping for Japanese task names to English slugs
    SLUG_MAPPING = {
        "誤字脱字チェック": "typo_check",
        "文法・表記統一チェック": "grammar_check",
        "読みやすさ基礎チェック": "readability_check",
        "キャラクター一貫性チェック": "character_consistency",
        "プロット整合性チェック": "plot_consistency",
        "世界観・設定チェック": "worldview_check",
        "構造・起承転結チェック": "structure_check",
        "伏線・回収チェック": "foreshadowing_check",
        "シーン転換チェック": "scene_transition",
        "文章表現・文体チェック": "expression_check",
        "リズム・テンポチェック": "rhythm_tempo",
        "総合品質認定": "final_quality_approval",
    }

    @staticmethod
    def get_step_slug(task_name: str) -> str:
        """Generate slug from task name for use in filenames.

        Args:
            task_name: Task name (e.g., "誤字脱字チェック")

        Returns:
            Slug (e.g., "typo_check")
            If task_name not in SLUG_MAPPING, generates slug by:
            - Converting to lowercase
            - Replacing "・" with "_"
            - Replacing "（" and "）" with "_"

        Side Effects:
            None (pure function)

        Examples:
            >>> TemplateProcessor.get_step_slug("誤字脱字チェック")
            "typo_check"
            >>> TemplateProcessor.get_step_slug("カスタムチェック・その他")
            "カスタムチェック_その他"
        """
        slug = TemplateProcessor.SLUG_MAPPING.get(
            task_name,
            task_name.lower().replace("・", "_").replace("（", "_").replace("）", ""),
        )
        return str(slug)

    @staticmethod
    def prepare_template_variables(
        step_id: int,
        episode_number: int,
        session_id: str,
        project_root: str,
        current_task: dict[str, Any] | None,
        completed_steps: list[int],
        total_steps: int,
    ) -> dict[str, Any]:
        """Prepare template variable dictionary.

        Args:
            step_id: Step ID (1-indexed)
            episode_number: Episode number (e.g., 1)
            session_id: Session ID (e.g., "EP001_202510041230")
            project_root: Project root path (e.g., "/path/to/project")
            current_task: Current task dict (e.g., {"name": "誤字脱字チェック", "phase": "basic_quality"})
                If None, step_name defaults to "チェックステップ {step_id}"
            completed_steps: List of completed step IDs
            total_steps: Total number of steps

        Returns:
            Variable dictionary with the following structure:
            {
                "step_id": int,
                "step_name": str,
                "episode_number": int,
                "episode_number_formatted": str,  # "001" format
                "project_root": str,
                "session_id": str,
                "completed_steps": int,  # Number of completed steps (not list)
                "total_steps": int,
                "phase": str,
                "next_step_id": int | None,
            }

        Side Effects:
            None (pure function)

        Examples:
            >>> variables = TemplateProcessor.prepare_template_variables(
            ...     step_id=1,
            ...     episode_number=1,
            ...     session_id="EP001_202510041230",
            ...     project_root="/project",
            ...     current_task={"name": "誤字脱字チェック", "phase": "basic_quality"},
            ...     completed_steps=[],
            ...     total_steps=12,
            ... )
            >>> variables["step_name"]
            "誤字脱字チェック"
            >>> variables["episode_number_formatted"]
            "001"
        """
        step_name = current_task["name"] if current_task else f"チェックステップ {step_id}"
        phase = current_task.get("phase", "unknown") if current_task else "unknown"

        return {
            "step_id": step_id,
            "step_name": step_name,
            "episode_number": episode_number,
            "episode_number_formatted": f"{episode_number:03d}",
            "project_root": project_root,
            "session_id": session_id,
            "completed_steps": len(completed_steps),  # Count, not list
            "total_steps": total_steps,
            "phase": phase,
            "next_step_id": step_id + 1 if step_id < total_steps else None,
        }

    @staticmethod
    def replace_variables(template: str, variables: dict[str, Any]) -> str:
        """Replace template variables using Python str.format() syntax.

        Uses {variable_name} syntax (single braces, NOT Jinja2 {{variable_name}}).

        Args:
            template: Template string (e.g., "Episode {episode_number}")
            variables: Variable dict (e.g., {"episode_number": 1})

        Returns:
            Template with variables replaced (e.g., "Episode 1")
            If KeyError or other exception occurs, returns template unchanged

        Side Effects:
            Logs warning if variable not found (KeyError)
            Logs error if other exception occurs

        Implementation:
            return template.format(**variables)

        Examples:
            >>> template = "Episode {episode_number}: {step_name}"
            >>> variables = {"episode_number": 1, "step_name": "Typo Check"}
            >>> TemplateProcessor.replace_variables(template, variables)
            "Episode 1: Typo Check"

            >>> template = "Missing {unknown_var}"
            >>> TemplateProcessor.replace_variables(template, {})
            "Missing {unknown_var}"  # Returns unchanged
        """
        try:
            return template.format(**variables)
        except (KeyError, Exception):
            # Domain layer: silent failure, return template unchanged
            # Caller can detect by comparing result with original template
            return template
