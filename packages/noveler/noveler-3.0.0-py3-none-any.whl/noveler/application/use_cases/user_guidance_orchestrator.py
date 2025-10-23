#!/usr/bin/env python3
"""ユーザーガイダンスオーケストレーター

ユーザーガイダンス機能のビジネスロジックを調整し、
ドメインサービス間の協調を管理するアプリケーション層コンポーネント
"""

import sys
from pathlib import Path
from typing import Any

from noveler.domain.entities.error_context import ErrorContext, ErrorSeverity
from noveler.domain.entities.progress_report import ProgressReport
from noveler.domain.services.plot_progress_service import PlotProgressService
from noveler.domain.services.smart_error_handler_service import SmartErrorHandlerService
from noveler.domain.services.user_guidance_service import UserGuidanceService
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
# DDD準拠: Infrastructure層実装への直接依存は遅延初期化で回避


class UserGuidanceOrchestrator:
    """ユーザーガイダンスオーケストレーター"""

    def __init__(self, plot_progress_repository=None) -> None:
        """初期化

        Args:
            plot_progress_repository: プロット進捗リポジトリ（依存性注入）
        """
        self.guidance_service = UserGuidanceService()

        # DDD準拠: Infrastructure層実装への直接依存を回避（遅延初期化）
        self._plot_progress_repository = plot_progress_repository
        self._progress_service = None
        self.error_handler = SmartErrorHandlerService()

    @property
    def progress_service(self) -> Any:
        """プロット進捗サービスの遅延初期化

        DDD準拠: Infrastructure層への直接依存を回避
        """
        if self._progress_service is None:
            if self._plot_progress_repository is None:
                # フォールバック: 遅延初期化でInfrastructure層インポート
                from noveler.infrastructure.repositories.yaml_plot_progress_repository import YamlPlotProgressRepository

                plot_progress_repository = YamlPlotProgressRepository()
            else:
                plot_progress_repository = self._plot_progress_repository

            self._progress_service = PlotProgressService(plot_progress_repository)
        return self._progress_service

    def handle_prerequisite_error(
        self, stage: WorkflowStageType, missing_files: list[str], user_context: dict[str, Any] | None = None
    ) -> str:
        """前提条件エラーのハンドリング

        Args:
            stage: 影響を受ける段階
            missing_files: 不足ファイル
            user_context: ユーザーコンテキスト

        Returns:
            str: 統合されたユーザー向けメッセージ
        """
        # エラーコンテキストの構築
        error_context = ErrorContext(
            error_type="PREREQUISITE_MISSING",
            severity=ErrorSeverity.WARNING,
            affected_stage=stage,
            missing_files=missing_files,
            user_context=user_context or {},
        )

        # スマートエラーメッセージの生成
        error_message = self.error_handler.generate_smart_error_message(error_context)

        # ガイダンスの生成
        guidance = self.guidance_service.generate_prerequisite_guidance(error_context)

        # 統合メッセージの構築
        return f"{error_message}\n\n{guidance.generate_display()}"

    def generate_progress_report_with_guidance(self, project_root: Path) -> str:
        """進捗レポートと次のステップガイダンスを統合生成

        Args:
            project_root: プロジェクトルート

        Returns:
            str: 統合された進捗レポートとガイダンス
        """
        # 進捗分析
        progress_report = self.progress_service.analyze_project_progress(project_root)

        # 基本的な進捗レポート
        report_display = progress_report.generate_display()

        # 次のステップガイダンスの生成
        next_step_guidance = self._generate_next_step_guidance(progress_report)

        # 統合メッセージ
        if next_step_guidance:
            return f"{report_display}\n\n{next_step_guidance}"
        return report_display

    def handle_success_scenario(
        self,
        completed_stage: WorkflowStageType,
        created_files: list[str],
        project_context: dict[str, Any] | None = None,
    ) -> str:
        """成功シナリオのハンドリング

        Args:
            completed_stage: 完了した段階
            created_files: 作成されたファイル
            project_context: プロジェクトコンテキスト

        Returns:
            str: 成功メッセージとガイダンス
        """
        # 成功コンテキストの構築
        success_context = {
            "completed_stage": completed_stage,
            "created_files": created_files,
            **(project_context or {}),
        }

        # 成功ガイダンスの生成
        guidance = self.guidance_service.generate_success_guidance(success_context)

        # 成功メッセージの生成
        stage_name = self._get_stage_japanese_name(completed_stage)
        success_message = f"🎉 {stage_name}が正常に作成されました!"

        # 統合メッセージ
        return f"{success_message}\n\n{guidance.generate_display()}"

    def _generate_next_step_guidance(self, progress_report: ProgressReport) -> str | None:
        """次のステップガイダンスの生成"""
        # 推奨アクションがある場合
        recommended_action = progress_report.recommend_next_action()
        if recommended_action:
            return f"""
💡 推奨される次のアクション:
   {recommended_action.display_text()}

   実行コマンド: {recommended_action.command}
"""

        # 阻害要因がある場合
        if progress_report.has_blocking_issues():
            return """
⚠️ 進行を阻害している問題があります。
   まず既存の問題を解決してから次のステップに進みましょう。
"""

        # レビューが必要な場合
        if progress_report.needs_review():
            return """
📝 レビューが必要な項目があります。
   作成済みのファイルを確認・編集してから次に進みましょう。
"""

        # 完了している場合
        if progress_report.is_completed():
            return """
✅ プロット作成が完了しています!
   次は実際の執筆を開始しましょう: novel write 1
"""

        return None

    def _get_stage_japanese_name(self, stage: WorkflowStageType) -> str:
        """段階の日本語名を取得"""
        stage_names = {
            WorkflowStageType.MASTER_PLOT: "全体構成プロット",
            WorkflowStageType.CHAPTER_PLOT: "章別プロット",
            WorkflowStageType.EPISODE_PLOT: "話数別プロット",
        }
        return stage_names.get(stage, str(stage.value))
