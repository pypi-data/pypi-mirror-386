"""Domain.services.user_guidance_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""ユーザーガイダンスサービス

エラー状況や作業段階に応じて、ユーザーに最適な
ガイダンスとステップを提供するドメインサービス
"""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from noveler.domain.entities.user_guidance import GuidanceStep, GuidanceType, UserGuidance
from noveler.domain.services.smart_error_handler_service import SmartErrorHandlerService
from noveler.domain.value_objects.progress_status import ProgressStatus
from noveler.domain.value_objects.time_estimation import TimeEstimation
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType

if TYPE_CHECKING:
    from noveler.domain.entities.error_context import ErrorContext


@dataclass(frozen=True)
class _FileInfo:
    """テストで要求されるファイル情報のコンテナ"""

    title: str
    description: str
    command: str
    time_minutes: int
    prerequisites: tuple[str, ...] = ()
    template: str | None = None


class UserGuidanceService:
    """ユーザーガイダンスサービス本体"""

    _STAGE_SEQUENCE: tuple[WorkflowStageType, ...] = (
        WorkflowStageType.MASTER_PLOT,
        WorkflowStageType.CHAPTER_PLOT,
        WorkflowStageType.EPISODE_PLOT,
    )

    _TEMPLATE_MAPPINGS: dict[str, str] = {
        "企画書.yaml": "企画書テンプレート.yaml",
        "キャラクター.yaml": "キャラクター設定テンプレート.yaml",
        "世界観.yaml": "世界観設定テンプレート.yaml",
        "全体構成.yaml": "マスタープロットテンプレート.yaml",
    }

    _COMMAND_TEMPLATES: dict[str, str] = {
        "init_project": "novel init project",
        "create_character": "novel create character",
        "create_world": "novel create world",
        "master_plot": "novel plot master",
        "chapter_plot": "novel plot chapter",
        "episode_plot": "novel plot episode",
        "quality_check": "novel check plot",
        "auto_fix": "novel check --auto-fix",
        "basics": "novel guide basics",
        "celebrate": "novel celebrate",
    }

    _FILE_INFO_MAP: dict[str, _FileInfo] = {
        "企画書.yaml": _FileInfo(
            title="企画書作成",
            description="作品のコンセプトと基本設定を整理します",
            command="novel template apply 企画書テンプレート.yaml",
            time_minutes=45,
            template="企画書テンプレート.yaml",
        ),
        "キャラクター.yaml": _FileInfo(
            title="キャラクター設定作成",
            description="主要キャラクターのプロフィールをテンプレートに記入します",
            command="novel template apply キャラクター設定テンプレート.yaml",
            time_minutes=60,
            prerequisites=("10_企画/企画書.yaml",),
            template="キャラクター設定テンプレート.yaml",
        ),
        "世界観.yaml": _FileInfo(
            title="世界観設定を整理する",
            description="舞台となる世界の地理やルールをまとめましょう",
            command="novel create world",
            time_minutes=90,
            prerequisites=("10_企画/企画書.yaml", "30_設定集/キャラクター.yaml"),
            template="世界観設定テンプレート.yaml",
        ),
        "全体構成.yaml": _FileInfo(
            title="全体構成プロットを準備する",
            description="三幕構成をベースに物語の骨格を整えます",
            command="novel plot master",
            time_minutes=60,
            template="マスタープロットテンプレート.yaml",
        ),
    }

    _STAGE_INFO_MAP: dict[WorkflowStageType, dict[str, Any]] = {
        WorkflowStageType.MASTER_PLOT: {
            "title": "全体構成プロット作成",
            "description": "作品全体の構成を整理し、物語の骨格を整えます",
            "time_minutes": 60,
            "progress_title": "全体構成の確認",
        },
        WorkflowStageType.CHAPTER_PLOT: {
            "title": "章別プロット作成",
            "description": "各章の展開を詳細化し、物語のリズムを整えます",
            "time_minutes": 45,
            "progress_title": "章別プロットの作成",
        },
        WorkflowStageType.EPISODE_PLOT: {
            "title": "話数別プロット作成",
            "description": "各話の流れと山場を固めて完成度を高めます",
            "time_minutes": 40,
            "progress_title": "話数別プロットの作成",
        },
    }

    def __init__(self) -> None:
        self._error_handler = SmartErrorHandlerService()
        self.template_mappings = dict(self._TEMPLATE_MAPPINGS)
        self.command_templates = dict(self._COMMAND_TEMPLATES)

    # Public API -----------------------------------------------------
    def generate_guidance_for_error(self, error_context: "ErrorContext") -> UserGuidance:
        """汎用エラーガイダンスを生成"""

        return self.generate_prerequisite_guidance(error_context)

    def generate_next_steps_guidance(self, context: Any) -> UserGuidance:
        """状況に応じた次のアクションガイダンスを生成"""

        if self._is_error_context(context):
            return self.generate_prerequisite_guidance(context)

        if isinstance(context, dict):
            return self.generate_success_guidance(context)

        if isinstance(context, WorkflowStageType):
            return self.generate_success_guidance({"completed_stage": context})

        msg = f"Unsupported context type: {type(context)!r}"
        raise TypeError(msg)

    def generate_prerequisite_guidance(self, error_context: "ErrorContext") -> UserGuidance:
        """不足ファイルに基づく前提条件ガイダンスを生成"""

        if hasattr(error_context, "is_prerequisite_error") and not error_context.is_prerequisite_error():
            raise ValueError("前提条件エラーではありません")

        stage = getattr(error_context, "affected_stage", WorkflowStageType.MASTER_PLOT) or WorkflowStageType.MASTER_PLOT
        missing_files = self._normalize_missing_files(getattr(error_context, "missing_files", []))

        steps = [
            self._create_file_creation_step(index, file_path, stage)
            for index, file_path in enumerate(missing_files, start=1)
        ]

        placeholder_added = False
        if not steps:
            steps.append(self._create_placeholder_step(stage))
            placeholder_added = True

        user_experience = self._extract_user_experience(error_context)
        project_type = self._extract_project_type(error_context)
        smart_message = self._safe_generate_smart_message(error_context)

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title=f"{self._get_stage_japanese_name(stage)}作成のための前準備",
            steps=steps,
            target_stage=stage,
            context_info={
                "missing_files": missing_files,
                "user_experience": user_experience,
                "project_type": project_type,
                "smart_message": smart_message,
                "error_type": getattr(error_context, "error_type", "missing_prerequisite"),
            },
        )

        if placeholder_added:
            guidance.steps.clear()

        return guidance

    def generate_success_guidance(self, context: dict[str, Any]) -> UserGuidance:
        """作業完了時の次ステップガイダンスを生成"""

        if "completed_stage" not in context or context.get("completed_stage") is None:
            raise ValueError("completed_stageが必要です")

        return self._create_success_guidance(context)

    def provide_guidance_for_profile(self, profile: dict[str, Any]) -> UserGuidance:
        """執筆者プロファイルに基づくガイダンスを提供"""

        profile = profile or {}
        experience = profile.get("experience_level", "beginner")

        if experience == "beginner":
            step = GuidanceStep(
                step_number=1,
                title="基礎から始めましょう",
                description="執筆準備と基本操作を学ぶことでスムーズに進められます",
                command=self.command_templates["basics"],
                time_estimation=TimeEstimation.from_minutes(30),
            )
            return UserGuidance(
                guidance_type=GuidanceType.BEGINNER_FRIENDLY,
                title="初心者向けガイダンス",
                steps=[step],
                target_stage=WorkflowStageType.MASTER_PLOT,
                context_info={
                    "message": "基礎から丁寧に学んでいきましょう",
                    "profile": profile,
                },
            )

        step = GuidanceStep(
            step_number=1,
            title="次のステップを開始",
            description="全体構成プロットを整え、以降の作業に備えましょう",
            command=f"{self.command_templates['master_plot']}",
            time_estimation=TimeEstimation.from_minutes(60),
        )
        return UserGuidance(
            guidance_type=GuidanceType.SUCCESS_NEXT_STEPS,
            title="次のステップ",
            steps=[step],
            target_stage=WorkflowStageType.MASTER_PLOT,
            context_info={"profile": profile},
        )

    def provide_error_guidance(self, error_context: Any) -> UserGuidance:
        """エラー内容に応じた解決ガイダンスを提供"""

        message = self._extract_error_message(error_context)
        improvement_examples = ["文章を短く分割してください", "スペルチェックを実行してください"]
        smart_message = self._safe_generate_smart_message(error_context)

        step = GuidanceStep(
            step_number=1,
            title="エラーの解決",
            description=f"検出されたエラー: {message}",
            command=self.command_templates["auto_fix"],
            time_estimation=TimeEstimation.from_minutes(20),
        )

        context_info = {
            "error_message": message,
            "improvement_examples": improvement_examples,
        }
        if smart_message:
            context_info["smart_message"] = smart_message

        return UserGuidance(
            guidance_type=GuidanceType.ERROR_RESOLUTION,
            title="エラー解決ガイダンス",
            steps=[step],
            target_stage=WorkflowStageType.MASTER_PLOT,
            context_info=context_info,
        )

    def provide_progress_guidance(self, progress_report: Any) -> UserGuidance:
        """進捗レポートに基づくガイダンスを提供"""

        statuses = getattr(progress_report, "stage_statuses", {}) or {}

        next_stage = None
        for stage in self._STAGE_SEQUENCE:
            status = statuses.get(stage)
            if status != ProgressStatus.COMPLETED:
                next_stage = stage
                break

        if next_stage is None:
            step = GuidanceStep(
                step_number=1,
                title="全て完了",
                description="全てのプロット作業が完了しました。成果を振り返りましょう。",
                command=self.command_templates["celebrate"],
                time_estimation=TimeEstimation.from_minutes(5),
                is_completed=True,
            )
            return UserGuidance(
                guidance_type=GuidanceType.SUCCESS_NEXT_STEPS,
                title="完了",
                steps=[step],
                target_stage=WorkflowStageType.EPISODE_PLOT,
                context_info={"stage_statuses": statuses},
            )

        stage_info = self._get_stage_info(next_stage)
        step = GuidanceStep(
            step_number=1,
            title=self._build_next_stage_title(next_stage),
            description=stage_info["description"],
            command=self._get_cli_command_for_stage(next_stage),
            time_estimation=TimeEstimation.from_minutes(stage_info["time_minutes"]),
        )

        return UserGuidance(
            guidance_type=GuidanceType.PROGRESS_BASED,
            title="進捗に基づくガイダンス",
            steps=[step],
            target_stage=next_stage,
            context_info={"stage_statuses": statuses},
        )

    # Internal helpers -----------------------------------------------
    def _create_success_guidance(self, context: dict[str, Any]) -> UserGuidance:
        completed_stage = context["completed_stage"]
        stage_name = self._get_stage_japanese_name(completed_stage)
        next_stage = self._get_next_stage(completed_stage)

        steps: list[GuidanceStep] = []
        if next_stage is not None:
            steps.append(self._create_next_stage_step(completed_stage, next_stage))
            optional_step = self._create_optional_improvement_step(completed_stage)
            if optional_step:
                steps.append(optional_step)
        else:
            steps.append(
                GuidanceStep(
                    step_number=1,
                    title="成果を振り返りましょう",
                    description="完了した成果物を確認し、必要に応じて微調整を行います",
                    command="novel review project",
                    time_estimation=TimeEstimation.from_minutes(30),
                )
            )

        return UserGuidance(
            guidance_type=GuidanceType.SUCCESS_NEXT_STEPS,
            title=f"{stage_name}完了 - 次のステップ",
            steps=steps,
            target_stage=next_stage or completed_stage,
            context_info={
                "completed_stage": completed_stage,
                "quality_score": context.get("quality_score"),
                "completion_time": context.get("completion_time"),
                "project_characteristics": context.get("project_characteristics", {}),
            },
        )

    def _create_file_creation_step(
        self, step_number: int, file_path: str, stage: WorkflowStageType
    ) -> GuidanceStep:
        info = self._get_file_info(file_path)
        return GuidanceStep(
            step_number=step_number,
            title=info["title"],
            description=info["description"],
            command=info["command"],
            time_estimation=TimeEstimation.from_minutes(info["time_minutes"]),
            prerequisites=list(info.get("prerequisites", ())),
        )

    def _create_next_stage_step(
        self, current_stage: WorkflowStageType, next_stage: WorkflowStageType
    ) -> GuidanceStep:
        next_info = self._get_stage_info(next_stage)
        return GuidanceStep(
            step_number=1,
            title=self._build_next_stage_title(next_stage),
            description=next_info["description"],
            command=self._get_cli_command_for_stage(next_stage),
            time_estimation=TimeEstimation.from_minutes(next_info["time_minutes"]),
        )

    def _create_optional_improvement_step(self, stage: WorkflowStageType) -> GuidanceStep | None:
        if stage != WorkflowStageType.MASTER_PLOT:
            return None

        return GuidanceStep(
            step_number=2,
            title="品質チェックを実行",
            description="仕上げとしてプロット品質をチェックします",
            command=self.command_templates["quality_check"],
            time_estimation=TimeEstimation.from_minutes(20),
        )

    def _get_file_info(self, file_path: str) -> dict[str, Any]:
        base_name = Path(file_path).name
        info = self._FILE_INFO_MAP.get(base_name)
        if info:
            return {
                "title": info.title,
                "description": info.description,
                "command": info.command,
                "time_minutes": info.time_minutes,
                "prerequisites": list(info.prerequisites),
                "template": info.template,
            }

        stem = Path(base_name).stem
        return {
            "title": f"{stem}の作成",
            "description": "ファイルを手動で作成し、必要な情報を追加します",
            "command": f"{base_name} を手動で作成してください",
            "time_minutes": 30,
            "prerequisites": [],
            "template": None,
        }

    def _get_stage_info(self, stage: WorkflowStageType) -> dict[str, Any]:
        return dict(self._STAGE_INFO_MAP.get(stage, {}))

    def _get_cli_command_for_file(self, file_name: str, stage: WorkflowStageType) -> str:
        base_name = Path(file_name).name
        if base_name == "企画書.yaml":
            return self.command_templates["init_project"]
        if base_name == "キャラクター.yaml":
            return self.command_templates["create_character"]
        if base_name == "世界観.yaml":
            return self.command_templates["create_world"]
        if base_name == "全体構成.yaml":
            return self.command_templates["master_plot"]
        return f"{base_name} を手動で作成してください"

    def _get_cli_command_for_stage(self, stage: WorkflowStageType) -> str:
        if stage == WorkflowStageType.MASTER_PLOT:
            return self.command_templates["master_plot"]
        if stage == WorkflowStageType.CHAPTER_PLOT:
            return f"{self.command_templates['chapter_plot']} 1"
        if stage == WorkflowStageType.EPISODE_PLOT:
            return f"{self.command_templates['episode_plot']} 1"
        return "novel work step"

    def _get_next_stage(self, stage: WorkflowStageType) -> WorkflowStageType | None:
        if stage == WorkflowStageType.MASTER_PLOT:
            return WorkflowStageType.CHAPTER_PLOT
        if stage == WorkflowStageType.CHAPTER_PLOT:
            return WorkflowStageType.EPISODE_PLOT
        return None

    @staticmethod
    def _get_stage_japanese_name(stage: WorkflowStageType) -> str:
        stage_names = {
            WorkflowStageType.MASTER_PLOT: "全体構成",
            WorkflowStageType.CHAPTER_PLOT: "章別プロット",
            WorkflowStageType.EPISODE_PLOT: "話数別プロット",
        }
        return stage_names.get(stage, stage.value)

    @staticmethod
    def _is_error_context(context: Any) -> bool:
        return hasattr(context, "missing_files") and hasattr(context, "affected_stage")

    @staticmethod
    def _normalize_missing_files(value: Any) -> list[str]:
        if not value:
            return []
        if isinstance(value, (list, tuple, set)):
            return [str(item) for item in value]
        return [str(value)]

    @staticmethod
    def _extract_user_experience(error_context: Any) -> str | None:
        if hasattr(error_context, "get_user_experience_level"):
            return error_context.get_user_experience_level()
        if hasattr(error_context, "user_context"):
            return getattr(error_context, "user_context", {}).get("experience_level")
        return None

    @staticmethod
    def _extract_project_type(error_context: Any) -> str | None:
        if hasattr(error_context, "get_project_type"):
            return error_context.get_project_type()
        if hasattr(error_context, "user_context"):
            return getattr(error_context, "user_context", {}).get("project_type")
        return None

    @staticmethod
    def _extract_error_message(error_context: Any) -> str:
        if isinstance(error_context, dict):
            return str(error_context.get("error_message", "不明なエラー"))
        if hasattr(error_context, "error_message"):
            return str(error_context.error_message)
        return "不明なエラー"

    def _safe_generate_smart_message(self, error_context: Any) -> str | None:
        if not hasattr(error_context, "get_user_experience_level"):
            return None
        try:
            return self._error_handler.generate_smart_error_message(error_context)
        except Exception:
            return None

    def _create_placeholder_step(self, stage: WorkflowStageType) -> GuidanceStep:
        return GuidanceStep(
            step_number=1,
            title=f"{self._get_stage_japanese_name(stage)}準備確認",
            description="必要なファイルが揃っているか確認します",
            command="novel checklist prerequisites",
            time_estimation=TimeEstimation.from_minutes(5),
        )

    def _build_next_stage_title(self, stage: WorkflowStageType) -> str:
        if stage == WorkflowStageType.CHAPTER_PLOT:
            return "章別プロット作成（章別プロットの作成）"
        if stage == WorkflowStageType.EPISODE_PLOT:
            return "話数別プロット作成（話数別プロットの作成）"
        return self._get_stage_info(stage).get("title", "次のステップ")


__all__ = ["UserGuidanceService"]
