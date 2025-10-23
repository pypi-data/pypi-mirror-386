#!/usr/bin/env python3

"""Application.use_cases.a31_claude_code_evaluation_use_case
Where: Application use case orchestrating Claude Code evaluations for A31 checklists.
What: Resolves dependencies, retrieves checklist items, runs evaluations, and formats results.
Why: Enables automated A31 assessments inside Claude Code sessions without manual setup.
"""

from __future__ import annotations

from typing import Any



from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.infrastructure.unit_of_work import IUnitOfWork

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.entities.a31_checklist_item import A31ChecklistItem
from noveler.domain.interfaces import IConsoleService, IPathService
from noveler.domain.repositories.a31_checklist_repository import A31ChecklistRepository
from noveler.domain.services.claude_code_evaluation_service import (
    ClaudeCodeEvaluationRequest,
    ClaudeCodeEvaluationService,
)
from noveler.domain.services.evaluation_result_formatter import EvaluationResultFormatter
from noveler.domain.services.project_config_provider import ProjectConfigProvider
from noveler.domain.services.project_path_resolver import ProjectPathResolver
from noveler.domain.value_objects.a31_evaluation_result import EvaluationResult
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.file_path import FilePath


@dataclass(frozen=True)
class A31ClaudeCodeEvaluationRequest:
    """A31 Claude Code評価ユースケースリクエスト"""

    project_name: str
    episode_number: int
    include_a31: bool = True
    a31_only: bool = False
    show_review: bool = False
    review_verbosity: str = "standard"  # none/basic/standard/verbose


@dataclass
class A31ClaudeCodeEvaluationResponse:
    """A31 Claude Code評価ユースケースレスポンス"""

    success: bool
    project_name: str
    episode_number: int
    total_items: int
    evaluated_items: int
    passed_items: int
    evaluation_results: dict[str, EvaluationResult]
    checklist_file_path: str | None = None
    error_message: str | None = None
    review_output: str | None = None


class A31ClaudeCodeEvaluationUseCase(AbstractUseCase[A31ClaudeCodeEvaluationRequest, A31ClaudeCodeEvaluationResponse]):
    """A31 Claude Code連携評価ユースケース

    Claude Code実行中セッションでの自動評価機能を提供。
    既存コマンド(check, complete, a31-auto-fix)との統合。
    """

    def __init__(self,
        logger_service: ILoggerService = None,
        unit_of_work: IUnitOfWork = None,
        console_service: IConsoleService | None = None,
        path_service: IPathService | None = None,
        **kwargs) -> None:
        """初期化

        Args:
            console_service: コンソールサービス（DI注入）
            path_service: パスサービス（DI注入）
            logger: ロガー（DI注入）
            config_service: 設定サービス（DI注入）
            repository_factory: リポジトリファクトリー（DI注入）
        """
        super().__init__(
            console_service=console_service,
            path_service=path_service,
            logger_service=logger_service,
            **kwargs)
        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work

        # 遅延初期化によるサービス取得
        self._a31_checklist_repository = None
        self._claude_code_evaluation_service = None
        self._project_config_provider = None
        self._project_path_resolver = None
        self._evaluation_result_formatter = None
        self._a31_auto_fix_use_case = None

    @property
    def a31_checklist_repository(self) -> A31ChecklistRepository:
        """A31チェックリストリポジトリ取得"""
        if self._a31_checklist_repository is None:
            self._a31_checklist_repository = self.repository_factory.get_a31_checklist_repository()
        return self._a31_checklist_repository

    @property
    def claude_code_evaluation_service(self) -> ClaudeCodeEvaluationService:
        """Claude Code評価サービス取得"""
        if self._claude_code_evaluation_service is None:
            try:
                from noveler.domain.services.claude_code_evaluation_service import ClaudeCodeEvaluationService
                from noveler.infrastructure.di.container import resolve_service

                self._claude_code_evaluation_service = resolve_service(ClaudeCodeEvaluationService)
            except (ImportError, ValueError):
                from noveler.domain.services.claude_code_evaluation_service import ClaudeCodeEvaluationService

                self._claude_code_evaluation_service = ClaudeCodeEvaluationService()
        return self._claude_code_evaluation_service

    @property
    def project_config_provider(self) -> ProjectConfigProvider:
        """プロジェクト設定プロバイダ取得"""
        if self._project_config_provider is None:
            try:
                from noveler.domain.services.project_config_provider import ProjectConfigProvider
                from noveler.infrastructure.di.container import resolve_service

                self._project_config_provider = resolve_service(ProjectConfigProvider)
            except (ImportError, ValueError):
                from noveler.domain.services.project_config_provider import ProjectConfigProvider

                self._project_config_provider = ProjectConfigProvider()
        return self._project_config_provider

    @property
    def project_path_resolver(self) -> ProjectPathResolver:
        """プロジェクトパス解決サービス取得"""
        if self._project_path_resolver is None:
            try:
                from noveler.domain.services.project_path_resolver import ProjectPathResolver
                from noveler.infrastructure.di.container import resolve_service

                self._project_path_resolver = resolve_service(ProjectPathResolver)
            except (ImportError, ValueError):
                from noveler.domain.services.project_path_resolver import ProjectPathResolver

                self._project_path_resolver = ProjectPathResolver()
        return self._project_path_resolver

    @property
    def evaluation_result_formatter(self) -> EvaluationResultFormatter:
        """評価結果フォーマッタ取得"""
        if self._evaluation_result_formatter is None:
            try:
                from noveler.domain.services.evaluation_result_formatter import EvaluationResultFormatter
                from noveler.infrastructure.di.container import resolve_service

                self._evaluation_result_formatter = resolve_service(EvaluationResultFormatter)
            except (ImportError, ValueError):
                from noveler.domain.services.evaluation_result_formatter import EvaluationResultFormatter

                self._evaluation_result_formatter = EvaluationResultFormatter()
        return self._evaluation_result_formatter

    async def execute(
        self,
        request: A31ClaudeCodeEvaluationRequest,
    ) -> A31ClaudeCodeEvaluationResponse:
        """A31 Claude Code連携評価を実行

        Args:
            request: 評価リクエスト

        Returns:
            A31ClaudeCodeEvaluationResponse: 評価結果
        """
        try:
            self.logger.info(f"A31評価開始: project={request.project_name}, episode={request.episode_number}")

            # 1. プロジェクト設定取得
            config = self.project_config_provider.get_project_config(request.project_name)
            if not self.project_config_provider.should_run_a31_evaluation(
                config, request.include_a31, request.a31_only
            ):
                return self._create_skipped_response(request)

            # 2. チェックリスト取得または作成
            checklist_items = await self._get_or_create_checklist(
                request.project_name,
                request.episode_number,
            )

            # 3. 評価対象項目の決定
            target_items = self._determine_target_items(checklist_items)

            # 4. Claude Code評価実行
            evaluation_results = await self._execute_claude_code_evaluation(
                request.project_name,
                request.episode_number,
                target_items,
            )

            # 5. チェックリスト更新
            checklist_file_path = await self._update_checklist_file(
                request.project_name,
                request.episode_number,
                evaluation_results,
            )

            # 6. レビュー出力生成
            review_output = None
            if request.show_review:
                review_output = self.evaluation_result_formatter.generate_review_output(
                    evaluation_results,
                    request.review_verbosity,
                )

            # 7. レスポンス作成
            passed_count = sum(1 for result in evaluation_results.values() if result.passed)

            self.logger.info(
                f"A31評価完了: total={len(target_items)}, evaluated={len(evaluation_results)}, passed={passed_count}"
            )

            return A31ClaudeCodeEvaluationResponse(
                success=True,
                project_name=request.project_name,
                episode_number=request.episode_number,
                total_items=len(target_items),
                evaluated_items=len(evaluation_results),
                passed_items=passed_count,
                evaluation_results=evaluation_results,
                checklist_file_path=checklist_file_path,
                review_output=review_output,
            )

        except Exception as e:
            self.logger.error(f"A31評価の予期しないエラー: {type(e).__name__}: {e}", exc_info=True)
            return A31ClaudeCodeEvaluationResponse(
                success=False,
                project_name=request.project_name,
                episode_number=request.episode_number,
                total_items=0,
                evaluated_items=0,
                passed_items=0,
                evaluation_results={},
                error_message=f"A31評価エラー: {e!s}",
            )

    def _create_skipped_response(
        self,
        request: A31ClaudeCodeEvaluationRequest,
    ) -> A31ClaudeCodeEvaluationResponse:
        """スキップされた場合のレスポンスを作成

        Args:
            request: 評価リクエスト

        Returns:
            A31ClaudeCodeEvaluationResponse: スキップレスポンス
        """
        return A31ClaudeCodeEvaluationResponse(
            success=True,
            project_name=request.project_name,
            episode_number=request.episode_number,
            total_items=0,
            evaluated_items=0,
            passed_items=0,
            evaluation_results={},
            error_message="A31評価がスキップされました(設定により無効化)",
        )

    async def _get_or_create_checklist(
        self,
        project_name: str,
        episode_number: int,
    ) -> list[A31ChecklistItem]:
        """チェックリストを取得または作成

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            list[A31ChecklistItem]: チェックリスト項目
        """
        try:
            # 既存チェックリストの取得を試行
            return await self._unit_of_work.a31_checklist_repository.get_checklist_items(
                project_name,
                EpisodeNumber(episode_number),
            )
        except (FileNotFoundError, ValueError, TypeError):
            # 存在しない場合はテンプレートから作成
            return await self._unit_of_work.a31_checklist_repository.create_from_template(
                project_name,
                EpisodeNumber(episode_number),
            )

    def _determine_target_items(
        self,
        checklist_items: list[A31ChecklistItem],
    ) -> list[A31ChecklistItem]:
        """評価対象項目を決定

        Args:
            checklist_items: 全チェックリスト項目

        Returns:
            list[A31ChecklistItem]: 評価対象項目
        """
        # Claude Code評価可能項目のみを抽出
        claude_evaluable_types = {
            "document_review",
            "content_review",
            "content_planning",
            "risk_assessment",
            "scene_design",
        }

        return [item for item in checklist_items if item.item_type.value in claude_evaluable_types]

    async def _execute_claude_code_evaluation(
        self,
        project_name: str,
        episode_number: int,
        target_items: list[A31ChecklistItem],
    ) -> dict[str, EvaluationResult]:
        """Claude Code評価を実行

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            target_items: 評価対象項目

        Returns:
            dict[str, EvaluationResult]: 項目ID別の評価結果
        """
        results: dict[str, Any] = {}

        # エピソードファイルパスの決定
        episode_file_path = self.project_path_resolver.resolve_episode_file_path(project_name, episode_number)

        for item in target_items:
            try:
                # 関連ファイルの決定(簡略化版)
                context_files: list[FilePath] = []

                # 評価リクエスト作成
                eval_request = ClaudeCodeEvaluationRequest(
                    item=item,
                    episode_file_path=episode_file_path,
                    context_files=context_files,
                    metadata={"project_name": project_name, "episode_number": episode_number},
                )

                # Claude Code評価実行
                result = await self.claude_code_evaluation_service.evaluate_item(eval_request)
                results[item.item_id] = result

            except (ConnectionError, TimeoutError, ValueError, AttributeError, ImportError) as e:
                self.logger.warning(f"評価項目 {item.item_id} でエラー: {e}")
                # エラー時は失敗結果を作成
                results[item.item_id] = EvaluationResult(
                    item_id=item.item_id,
                    current_score=0.0,
                    threshold_value=item.threshold.value if item.threshold else 0.0,
                    passed=False,
                    details={"error": f"評価エラー: {e!s}"},
                )

        return results

    async def _update_checklist_file(
        self,
        project_name: str,
        episode_number: int,
        evaluation_results: dict[str, EvaluationResult],
    ) -> str:
        """チェックリストファイルを更新

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            evaluation_results: 評価結果

        Returns:
            str: 更新されたチェックリストファイルパス
        """
        return await self._unit_of_work.a31_checklist_repository.update_evaluation_results(
            project_name,
            EpisodeNumber(episode_number),
            evaluation_results,
        )
