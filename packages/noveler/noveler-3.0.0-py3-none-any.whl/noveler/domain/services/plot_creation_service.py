"""Domain.services.plot_creation_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

from noveler.domain.value_objects.domain_message import DomainMessage

"プロット作成ドメインサービス\n\nプロット作成のビジネスロジックを調整するドメインサービス\n複数のエンティティとリポジトリを組み合わせてワークフローを実行\n"
import contextlib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import yaml

from collections.abc import Mapping

from noveler.domain.entities.plot_workflow import PlotWorkflow
from noveler.domain.services.plot_merge_service import PlotMergeService
from noveler.domain.services.plot_validation_service import PlotValidationService
from noveler.domain.value_objects.merge_strategy import MergeStrategy
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

if TYPE_CHECKING:
    from noveler.domain.entities.plot_creation_task import PlotCreationTask
    from noveler.domain.value_objects.validation_result import ValidationResult
JST = ProjectTimezone.jst().timezone


@dataclass(frozen=True)
class PlotCreationResult:
    """プロット作成結果"""

    success: bool
    created_files: list[str]
    error_message: str = ""
    conflict_files: list[str] = field(default_factory=list)
    validation_result: ValidationResult | None = None
    messages: list[DomainMessage] = field(default_factory=list)


class PlotCreationService:
    """プロット作成ドメインサービス"""

    def __init__(
        self,
        project_file_repository: object,
        template_repository: object,
        plot_merge_service: object = None,
        plot_validation_service: object = None,
    ) -> None:
        """Args:
        project_file_repository: プロジェクトファイルリポジトリ
        template_repository: テンプレートリポジトリ
        plot_merge_service: プロットマージサービス(オプション)
        plot_validation_service: プロット検証サービス(オプション)
        """
        self.project_file_repo = project_file_repository
        self.template_repo = template_repository
        self.plot_merge_service = plot_merge_service or PlotMergeService()
        self.plot_validation_service = plot_validation_service or PlotValidationService()

    def execute_plot_creation(self, task: PlotCreationTask, auto_confirm: bool = False) -> PlotCreationResult:
        """プロット作成タスクを実行

        Args:
            task: プロット作成タスク
            auto_confirm: 自動確認(既存ファイル上書き等)。指定がない場合はFalse。

        Returns:
            PlotCreationResult: 作成結果
        """
        messages: list[DomainMessage] = []
        try:
            task.start_execution()
            workflow = PlotWorkflow(task.project_root)
            (can_execute, prerequisites_results) = workflow.can_execute_stage(
                task.stage_type, self.project_file_repo, **task.parameters
            )
            if not can_execute:
                error_msg = self._build_prerequisites_error_message(prerequisites_results)
                task.fail_execution(f"前提条件を満たしていません: {error_msg}")
                messages.append(
                    DomainMessage(
                        level="error",
                        message="プロット作成前提条件を満たしていません",
                        details={
                            "missing_prerequisites": error_msg,
                        },
                    )
                )
                return PlotCreationResult(
                    success=False,
                    created_files=[],
                    error_message=error_msg,
                    messages=messages,
                )
            target_stage = workflow.get_stage_by_type(task.stage_type)
            output_path = task.generate_output_path()
            has_conflicts = target_stage.has_output_conflicts(self.project_file_repo, **task.parameters)
            if has_conflicts and (not auto_confirm):
                messages.append(
                    DomainMessage(
                        level="warning",
                        message="出力先に既存ファイルがあり、上書きの確認が必要です",
                        details={"conflict_files": [output_path]},
                    )
                )
                return PlotCreationResult(
                    success=False,
                    created_files=[],
                    error_message="ファイル衝突により停止(上書き確認が必要)",
                    conflict_files=[output_path],
                    messages=messages,
                )
            template_content = self.template_repo.load_template(task.stage_type)
            customized_content = self._customize_template(template_content, task)
            if has_conflicts and task.merge_strategy == MergeStrategy.MERGE:
                try:
                    existing_content = self.project_file_repo.load_file(output_path)
                    if not isinstance(existing_content, dict):
                        try:
                            existing_content = dict(existing_content)
                        except (TypeError, ValueError):
                            existing_content = {}
                    final_content = self.plot_merge_service.merge_plot_data(
                        existing_content, customized_content, task.merge_strategy
                    )
                except (OSError, ValueError, yaml.YAMLError):
                    final_content = customized_content
            else:
                final_content = customized_content
            parent_dir = "/".join(output_path.split("/")[:-1])
            self.project_file_repo.create_directory(parent_dir)
            self.project_file_repo.save_file(output_path, final_content)
            validation_result = self.plot_validation_service.validate_plot_file(task.stage_type, final_content)
            if not validation_result.is_valid:
                messages.append(
                    DomainMessage(
                        level="warning",
                        message="作成されたファイルに検証上の問題が検出されました",
                        details={"issue_count": len(validation_result.issues)},
                    )
                )
                for issue in validation_result.issues:
                    messages.append(
                        DomainMessage(
                            level=issue.level.value,
                            message=issue.message,
                            suggestion=getattr(issue, "suggestion", None),
                            code=getattr(issue, "code", None),
                        )
                    )
            task.complete_execution([output_path])
            return PlotCreationResult(
                success=True,
                created_files=[output_path],
                validation_result=validation_result,
                messages=messages,
            )
        except Exception as e:
            import traceback
            from pathlib import Path
            log_path = Path("temp/plot_creation_error.log")
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("w", encoding="utf-8") as log:
                traceback.print_exc(file=log)
            setattr(task, "_last_exception", e)
            error_msg = f"プロット作成中にエラーが発生: {e!s}"
            task.fail_execution(error_msg)
            messages.append(
                DomainMessage(
                    level="error",
                    message="プロット作成中に未処理の例外が発生しました",
                    details={"error": str(e)},
                )
            )
            return PlotCreationResult(success=False, created_files=[], error_message=error_msg, messages=messages)

    def _build_prerequisites_error_message(self, prerequisites_results: dict) -> str:
        """前提条件エラーメッセージを構築"""
        missing_files: list[str] = []
        missing_files.extend(
            f"{result.rule.description}({result.file_path})"
            for result in prerequisites_results
            if result.rule.required and (not result.satisfied)
        )
        return f"不足ファイル: {', '.join(missing_files)}"

    def _customize_template(self, template_content: dict[str, Any], task: PlotCreationTask) -> dict[str, Any]:
        """テンプレートをプロジェクト固有情報でカスタマイズ

        Args:
            template_content: テンプレート内容
            task: プロット作成タスク

        Returns:
            Dict[str, Any]: カスタマイズされた内容
        """
        project_config_raw = self.project_file_repo.load_project_config()
        if isinstance(project_config_raw, dict):
            project_config = project_config_raw
        elif isinstance(project_config_raw, Mapping):
            project_config = dict(project_config_raw)
        else:
            try:
                project_config = dict(project_config_raw)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                project_config = {}
        if isinstance(template_content, dict):
            customized: dict[str, Any] = template_content.copy()
        elif isinstance(template_content, Mapping):
            try:
                customized = dict(template_content)
            except (TypeError, ValueError):
                customized = {}
        else:
            customized = {}
        customized.update(
            {
                "creation_date": project_now().datetime.isoformat(),
                "last_updated": project_now().datetime.isoformat(),
                "stage_type": task.stage_type.value,
            }
        )
        customized.update(task.parameters)
        if "project" in customized and isinstance(customized["project"], str):
            with contextlib.suppress(KeyError, ValueError, TypeError):
                customized["project"] = customized["project"].format(**project_config)
        return customized
