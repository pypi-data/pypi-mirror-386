"""プロット関連イベントハンドラー

SPEC-901-DDD-REFACTORING対応:
- プロット関連ドメインイベントの副作用処理
- 非同期イベント処理によるスケーラビリティ向上
"""

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noveler.domain.interfaces import IConfigurationService, ILoggerService


from noveler.domain.events.plot_events import (
    MasterPlotUpdated,
    PlotGenerationCompleted,
    PlotGenerationFailed,
    PlotGenerationStarted,
    PlotQualityCheckCompleted,
    PlotSaved,
)


class PlotGenerationEventHandler:
    """プロット生成イベントハンドラー

    プロット生成に関連する副作用処理を担当
    """

    def __init__(
        self,
        logger_service: "ILoggerService",
        config_service: "IConfigurationService"
    ) -> None:
        """ハンドラー初期化

        Args:
            logger_service: ロガーサービス
            config_service: 設定サービス
        """
        self.logger_service = logger_service
        self.config_service = config_service

    def handle_generation_started(self, event: PlotGenerationStarted) -> None:
        """プロット生成開始イベント処理

        Args:
            event: プロット生成開始イベント
        """
        self.logger_service.info(
            f"プロット生成開始通知: episode={event.episode_number}, "
            f"mode={event.generation_mode}, command_id={event.command_id}"
        )

        # 進行状況ログ出力
        if event.episode_number:
            self.logger_service.info(f"第{event.episode_number}話のプロット生成を開始します")

        # 統計情報記録（オプション）
        self._record_generation_metrics("started", event)

    def handle_generation_completed(self, event: PlotGenerationCompleted) -> None:
        """プロット生成完了イベント処理

        Args:
            event: プロット生成完了イベント
        """
        self.logger_service.info(
            f"プロット生成完了通知: path={event.plot_file_path}, "
            f"quality_score={event.quality_score}, command_id={event.command_id}"
        )

        # 成功統計更新
        self._record_generation_metrics("completed", event)

        # 品質スコアが低い場合の警告
        if event.quality_score and event.quality_score < 0.7:
            self.logger_service.warning(
                f"プロット品質スコアが低いです: {event.quality_score:.2f} "
                f"(推奨: 0.7以上) - {event.plot_file_path}"
            )

    def handle_generation_failed(self, event: PlotGenerationFailed) -> None:
        """プロット生成失敗イベント処理

        Args:
            event: プロット生成失敗イベント
        """
        self.logger_service.error(
            f"プロット生成失敗通知: error={event.error_message}, "
            f"type={event.error_type}, retry_count={event.retry_count}, "
            f"command_id={event.command_id}"
        )

        # エラー統計更新
        self._record_generation_metrics("failed", event)

        # 自動復旧処理（オプション）
        if event.retry_count < 3 and event.error_type in ["NetworkError", "TimeoutError"]:
            self.logger_service.info(f"自動復旧を検討中: {event.command_id}")
            # ここで復旧処理トリガーを発行可能

    async def handle_generation_started_async(self, event: PlotGenerationStarted) -> None:
        """非同期プロット生成開始イベント処理"""
        # 同期版を非同期で実行
        await asyncio.to_thread(self.handle_generation_started, event)

    async def handle_generation_completed_async(self, event: PlotGenerationCompleted) -> None:
        """非同期プロット生成完了イベント処理"""
        await asyncio.to_thread(self.handle_generation_completed, event)

    async def handle_generation_failed_async(self, event: PlotGenerationFailed) -> None:
        """非同期プロット生成失敗イベント処理"""
        await asyncio.to_thread(self.handle_generation_failed, event)

    def _record_generation_metrics(self, status: str, event) -> None:
        """生成メトリクス記録（統計用）

        Args:
            status: ステータス（started, completed, failed）
            event: 対象イベント
        """
        # 簡単な統計記録処理
        # 実際の実装では、メトリクス収集システムに送信
        self.logger_service.debug(f"生成メトリクス記録: {status} - {event.event_id}")


class PlotQualityEventHandler:
    """プロット品質チェックイベントハンドラー

    品質チェック結果に基づく副作用処理
    """

    def __init__(
        self,
        logger_service: "ILoggerService",
        config_service: "IConfigurationService"
    ) -> None:
        self.logger_service = logger_service
        self.config_service = config_service

    def handle_quality_check_completed(self, event: PlotQualityCheckCompleted) -> None:
        """品質チェック完了イベント処理

        Args:
            event: 品質チェック完了イベント
        """
        self.logger_service.info(
            f"品質チェック完了: {event.plot_file_path}, "
            f"score={event.quality_score:.3f}, "
            f"passed={event.passed_validation}"
        )

        # 品質基準未達成時の対応
        if not event.passed_validation:
            self.logger_service.warning(
                f"品質基準未達成 ({event.quality_score:.3f}): {event.plot_file_path}"
            )

            # 改善提案ログ出力
            self._suggest_quality_improvements(event)

    def _suggest_quality_improvements(self, event: PlotQualityCheckCompleted) -> None:
        """品質改善提案

        Args:
            event: 品質チェック完了イベント
        """
        metrics = event.quality_metrics
        suggestions = []

        # メトリクスに基づく提案生成
        if metrics.get("content_length", 0) < 200:
            suggestions.append("プロット内容をより詳細に記述してください")

        if not metrics.get("has_title", False):
            suggestions.append("タイトルを設定してください")

        if not metrics.get("has_structure", False):
            suggestions.append("基本構成を明確にしてください")

        if metrics.get("paragraph_count", 0) < 3:
            suggestions.append("段落を増やして構造を明確にしてください")

        for suggestion in suggestions:
            self.logger_service.info(f"改善提案: {suggestion}")


class PlotFileEventHandler:
    """プロットファイル操作イベントハンドラー

    ファイル保存・更新に関する副作用処理
    """

    def __init__(
        self,
        logger_service: "ILoggerService"
    ) -> None:
        self.logger_service = logger_service

    def handle_plot_saved(self, event: PlotSaved) -> None:
        """プロット保存イベント処理

        Args:
            event: プロット保存イベント
        """
        self.logger_service.info(f"プロット保存完了: {event.file_path}")

        if event.backup_path:
            self.logger_service.info(f"バックアップ作成: {event.backup_path}")

        # ファイルサイズチェック
        file_path = Path(event.file_path)
        if file_path.exists():
            file_size = file_path.stat().st_size
            self.logger_service.debug(f"保存ファイルサイズ: {file_size} bytes")

            # 異常に小さいファイルの警告
            if file_size < 100:
                self.logger_service.warning(f"保存されたプロットが小さすぎます: {file_size} bytes")

    def handle_master_plot_updated(self, event: MasterPlotUpdated) -> None:
        """マスタープロット更新イベント処理

        Args:
            event: マスタープロット更新イベント
        """
        self.logger_service.info(
            f"マスタープロット更新完了: {event.master_plot_path}, "
            f"episodes={event.episode_count}, mode={event.integration_mode}"
        )

        # 更新セクション詳細ログ
        for section in event.updated_sections:
            self.logger_service.debug(f"更新セクション: {section}")

        # マスタープロット整合性チェック（オプション）
        self._verify_master_plot_integrity(event)

    def _verify_master_plot_integrity(self, event: MasterPlotUpdated) -> None:
        """マスタープロット整合性検証

        Args:
            event: マスタープロット更新イベント
        """
        try:
            master_path = Path(event.master_plot_path)
            if not master_path.exists():
                self.logger_service.error(f"マスタープロットファイルが見つかりません: {master_path}")
                return

            content = master_path.read_text(encoding="utf-8")

            # 基本整合性チェック
            if len(content.strip()) == 0:
                self.logger_service.warning("マスタープロットが空です")
            elif len(content) < 100:
                self.logger_service.warning("マスタープロットが短すぎる可能性があります")

            self.logger_service.debug("マスタープロット整合性チェック完了")

        except Exception as e:
            self.logger_service.exception(f"マスタープロット整合性チェックエラー: {e}")


# イベントハンドラー統合クラス
class PlotEventHandlerAggregate:
    """プロット関連イベントハンドラー統合クラス

    すべてのプロット関連イベントハンドラーを統合管理
    Message Bus登録を簡素化
    """

    def __init__(
        self,
        logger_service: "ILoggerService",
        config_service: "IConfigurationService"
    ) -> None:
        self.generation_handler = PlotGenerationEventHandler(logger_service, config_service)
        self.quality_handler = PlotQualityEventHandler(logger_service, config_service)
        self.file_handler = PlotFileEventHandler(logger_service)

    def get_event_handlers(self) -> dict:
        """Message Bus登録用のイベントハンドラー辞書を取得

        Returns:
            dict: イベントタイプをキー、ハンドラーリストを値とする辞書
        """
        return {
            PlotGenerationStarted: [self.generation_handler.handle_generation_started],
            PlotGenerationCompleted: [self.generation_handler.handle_generation_completed],
            PlotGenerationFailed: [self.generation_handler.handle_generation_failed],
            PlotQualityCheckCompleted: [self.quality_handler.handle_quality_check_completed],
            PlotSaved: [self.file_handler.handle_plot_saved],
            MasterPlotUpdated: [self.file_handler.handle_master_plot_updated]
        }

    def get_async_event_handlers(self) -> dict:
        """非同期Message Bus登録用のイベントハンドラー辞書を取得

        Returns:
            dict: イベントタイプをキー、非同期ハンドラーリストを値とする辞書
        """
        return {
            PlotGenerationStarted: [self.generation_handler.handle_generation_started_async],
            PlotGenerationCompleted: [self.generation_handler.handle_generation_completed_async],
            PlotGenerationFailed: [self.generation_handler.handle_generation_failed_async],
            # 他のイベントも必要に応じて非同期版を追加
        }
