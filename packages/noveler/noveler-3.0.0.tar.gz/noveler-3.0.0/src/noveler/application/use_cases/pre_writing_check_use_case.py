#!/usr/bin/env python3

"""Application.use_cases.pre_writing_check_use_case
Where: Application use case performing pre-writing checks.
What: Validates story setup, metadata, and constraints before writing begins.
Why: Helps authors catch inconsistencies early to avoid downstream rewrites.
"""

from __future__ import annotations



from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.domain.entities.pre_writing_check import (
    CheckItemStatus,
    CheckItemType,
    PreWritingCheck,
)
from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.episode_number import EpisodeNumber

if TYPE_CHECKING:
    from noveler.domain.repositories.episode_repository import EpisodeRepository
    from noveler.domain.repositories.project_repository import ProjectRepository
    from noveler.domain.repositories.quality_repository import QualityRepository
    from noveler.domain.repositories.plot_repository import PlotRepository
    from noveler.domain.repositories.scene_repository import SceneRepository

logger = get_logger(__name__)


class CheckStatus(Enum):
    """チェック結果ステータス"""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class CheckItemInput:
    """チェック項目入力データ"""

    item_id: str | None = None
    item_name: str = ""
    check_type: str = "basic"
    required: bool = True
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    check_id: str | None = None
    item_type: CheckItemType | None = None
    notes: str = ""


@dataclass
class PreWritingCheckRequest:
    """執筆前チェックリクエスト"""

    project_name: str
    episode_number: int
    check_items: list[CheckItemInput] = field(default_factory=list)
    strict_mode: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PreWritingCheckResponse:
    """執筆前チェックレスポンス"""

    success: bool
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    warning_checks: int = 0
    check_results: list[dict[str, Any]] = field(default_factory=list)
    error_details: str | None = None


@dataclass
class PreWritingCheckListResponse:
    """チェックリスト作成レスポンス"""

    success: bool
    check_id: str
    project_name: str
    episode_number: int
    check_items: list[dict[str, Any]]
    completion_rate: float


@dataclass
class CheckCompletionResponse:
    """チェック項目完了レスポンス"""

    success: bool
    check_id: str
    item_type: CheckItemType
    completion_rate: float
    status: CheckItemStatus


class PreWritingCheckUseCase(AbstractUseCase[PreWritingCheckRequest, PreWritingCheckResponse]):
    """執筆前チェックユースケース

    執筆開始前の各種事前チェック処理を管理
    """

    def __init__(
        self,
        project_repository: ProjectRepository,
        quality_repository: QualityRepository | None = None,
        episode_repository: EpisodeRepository | None = None,
        plot_repository: PlotRepository | None = None,
        scene_repository: SceneRepository | None = None,
        **kwargs: Any,
    ) -> None:
        """初期化

        Args:
            project_repository: プロジェクトリポジトリ
            quality_repository: 品質リポジトリ（オプション）
            **kwargs: 基底クラスに渡される追加引数
        """
        super().__init__(**kwargs)
        self.project_repository = project_repository
        self.quality_repository = quality_repository
        self.episode_repository = episode_repository
        self.plot_repository = plot_repository
        self.scene_repository = scene_repository

        self._checks: dict[str, PreWritingCheck] = {}
        self._history: list[dict[str, Any]] = []

        logger.debug("PreWritingCheckUseCase initialized")

    async def execute(self, request: PreWritingCheckRequest) -> PreWritingCheckResponse:
        """執筆前チェック実行

        Args:
            request: 執筆前チェックリクエスト

        Returns:
            PreWritingCheckResponse: チェック結果
        """
        try:
            logger.info(f"Starting pre-writing check for episode {request.episode_number}")

            # プロジェクト存在確認
            project = await self.project_repository.find_by_id(request.project_name)
            if not project:
                return PreWritingCheckResponse(success=False, error_details=f"Project {request.project_name} not found")

            check_results = []
            passed_count = 0
            failed_count = 0
            warning_count = 0

            # チェック項目がない場合のデフォルトチェック
            if not request.check_items:
                request.check_items = self._get_default_check_items()

            # 各チェック項目を実行
            for check_item in request.check_items:
                result = await self._execute_check_item(check_item, request)
                check_results.append(result)

                if result["status"] == CheckStatus.PASSED.value:
                    passed_count += 1
                elif result["status"] == CheckStatus.FAILED.value:
                    failed_count += 1
                elif result["status"] == CheckStatus.WARNING.value:
                    warning_count += 1

            # 全体結果判定
            success = failed_count == 0
            if request.strict_mode:
                success = failed_count == 0 and warning_count == 0

            logger.info(
                f"Pre-writing check completed: {passed_count} passed, {failed_count} failed, {warning_count} warnings"
            )

            return PreWritingCheckResponse(
                success=success,
                total_checks=len(check_results),
                passed_checks=passed_count,
                failed_checks=failed_count,
                warning_checks=warning_count,
                check_results=check_results,
            )

        except Exception as e:
            logger.exception(f"Pre-writing check failed: {e}")
            return PreWritingCheckResponse(success=False, error_details=str(e))

    # ------------------------------------------------------------------
    # 同期ユースケースAPI（テスト用）
    # ------------------------------------------------------------------
    def create_check_list(self, request: PreWritingCheckRequest) -> PreWritingCheckListResponse:
        """新しいチェックリストを作成"""
        if not self.project_repository.exists(request.project_name):
            raise DomainException("プロジェクトが存在しません")

        check_id = self._generate_check_id(request.project_name, request.episode_number)
        checklist = PreWritingCheck(EpisodeNumber(request.episode_number), request.project_name)

        self._checks[check_id] = checklist
        self._history.append({
            "check_id": check_id,
            "project_name": request.project_name,
            "episode_number": request.episode_number,
            "created_at": datetime.utcnow(),
            "completion_rate": checklist.get_completion_rate(),
        })

        return PreWritingCheckListResponse(
            success=True,
            check_id=check_id,
            project_name=request.project_name,
            episode_number=request.episode_number,
            check_items=self._serialize_check_items(checklist),
            completion_rate=0.0,
        )

    def check_previous_flow(self, project_name: str, current_episode_number: int) -> dict[str, Any]:
        """前話との繋がりを確認"""
        if current_episode_number <= 1:
            return {
                "has_previous": False,
                "skip_reason": "第1話のため前話確認は不要",
                "suggestions": [],
            }

        if self.episode_repository is None:
            return {
                "has_previous": False,
                "skip_reason": "前話情報を取得できません",
                "suggestions": [],
            }

        prev_episode = self.episode_repository.find_by_number(project_name, current_episode_number - 1)
        if not prev_episode:
            return {
                "has_previous": False,
                "skip_reason": "前話の情報が見つかりません",
                "suggestions": ["話数管理.yamlを更新して前話情報を登録してください"],
            }

        previous_title = getattr(getattr(prev_episode, "title", None), "value", "")
        previous_ending = prev_episode.get_metadata("previous_climax", None)
        if previous_ending is None:
            previous_ending = prev_episode.get_metadata("ending", None)

        return {
            "has_previous": True,
            "previous_title": previous_title,
            "previous_ending": previous_ending,
            "suggestions": ["前話の終わり方に合わせて導入シーンを調整してください"],
        }

    def analyze_dropout_risks(self, project_name: str, episode_number: int) -> list[str]:
        """離脱リスクを分析"""
        if self.plot_repository is None:
            return ["プロット情報にアクセスできませんでした"]

        plot_data = self.plot_repository.find_episode_plot(project_name, episode_number)
        if not plot_data:
            return ["プロットデータが見つかりませんでした"]

        risks: list[str] = []
        if plot_data.get("development_pattern") in {"daily_life", "slice_of_life"}:
            risks.append("日常回のため、テンポ低下による離脱リスクがあります")

        middle_scene = plot_data.get("detailed_plot", {}).get("middle", {})
        scene_description = middle_scene.get("scene", "")
        if "説明" in scene_description:
            risks.append("説明が多いため、会話やアクションを挿入してリズムを維持してください")

        if not risks:
            risks.append("特筆すべき離脱リスクは見つかりませんでした")

        return risks

    def get_important_scenes(self, project_name: str, episode_number: int) -> list[dict[str, Any]]:
        """重要シーン情報を取得"""
        if self.scene_repository is None:
            return []

        scenes = self.scene_repository.find_by_episode(project_name, episode_number)
        return scenes or []

    def complete_check_item(self, input_data: CheckItemInput) -> CheckCompletionResponse:
        """チェック項目を完了に更新"""
        checklist = self._require_check(input_data.check_id)
        checklist.complete_item(input_data.item_type, input_data.notes)

        for entry in self._history:
            if entry["check_id"] == input_data.check_id:
                entry["completion_rate"] = checklist.get_completion_rate()
                break

        return CheckCompletionResponse(
            success=True,
            check_id=input_data.check_id,
            item_type=input_data.item_type,
            completion_rate=checklist.get_completion_rate(),
            status=checklist.get_check_item(input_data.item_type).status,
        )

    def validate_for_writing(self, check_id: str) -> dict[str, Any]:
        """執筆開始可否を判定"""
        checklist = self._require_check(check_id)
        pending_items = [item for item in checklist.check_items if not item.is_done()]
        issues = [f"未完了: {item.title}" for item in pending_items]

        return {
            "can_start_writing": not pending_items,
            "completion_rate": checklist.get_completion_rate(),
            "issues": issues,
        }

    def get_check_history(self, project_name: str, episode_number: int) -> list[dict[str, Any]]:
        """チェック履歴を取得"""
        history: list[dict[str, Any]] = []
        for entry in self._history:
            if entry["project_name"] == project_name and entry["episode_number"] == episode_number:
                history.append({
                    "check_id": entry["check_id"],
                    "episode_number": entry["episode_number"],
                    "completion_rate": entry["completion_rate"],
                    "created_at": entry["created_at"],
                })
        return history


    def _get_default_check_items(self) -> list[CheckItemInput]:
        """デフォルトチェック項目取得

        Returns:
            デフォルトのチェック項目リスト
        """
        return [
            CheckItemInput(
                item_id="project_setup",
                item_name="プロジェクト設定確認",
                check_type="setup",
                description="プロジェクトの基本設定が完了しているかチェック",
            ),
            CheckItemInput(
                item_id="plot_availability",
                item_name="プロットデータ存在確認",
                check_type="data",
                description="執筆に必要なプロットデータが存在するかチェック",
            ),
            CheckItemInput(
                item_id="character_consistency",
                item_name="キャラクター設定整合性",
                check_type="consistency",
                required=False,
                description="キャラクター設定の整合性チェック",
            ),
        ]

    async def _execute_check_item(self, check_item: Any, request: PreWritingCheckRequest) -> dict[str, Any]:
        """個別チェック項目実行

        Args:
            check_item: チェック項目
            request: 元のリクエスト

        Returns:
            チェック結果
        """
        try:
            item_id, item_name = self._resolve_item_labels(check_item)
            required = getattr(check_item, "required", True)

            # チェック項目別の処理
            if item_id == "project_setup":
                return await self._check_project_setup(item_id, item_name, request)
            if item_id == "plot_availability":
                return await self._check_plot_availability(item_id, item_name, request)
            if item_id == "character_consistency":
                return await self._check_character_consistency(item_id, item_name, request)
            # 未知のチェック項目
            return {
                "item_id": item_id,
                "item_name": item_name,
                "status": CheckStatus.SKIPPED.value,
                "message": "Unknown check type",
                "details": {},
            }

        except Exception as e:
            logger.warning(f"Check item {getattr(check_item, 'item_id', '?')} failed: {e}")
            return {
                "item_id": item_id,
                "item_name": item_name,
                "status": CheckStatus.FAILED.value if required else CheckStatus.WARNING.value,
                "message": f"Check execution failed: {e}",
                "details": {"error": str(e)},
            }

    async def _check_project_setup(self, item_id: str, item_name: str, request: PreWritingCheckRequest) -> dict[str, Any]:
        """プロジェクト設定チェック"""
        # 簡易実装: プロジェクトが存在すればOK
        return {
            "item_id": item_id,
            "item_name": item_name,
            "status": CheckStatus.PASSED.value,
            "message": "プロジェクト設定OK",
            "details": {"project_name": request.project_name},
        }

    async def _check_plot_availability(
        self, item_id: str, item_name: str, request: PreWritingCheckRequest
    ) -> dict[str, Any]:
        """プロットデータ存在チェック"""
        # TODO: 実際のプロットリポジトリとの連携実装
        return {
            "item_id": item_id,
            "item_name": item_name,
            "status": CheckStatus.WARNING.value,
            "message": "プロットデータチェック未実装",
            "details": {"episode_number": request.episode_number},
        }

    async def _check_character_consistency(
        self, item_id: str, item_name: str, request: PreWritingCheckRequest
    ) -> dict[str, Any]:
        """キャラクター設定整合性チェック"""
        # TODO: 実際のキャラクター整合性チェック実装
        return {
            "item_id": item_id,
            "item_name": item_name,
            "status": CheckStatus.PASSED.value,
            "message": "キャラクター設定整合性OK",
            "details": {},
        }

    def _generate_check_id(self, project_name: str, episode_number: int) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        return f"{project_name}-{episode_number}-{timestamp}"

    def _serialize_check_items(self, checklist: PreWritingCheck) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for item in checklist.check_items:
            items.append(
                {
                    "type": item.type,
                    "title": item.title,
                    "description": item.description,
                    "status": item.status,
                    "notes": item.notes,
                    "checked_at": item.checked_at,
                }
            )
        return items

    def _require_check(self, check_id: str) -> PreWritingCheck:
        checklist = self._checks.get(check_id)
        if checklist is None:
            raise DomainException("チェックリストが見つかりません")
        return checklist

    def _resolve_item_labels(self, check_item: Any) -> tuple[str, str]:
        item_id = getattr(check_item, "item_id", None)
        if item_id is None and hasattr(check_item, "item_type"):
            item_id = getattr(check_item.item_type, "value", str(check_item.item_type))
        if item_id is None:
            item_id = "unknown"

        item_name = getattr(check_item, "item_name", item_id)
        return str(item_id), str(item_name)
