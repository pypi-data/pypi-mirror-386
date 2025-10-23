#!/usr/bin/env python3

"""Application.use_cases.a31_complete_check_use_case
Where: Application use case coordinating the complete A31 checklist evaluation.
What: Orchestrates checklist loading, evaluation execution, and result aggregation.
Why: Provides a reusable entry point for comprehensive A31 quality checks.
"""

from __future__ import annotations


import contextlib
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from noveler.domain.interfaces.console_service_protocol import IConsoleService
    from noveler.domain.interfaces.path_service_protocol import IPathService

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.entities.a31_checklist_item import A31ChecklistItem, ChecklistItemType
from noveler.domain.entities.a31_complete_evaluation_engine import (
    A31CompleteCheckRequest,
    A31CompleteCheckResponse,
    A31EvaluationBatch,
    A31EvaluationCategory,
)
from noveler.domain.services.a31_auto_fix_service import A31AutoFixService
from noveler.domain.value_objects.a31_fix_level import FixLevel


class A31CompleteCheckUseCase(AbstractUseCase[A31CompleteCheckRequest, A31CompleteCheckResponse]):
    """A31完全チェックユースケース - B20準拠

    B20準拠DIパターン:
    - logger_service, unit_of_work 注入
    - 仕様68項目のA31チェックリストを6カテゴリで評価
    - 構造化された結果レポートを生成
    """

    def __init__(
        self,
        logger_service,
        unit_of_work,
        console_service: IConsoleService | None = None,
        path_service: IPathService | None = None,
    ) -> None:
        """完全チェックユースケースの初期化 - B20準拠

        Args:
            logger_service: ロガーサービス
            unit_of_work: Unit of Work
            console_service: コンソールサービス（DI注入）
            path_service: パスサービス（DI注入）
        """
        # 基底クラス初期化（共通サービス）
        super().__init__(console_service=console_service, path_service=path_service)

        self._logger_service = logger_service
        self._unit_of_work = unit_of_work

        # ドメインサービスは必要時に生成
        self._evaluation_engine = None
        self._claude_analyzer = None
        self._result_integrator = None

    async def execute(self, request: A31CompleteCheckRequest) -> A31CompleteCheckResponse:
        """A31完全チェックの実行（Claude分析統合対応）

        Args:
            request: チェックリクエスト

        Returns:
            A31CompleteCheckResponse: チェック結果

        Raises:
            FileNotFoundError: エピソードファイルが見つからない場合
            ValueError: チェックリスト項目が無効な場合
        """
        start_time = time.time()

        try:
            # 1. エピソード内容の取得
            episode_content = self._get_episode_content(request.project_name, request.episode_number)

            # 2. チェックリスト項目の取得
            checklist_items = self._get_checklist_items(request.project_name, request.target_categories)

            if not checklist_items:
                return A31CompleteCheckResponse(
                    success=False,
                    project_name=request.project_name,
                    episode_number=request.episode_number,
                    evaluation_batch=A31EvaluationBatch({}, 0, 0, 0.0),
                    error_message="対象のチェックリスト項目が見つかりません",
                )

            # 3. 評価コンテキストの準備
            evaluation_context = self._prepare_evaluation_context(request.project_name, request.episode_number)

            # 4. ローカル評価の実行
            evaluation_batch = self._evaluation_engine.evaluate_all_items(
                episode_content, checklist_items, evaluation_context
            )

            # 🆕 5. Claude分析統合処理
            claude_integration_results = None
            if request.include_claude_analysis and self._claude_analyzer and self._result_integrator:
                claude_integration_results = await self._execute_claude_analysis_integration(
                    request, episode_content, evaluation_batch
                )

                # Claude分析結果でローカル評価を拡張
                if claude_integration_results and claude_integration_results.success:
                    evaluation_batch = self._merge_claude_results_with_local(
                        evaluation_batch, claude_integration_results.analysis_result
                    )

            auto_fixes_applied = 0
            final_content = episode_content

            # 6. 自動修正の実行(include_auto_fixがTrueの場合のみ)
            if request.include_auto_fix:
                fix_count, fixed_content = self._apply_integrated_auto_fixes(
                    request, final_content, evaluation_batch, checklist_items
                )

                auto_fixes_applied = fix_count

                if fix_count > 0:
                    final_content = fixed_content

                    # 修正後の再評価
                    evaluation_batch = self._evaluation_engine.evaluate_all_items(
                        final_content, checklist_items, evaluation_context
                    )

                    # エピソードファイルの更新
                    self._update_episode_content(request.project_name, request.episode_number, final_content)

            # 7. チェックリストファイルの保存
            checklist_file_path = self._save_checklist_results(
                request.project_name, request.episode_number, evaluation_batch
            )

            execution_time = (time.time() - start_time) * 1000

            return A31CompleteCheckResponse(
                success=True,
                project_name=request.project_name,
                episode_number=request.episode_number,
                evaluation_batch=evaluation_batch,
                total_items_checked=len(checklist_items),
                checklist_file_path=str(checklist_file_path),
                auto_fixes_applied=auto_fixes_applied,
                claude_analysis_applied=claude_integration_results is not None,
                execution_time_ms=execution_time,
            )

        except FileNotFoundError as e:
            return A31CompleteCheckResponse(
                success=False,
                project_name=request.project_name,
                episode_number=request.episode_number,
                evaluation_batch=A31EvaluationBatch({}, 0, 0, 0.0),
                error_message=f"エピソードファイルが見つかりません: {e!s}",
            )

        except Exception as e:
            return A31CompleteCheckResponse(
                success=False,
                project_name=request.project_name,
                episode_number=request.episode_number,
                evaluation_batch=A31EvaluationBatch({}, 0, 0, 0.0),
                error_message=f"チェック実行中にエラーが発生しました: {e!s}",
            )

    async def _execute_claude_analysis_integration(
        self, request: A31CompleteCheckRequest, episode_content: str, local_evaluation_batch: A31EvaluationBatch
    ) -> dict | None:
        """Claude分析統合処理

        Args:
            request: チェックリクエスト
            episode_content: エピソード内容
            local_evaluation_batch: ローカル評価結果

        Returns:
            Optional[SessionAnalysisResponse]: Claude分析結果
        """
        if not self._claude_analyzer:
            return None

        try:
            # プロジェクトルート取得
            project_root = self._get_project_root_path(request.project_name)

            # エピソードタイトル取得
            episode_title = self._get_episode_title(request.project_name, request.episode_number)

            # パスサービス使用（DI注入による依存性解決）
            path_service = self.get_path_service(project_root)
            checklist_file_path = path_service.get_checklist_file_path(request.episode_number, episode_title)

            manuscript_file_path = path_service.get_episode_file_path(request.episode_number, episode_title)

            # SessionAnalysisRequest構築
            from noveler.application.use_cases.session_based_analysis_use_case import SessionAnalysisRequest

            analysis_request = SessionAnalysisRequest(
                checklist_file_path=str(checklist_file_path),
                manuscript_file_path=str(manuscript_file_path),
                episode_number=request.episode_number,
                project_name=request.project_name,
                max_priority_items=20,
                extraction_strategy="hybrid",
                enable_parallel_analysis=True,
                enable_real_time_integration=False,  # 手動統合に変更
            )

            # Claude分析実行
            from noveler.application.use_cases.session_based_analysis_use_case import SessionBasedAnalysisUseCase
            from noveler.domain.services.a31_priority_extractor_service import A31PriorityExtractorService

            priority_extractor = A31PriorityExtractorService()
            session_use_case = SessionBasedAnalysisUseCase(
                priority_extractor=priority_extractor, session_analyzer=self._claude_analyzer
            )

            # プログレスコールバック（簡易版）
            def progress_callback(message: str, current: int, total: int) -> None:
                pass  # 統合時は内部進捗のため簡素化

            return await session_use_case.execute(analysis_request, progress_callback)

        except Exception as e:
            # Claude分析失敗時はローカル評価のみで継続
            self.logger.warning("Claude分析統合に失敗しました: %s", e)
            return None

    def _merge_claude_results_with_local(
        self, local_batch: A31EvaluationBatch, claude_result: dict
    ) -> A31EvaluationBatch:
        """ローカル評価結果とClaude分析結果をマージ

        Args:
            local_batch: ローカル評価結果
            claude_result: Claude分析結果

        Returns:
            A31EvaluationBatch: マージされた評価結果
        """
        if not claude_result:
            return local_batch

        # ローカル結果をベースに、Claude分析で改善提案を追加
        merged_results = local_batch.results.copy()

        for item_id, claude_item_result in claude_result.get("item_results", {}).items():
            if item_id in merged_results:
                local_result = merged_results[item_id]

                # Claude改善提案をローカル結果に統合
                if hasattr(local_result, "claude_improvements"):
                    local_result.claude_improvements = claude_item_result.improvements
                else:
                    # 動的属性追加
                    local_result.claude_improvements = claude_item_result.improvements

                # Claude分析スコアで補強（より高い信頼度のスコアを採用）
                if claude_item_result.analysis_score > local_result.score:
                    local_result.score = max(local_result.score, claude_item_result.analysis_score)

                # 問題点も統合
                if hasattr(local_result, "claude_issues"):
                    local_result.claude_issues = claude_item_result.issues_found
                else:
                    local_result.claude_issues = claude_item_result.issues_found

        # 🔧 修正: 正しいコンストラクタパラメータを使用
        return A31EvaluationBatch(
            results=merged_results,
            total_items=local_batch.total_items,
            evaluated_items=local_batch.evaluated_items,
            execution_time_ms=local_batch.execution_time_ms,
        )

    async def execute_by_category(
        self, request: A31CompleteCheckRequest, target_category: A31EvaluationCategory
    ) -> A31CompleteCheckResponse:
        """カテゴリ別チェックの実行

        Args:
            request: チェックリクエスト
            target_category: 対象カテゴリ

        Returns:
            A31CompleteCheckResponse: チェック結果
        """
        # リクエストを単一カテゴリに限定
        category_request = A31CompleteCheckRequest(
            project_name=request.project_name,
            episode_number=request.episode_number,
            target_categories=[target_category],
            include_auto_fix=request.include_auto_fix,
            fix_level=request.fix_level,
        )

        return await self.execute(category_request)

    def get_evaluation_summary(self, response: A31CompleteCheckResponse) -> dict[str, any]:
        """評価結果サマリーの生成

        Args:
            response: チェック結果

        Returns:
            dict[str, any]: サマリー情報
        """
        if not response.success:
            return {"success": False, "error": response.error_message}

        batch = response.evaluation_batch
        category_stats = batch.get_category_statistics()

        return {
            "success": True,
            "overall_score": response.get_overall_score(),
            "pass_rate": response.get_pass_rate(),
            "total_items": response.total_items_checked,
            "passed_items": len(batch.filter_passed_items()),
            "failed_items": len(batch.filter_failed_items()),
            "category_breakdown": {
                category.value: {
                    "count": stats["count"],
                    "pass_rate": stats["pass_rate"],
                    "average_score": stats["average_score"],
                }
                for category, stats in category_stats.items()
            },
            "execution_time_ms": batch.get_total_execution_time(),
        }

    def _get_episode_content(self, project_name: str, episode_number: int) -> str:
        """エピソード内容の取得"""
        try:
            return self._episode_repository.get_episode_content(project_name, episode_number)

        except FileNotFoundError as e:
            msg = f"エピソード {episode_number} が見つかりません: {project_name}"
            raise FileNotFoundError(msg) from e

    def _get_checklist_items(
        self, project_name: str, target_categories: list[A31EvaluationCategory]
    ) -> list[A31ChecklistItem]:
        """チェックリスト項目の取得"""
        # 全項目を取得
        all_items = self._a31_checklist_repository.get_all_checklist_items(project_name)

        if not target_categories:
            return all_items

        # カテゴリでフィルタリング
        filtered_items = []
        for item in all_items:
            item_category = self._evaluation_engine._get_category_from_item_type(item.item_type)
            if item_category in target_categories:
                filtered_items.append(item)

        return filtered_items

    def _prepare_evaluation_context(self, project_name: str, episode_number: int) -> dict[str, any]:
        """評価コンテキストの準備"""
        try:
            # プロジェクト設定の取得
            project_config: dict[str, Any] = self._project_repository.get_project_config(project_name)

            # 前話情報の取得(利用可能な場合)
            previous_episode_content = None
            if episode_number > 1:
                with contextlib.suppress(FileNotFoundError):
                    previous_episode_content = self._episode_repository.get_episode_content(
                        project_name, episode_number - 1
                    )

            return {
                "project_name": project_name,
                "episode_number": episode_number,
                "project_config": project_config,
                "previous_episode_content": previous_episode_content,
                "characters": project_config.get("characters", {}),
                "terminology": project_config.get("terminology", {}),
                "quality_threshold": project_config.get("quality_threshold", 70.0),
            }

        except Exception:
            # エラーの場合は最小限のコンテキストを返す
            return {"project_name": project_name, "episode_number": episode_number, "quality_threshold": 70.0}

    def _save_checklist_results(
        self, project_name: str, episode_number: int, evaluation_batch: A31EvaluationBatch
    ) -> Path:
        """チェックリスト結果の保存"""
        try:
            # エピソードタイトルを取得
            episode_title = self._get_episode_title(project_name, episode_number)

            # プロジェクトルートパスを取得
            project_root = self._get_project_root_path(project_name)

            # まずエピソード用チェックリストファイルを作成
            checklist_file_path = self._a31_checklist_repository.create_episode_checklist(
                episode_number, episode_title, project_root
            )

            # 評価結果も別途保存(統計・レポート用)
            self._a31_checklist_repository.save_evaluation_results(project_name, episode_number, evaluation_batch)

            return checklist_file_path

        except Exception as e:
            # 保存に失敗しても処理は継続(ログに記録)
            self.logger.warning("チェックリスト結果の保存に失敗しました: %s", e)
            return Path(f"temp/a31_checklist_episode_{episode_number}.yaml")

    def _get_episode_title(self, project_name: str, episode_number: int) -> str:
        """エピソードタイトルの取得

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            str: エピソードタイトル
        """
        try:
            # 🔧 修正: 実際のファイル名からタイトルを抽出
            actual_file_path = self._find_actual_episode_file(episode_number)
            if actual_file_path and actual_file_path.exists():
                # ファイル名から: 第XXX話_タイトル.md → タイトル
                filename = actual_file_path.stem
                if "_" in filename:
                    parts = filename.split("_", 1)
                    if len(parts) > 1:
                        return parts[1]

            # フォールバック: エピソード管理データから取得
            episodes = self._episode_repository.get_all_episodes(project_name)
            for episode in episodes:
                if episode.get("number") == episode_number:
                    return episode.get("title", f"第{episode_number:03d}話")

        except Exception as e:
            # エラーの場合はデフォルトタイトルを返す(ログ記録)
            self.logger.warning("エピソードタイトル取得エラー: %s", e)

        return f"第{episode_number:03d}話"

    def _get_project_root_path(self, project_name: str) -> Path:
        """プロジェクトルートパスの取得

        Args:
            project_name: プロジェクト名

        Returns:
            Path: プロジェクトルートパス
        """
        # まず、episode_repositoryが持つproject_rootを使用(CLIから渡された正しいパス)
        if hasattr(self._episode_repository, "project_root"):
            project_root = self._episode_repository.project_root
            if project_root and project_root.exists():
                return project_root

        # 次に、project_repositoryから取得を試みる
        try:
            project_root = self._project_repository.get_project_root(project_name)
            if project_root and project_root.exists():
                return project_root
        except Exception as e:
            # プロジェクトルート取得エラー(ログ記録)
            self.logger.warning("プロジェクトルート取得エラー: %s", e)

        # フォールバック: project_repositoryのproject_rootから推定
        if hasattr(self._project_repository, "project_root"):
            repo_root = self._project_repository.project_root
            project_path = repo_root / project_name
            if project_path.exists():
                return project_path

        # 最終フォールバック: 現在のディレクトリから相対パス
        return Path(f"projects/{project_name}")

    def _find_actual_episode_file(self, episode_number: int) -> Path | None:
        """実際のエピソードファイルを検索

        Args:
            episode_number: エピソード番号

        Returns:
            Path | None: 見つかったファイルパス、見つからない場合はNone
        """
        try:
            # プロジェクトルートの取得
            if hasattr(self._episode_repository, "project_root"):
                project_root = self._episode_repository.project_root
            else:
                project_root = Path()

            # パスサービス使用（DI注入による依存性解決）
            path_service = self.get_path_service(project_root)
            # まず統一パスで確認
            candidate = path_service.get_manuscript_path(episode_number)
            if candidate.exists():
                return candidate

            # フォールバック: パターン探索
            manuscript_dir = path_service.get_manuscript_dir()
            if not manuscript_dir.exists():
                return None
            import glob
            pattern = f"第{episode_number:03d}話_*.md"
            search_path = str(manuscript_dir / pattern)
            matching_files = glob.glob(search_path)
            if matching_files:
                return Path(matching_files[0])
            return None

        except Exception:
            return None

    def _update_episode_content(self, project_name: str, episode_number: int, new_content: str) -> None:
        """エピソード内容の更新(自動修正後)

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            new_content: 新しい内容
        """
        try:
            self._episode_repository.update_episode_content(project_name, episode_number, new_content)

        except Exception as e:
            self.logger.warning("エピソード内容の更新に失敗しました: %s", e)

    def _apply_auto_fixes(
        self,
        request: A31CompleteCheckRequest,
        content: str,
        evaluation_batch: A31EvaluationBatch,
        checklist_items: list[A31ChecklistItem],
    ) -> tuple[int, str]:
        """自動修正処理の実行

        Args:
            request: チェックリクエスト
            content: 元のコンテンツ
            evaluation_batch: 評価結果
            checklist_items: チェックリスト項目

        Returns:
            tuple[int, str]: (修正件数, 修正後コンテンツ)
        """

        auto_fix_service = A31AutoFixService()

        # FixLevelの変換
        fix_level_map = {"safe": FixLevel.SAFE, "standard": FixLevel.STANDARD, "aggressive": FixLevel.INTERACTIVE}
        fix_level = fix_level_map.get(request.fix_level, FixLevel.SAFE)

        # 評価結果をEvaluationResult形式に変換
        evaluation_results = {}
        for item_id, result in evaluation_batch.results.items():
            # 簡易的なEvaluationResult変換
            evaluation_results[item_id] = type(
                "EvaluationResult",
                (),
                {"passed": result.passed, "current_score": result.score, "details": result.details},
            )()

        # 自動修正の実行
        fixed_content, fix_results = auto_fix_service.apply_fixes(
            content, evaluation_results, checklist_items, fix_level
        )

        if fixed_content != content:
            auto_fixes_applied = len([r for r in fix_results if r.fix_applied])
            return auto_fixes_applied, fixed_content

        return 0, content

    def _apply_integrated_auto_fixes(
        self,
        request: A31CompleteCheckRequest,
        content: str,
        evaluation_batch: A31EvaluationBatch,
        checklist_items: list[A31ChecklistItem],
    ) -> tuple[int, str]:
        """統合自動修正処理の実行(標準修正器 + Claude Code統合)

        Args:
            request: チェックリクエスト
            content: 元のコンテンツ
            evaluation_batch: 評価結果
            checklist_items: チェックリスト項目

        Returns:
            tuple[int, str]: (修正件数, 修正後コンテンツ)
        """
        # Phase 1: 標準自動修正器による処理
        standard_fixes_applied, partially_fixed_content = self._apply_standard_fixes(
            request, content, evaluation_batch, checklist_items
        )

        # Phase 2: Claude Code による追加修正(失敗項目対象)
        claude_fixes_applied, fully_fixed_content = self._apply_claude_code_fixes(
            request, partially_fixed_content, evaluation_batch, checklist_items
        )

        total_fixes = standard_fixes_applied + claude_fixes_applied
        return total_fixes, fully_fixed_content

    def _apply_standard_fixes(
        self,
        request: A31CompleteCheckRequest,
        content: str,
        evaluation_batch: A31EvaluationBatch,
        checklist_items: list[A31ChecklistItem],
    ) -> tuple[int, str]:
        """標準自動修正器による修正処理

        Args:
            request: チェックリクエスト
            content: 元のコンテンツ
            evaluation_batch: 評価結果
            checklist_items: チェックリスト項目

        Returns:
            tuple[int, str]: (修正件数, 修正後コンテンツ)
        """
        auto_fix_service = A31AutoFixService()

        # FixLevelの変換
        fix_level_map = {"safe": FixLevel.SAFE, "standard": FixLevel.STANDARD, "aggressive": FixLevel.INTERACTIVE}
        fix_level = fix_level_map.get(request.fix_level, FixLevel.SAFE)

        # 評価結果をEvaluationResult形式に変換
        evaluation_results = {}
        for item_id, result in evaluation_batch.results.items():
            evaluation_results[item_id] = type(
                "EvaluationResult",
                (),
                {"passed": result.passed, "current_score": result.score, "details": result.details},
            )()

        # 標準自動修正の実行
        fixed_content, fix_results = auto_fix_service.apply_fixes(
            content, evaluation_results, checklist_items, fix_level
        )

        if fixed_content != content:
            auto_fixes_applied = len([r for r in fix_results if r.fix_applied])
            return auto_fixes_applied, fixed_content

        return 0, content

    def _apply_claude_code_fixes(
        self,
        request: A31CompleteCheckRequest,
        content: str,
        evaluation_batch: A31EvaluationBatch,
        checklist_items: list[A31ChecklistItem],
    ) -> tuple[int, str]:
        """Claude Codeによる自動修正処理

        Args:
            request: チェックリクエスト
            content: 部分修正済みコンテンツ
            evaluation_batch: 評価結果
            checklist_items: チェックリスト項目

        Returns:
            tuple[int, str]: (修正件数, 修正後コンテンツ)
        """
        try:
            # Claude Code評価サービスの初期化
            from noveler.domain.services.claude_code_evaluation_service import ClaudeCodeEvaluationService

            claude_service = ClaudeCodeEvaluationService()

            # 失敗項目のうち、Claude Code で修正可能なものを抽出
            failed_items = evaluation_batch.filter_failed_items()
            claude_fixable_items = [
                item for item in checklist_items
                if item.item_id in failed_items and (
                    item.item_type == ChecklistItemType.CLAUDE_CODE_EVALUATION or not item.is_auto_fixable()
                )  # 標準修正器で処理できないもの
            ]

            if not claude_fixable_items:
                return 0, content

            # Claude Code による段階的修正実行
            fixes_applied = 0
            current_content = content

            for item in claude_fixable_items:
                try:
                    # 修正リクエスト作成
                    fix_request = self._create_claude_fix_request(item, current_content, request)

                    # Claude Code による修正実行
                    fix_result = claude_service.apply_fix(fix_request)

                    if fix_result.success:
                        current_content = fix_result.fixed_content
                        fixes_applied += 1

                        # 修正ログ出力
                        self._log_claude_fix_applied(item, fix_result)

                except Exception as e:
                    # Claude Code 修正失敗時のログ出力
                    self._log_claude_fix_error(item, str(e))
                    continue

            return fixes_applied, current_content

        except ImportError:
            # ClaudeCodeEvaluationServiceが利用できない場合
            return 0, content
        except Exception:
            # その他のエラー時
            return 0, content

    def _create_claude_fix_request(
        self, item: A31ChecklistItem, content: str, request: A31CompleteCheckRequest
    ) -> dict[str, Any]:
        """Claude Code修正リクエストの作成

        Args:
            item: チェックリスト項目
            content: 修正対象コンテンツ
            request: 元のチェックリクエスト

        Returns:
            dict[str, Any]: Claude Code修正リクエスト
        """
        return {
            "item": item,
            "content": content,
            "context": {
                "project_name": request.project_name,
                "episode_number": request.episode_number,
                "fix_level": request.fix_level,
                "fix_mode": "auto_correction",
            },
        }

    def _log_claude_fix_applied(self, item: A31ChecklistItem, fix_result: Any) -> None:
        """Claude Code修正適用ログ

        Args:
            item: チェックリスト項目
            fix_result: 修正結果
        """
        # 実装は後で追加

    def _log_claude_fix_error(self, item: A31ChecklistItem, error_message: str) -> None:
        """Claude Code修正エラーログ

        Args:
            item: チェックリスト項目
            error_message: エラーメッセージ
        """
        # 実装は後で追加

class A31CompleteCheckUseCaseError(Exception):
    """A31完全チェックユースケースエラー"""

class EpisodeContentNotFoundError(A31CompleteCheckUseCaseError):
    """エピソード内容未発見エラー"""

class ChecklistItemsNotFoundError(A31CompleteCheckUseCaseError):
    """チェックリスト項目未発見エラー"""

class EvaluationExecutionError(A31CompleteCheckUseCaseError):
    """評価実行エラー"""
