#!/usr/bin/env python3
"""Implements the automated A31 checklist fixing workflow."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noveler.domain.interfaces.console_service_protocol import IConsoleService
    from noveler.domain.interfaces.path_service_protocol import IPathService

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.entities.a31_checklist_item import A31ChecklistItem
from noveler.domain.entities.auto_fix_session import AutoFixSession
from noveler.domain.services.a31_auto_fix_service import A31AutoFixService
from noveler.domain.services.a31_evaluation_service import A31EvaluationService
from noveler.domain.value_objects.a31_evaluation_result import EvaluationResult
from noveler.domain.value_objects.a31_fix_level import FixLevel
from noveler.domain.value_objects.a31_session_id import SessionId


class A31AutoFixUseCase(AbstractUseCase[object, AutoFixSession]):
    """Run the automated A31 checklist fix workflow for an episode."""

    def __init__(
        self,
        logger_service=None,
        unit_of_work=None,
        *,
        console_service: "IConsoleService" | None = None,
        path_service: "IPathService" | None = None,
        episode_repository=None,
        project_repository=None,
        evaluation_service: A31EvaluationService | None = None,
        auto_fix_service: A31AutoFixService | None = None,
        a31_checklist_repository=None,
        **legacy_kwargs,
    ) -> None:
        """Initialise the use case with required infrastructure services.

        Args:
            logger_service (ILoggerService): Logger used for diagnostics.
            unit_of_work (IUnitOfWork): Unit of Work coordinating repositories.
            console_service (IConsoleService, optional): Console writer used for
                status output. Defaults to ``None``.
            path_service (IPathService, optional): Path helper for project
                lookups. Defaults to ``None``.
        """
        # 基底クラス初期化（共通サービス）
        super().__init__(
            logger_service=logger_service,
            unit_of_work=unit_of_work,
            console_service=console_service,
            path_service=path_service,
            **legacy_kwargs,
        )

        if self.unit_of_work is None:
            if episode_repository is None or project_repository is None:
                msg = "unit_of_work または episode_repository/project_repository を指定してください"
                raise ValueError(msg)

            from noveler.infrastructure.unit_of_work import UnitOfWork

            unit_of_work = UnitOfWork(
                episode_repository=episode_repository,
                project_repository=project_repository,
            )
        else:
            unit_of_work = self.unit_of_work

        self._unit_of_work = unit_of_work
        self._episode_repository = episode_repository or getattr(unit_of_work, "episode_repository", None)
        self._project_repository = project_repository or getattr(unit_of_work, "project_repository", None)

        if self._episode_repository is None or self._project_repository is None:
            msg = "A31AutoFixUseCase には episode_repository と project_repository が必要です"
            raise ValueError(msg)

        self._logger_service = self.logger_service
        self._console_service = self.console_service
        self._evaluation_service = evaluation_service
        self._auto_fix_service = auto_fix_service
        self._checklist_repository = a31_checklist_repository

    def execute(
        self, project_name: str, episode_number: int, fix_level: FixLevel, items_to_fix: list[str]
    ) -> AutoFixSession:
        """Execute the automatic fixing workflow for the provided episode."""
        self._logger_service.info(f"A31自動修正開始: {project_name} #{episode_number}")

        with self._unit_of_work.transaction():
            try:
                episode_content = self._unit_of_work.episode_repository.get_episode_content(
                    project_name, episode_number
                )

                checklist_items = self._project_repository.get_checklist_items(project_name, items_to_fix)
                if not checklist_items:
                    msg = "指定されたチェックリスト項目が見つかりません"
                    raise ValueError(msg)

                session_id = SessionId.generate()
                target_file = self._get_episode_file_path(project_name, episode_number)
                session = AutoFixSession(
                    session_id=session_id, target_file=target_file, fix_level=fix_level, items_to_fix=items_to_fix
                )

                evaluation_service = self._create_evaluation_service()
                auto_fix_service = self._create_auto_fix_service()

                evaluation_results = evaluation_service.evaluate_all_items(
                    checklist_items, episode_content, self._get_project_metadata(project_name)
                )

                fixed_content, fix_results = auto_fix_service.apply_fixes(
                    episode_content, evaluation_results, checklist_items, fix_level
                )

                for fix_result in fix_results:
                    session.add_result(fix_result)

                if fixed_content != episode_content:
                    self.save_fixed_content(session, fixed_content)

                if self._checklist_repository is not None:
                    base_path = getattr(self._project_repository, "base_path", None)
                    project_root = Path(base_path) / project_name if base_path else self._get_project_root_path(project_name)
                    if not project_root.exists():
                        project_root = self._get_project_root_path(project_name)
                    episode_title = self._get_episode_title(project_name, episode_number)
                    checklist_path = self._checklist_repository.create_episode_checklist(
                        episode_number, episode_title, project_root
                    )
                    self._checklist_repository.save_results(session, checklist_path)

                session.complete()

                self._logger_service.info(f"A31自動修正完了: セッション{session_id.value}")
                return session

            except Exception as e:
                self._logger_service.error(f"A31自動修正エラー: {e}")
                raise

    def _create_evaluation_service(self) -> A31EvaluationService:
        """Return a new instance of the A31 evaluation service."""
        # ドメインサービスは依存関係なしで生成可能
        if self._evaluation_service is None:
            self._evaluation_service = A31EvaluationService()
        return self._evaluation_service

    def _create_auto_fix_service(self) -> A31AutoFixService:
        """Return a new instance of the A31 auto fix service."""
        # ドメインサービスは依存関係なしで生成可能
        if self._auto_fix_service is None:
            self._auto_fix_service = A31AutoFixService()
        return self._auto_fix_service

    def save_fixed_content(self, session: AutoFixSession, fixed_content: str) -> None:
        """Persist the fixed manuscript content for the session.

        Args:
            session (AutoFixSession): Session describing the target file.
            fixed_content (str): Updated manuscript content.
        """
        self._unit_of_work.episode_repository.save_episode_content(session.target_file, fixed_content)

    def _get_project_root_path(self, project_name: str) -> Path:
        """Resolve the project root path for the given project name.

        Args:
            project_name (str): Project identifier.

        Returns:
            Path: Absolute project root path.
        """
        # プロジェクトリポジトリから設定を取得し、プロジェクトルートを特定
        config = self._project_repository.get_project_config(project_name)

        # 設定からプロジェクトルートを取得
        if "project_root" in config:
            return Path(config["project_root"])

        # プロジェクトリポジトリから直接プロジェクトルートを取得
        project_root = self._project_repository.get_project_root(project_name)
        if project_root and project_root.exists():
            return project_root

        # フォールバック: プロジェクトリポジトリのproject_rootから推定
        if hasattr(self._project_repository, "project_root"):
            repo_root = self._project_repository.project_root
            project_path = repo_root / project_name
            if project_path.exists():
                return project_path

        # 最終フォールバック: 現在のディレクトリからの相対パス
        return Path(f"projects/{project_name}")

    def _get_episode_title(self, project_name: str, episode_number: int) -> str:
        """Lookup the episode title from the project metadata.

        Args:
            project_name (str): Project identifier.
            episode_number (int): Episode number to inspect.

        Returns:
            str: Episode title or a fallback label when not present.
        """
        try:
            # エピソード管理データからタイトルを取得
            episode_management = self._project_repository.get_episode_management(project_name)
            episodes = episode_management.get("episodes", [])

            for episode in episodes:
                if episode.get("number") == episode_number:
                    return episode.get("title", f"第{episode_number:03d}話")

        except Exception as e:
            # エラーの場合はデフォルトタイトルを返す(ログ記録)
            self.logger.warning("エピソードタイトル取得エラー: %s", e)

        return f"第{episode_number:03d}話"

    def generate_session_report(self, session: AutoFixSession) -> str:
        """セッションレポートの生成

        Args:
            session: 修正セッション

        Returns:
            str: レポート文字列
        """
        report_lines = [
            "=" * 50,
            "A31自動修正セッション完了",
            "=" * 50,
            f"セッションID: {session.session_id.value}",
            f"対象ファイル: {session.target_file}",
            f"修正レベル: {session.fix_level.value}",
            f"処理時間: {session.get_duration()}秒",
            "",
            "📊 修正結果サマリー:",
            f"  - 成功: {session.get_successful_fixes_count()}件",
            f"  - 失敗: {session.get_failed_fixes_count()}件",
            f"  - 総改善点: {session.get_total_improvement():.1f}点",
            "",
        ]

        # 個別修正結果の詳細
        if session.results:
            report_lines.append("🔧 修正詳細:")
            for result in session.results:
                status = "✅" if result.fix_applied else "❌"
                report_lines.append(f"  {status} {result.item_id} ({result.fix_type})")

                if result.fix_applied and result.changes_made:
                    report_lines.extend(f"    - {change}" for change in result.changes_made)

                    improvement = result.after_score - result.before_score
                    if improvement > 0:
                        report_lines.append(f"    💡 スコア改善: {improvement:.1f}点")

                report_lines.append("")

        # 改善提案の追加
        auto_fix_service = self._create_auto_fix_service()
        suggestions = auto_fix_service.generate_improvement_suggestions(
            self._get_evaluation_results_from_session(session), self._get_checklist_items_from_session(session)
        )

        if suggestions:
            report_lines.append("💭 改善提案:")
            report_lines.extend(f"  - {suggestion}" for suggestion in suggestions)
            report_lines.append("")

        report_lines.append("=" * 50)

        return "\n".join(report_lines)

    def _get_episode_file_path(self, project_name: str, episode_number: int) -> Path:
        """エピソードファイルパスの取得"""
        # 共通基盤の命名規則に統一
        try:
            path_service = self.get_path_service()
            return path_service.get_manuscript_path(episode_number)
        except Exception:
            # フォールバック: 旧来のパス（互換用）
            return Path(f"{project_name}/40_原稿/第{episode_number:03d}話_タイトル.md")

    def _get_project_metadata(self, _project_name: str) -> dict[str, any]:
        """プロジェクトメタデータの取得"""
        # 実際の実装では、プロジェクト設定やキャラクター情報等を取得
        return {"quality_score": 75.0, "characters": {}, "terminology": {}}

    def _get_evaluation_results_from_session(self, session: AutoFixSession) -> dict[str, EvaluationResult]:
        """セッションから評価結果を復元"""
        # 実際の実装では、セッションに保存された評価結果を取得
        # ここでは簡易的な実装
        evaluation_results = {}

        for result in session.results:
            evaluation_results[result.item_id] = EvaluationResult.create_failed_result(
                item_id=result.item_id,
                current_score=result.before_score,
                threshold_value=result.after_score,
                details={},
            )

        return evaluation_results

    def _get_checklist_items_from_session(self, _session: AutoFixSession) -> list[A31ChecklistItem]:
        """セッションからチェックリスト項目を復元"""
        # 実際の実装では、より詳細な復元処理が必要
        # ここでは空のリストを返す
        return []

class A31AutoFixUseCaseError(Exception):
    """A31自動修正ユースケースエラー"""

class EpisodeNotFoundError(A31AutoFixUseCaseError):
    """エピソード未発見エラー"""

class InvalidChecklistItemError(A31AutoFixUseCaseError):
    """無効なチェックリスト項目エラー"""

class FixLevelNotSupportedError(A31AutoFixUseCaseError):
    """修正レベル未対応エラー"""
