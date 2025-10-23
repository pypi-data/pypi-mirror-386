#!/usr/bin/env python3
"""A31結果統合サービス

Claude分析結果をA31チェックリストに統合し、
改善提案のコメント追加と品質スコア更新を行うドメインサービス。
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Phase 6修正: Service → Repository循環依存解消のため、DI注入に変更
# from noveler.domain.repositories.file_backup_repository import FileBackupRepository
from typing import Any, Protocol

import yaml

from noveler.domain.entities.session_analysis_result import (
    AnalysisConfidence,
    AnalysisImprovement,
    ItemAnalysisResult,
    SessionAnalysisResult,
)


class IFileBackupRepository(Protocol):
    """ファイルバックアップリポジトリインターフェース（循環依存解消）"""

    def backup_file(self, file_path: Path) -> Path: ...
    def restore_file(self, backup_path: Path) -> None: ...


from noveler.domain.value_objects.a31_checklist_data import QualityChecklistData as A31ChecklistData
from noveler.domain.value_objects.project_time import project_now


class IntegrationMode(Enum):
    """統合モード"""

    APPEND_ONLY = "append_only"  # 追記のみ
    UPDATE_EXISTING = "update_existing"  # 既存更新
    REPLACE_ALL = "replace_all"  # 全置換
    MERGE_SMART = "merge_smart"  # スマートマージ


class IntegratedResultType(Enum):
    """統合結果タイプ"""

    IMPROVEMENT_COMMENT = "improvement_comment"
    SCORE_UPDATE = "score_update"
    STATUS_CHANGE = "status_change"
    METADATA_ADDITION = "metadata_addition"


@dataclass(frozen=True)
class IntegrationRequest:
    """統合リクエスト"""

    checklist_file_path: str
    session_result: SessionAnalysisResult
    integration_mode: IntegrationMode = IntegrationMode.MERGE_SMART
    confidence_threshold: AnalysisConfidence = AnalysisConfidence.MEDIUM
    backup_original: bool = True
    add_metadata: bool = True

    def __post_init__(self) -> None:
        """リクエスト妥当性検証"""
        if not Path(self.checklist_file_path).exists():  # TODO: IPathServiceを使用するように修正
            msg = f"チェックリストファイルが見つかりません: {self.checklist_file_path}"
            raise ValueError(msg)


@dataclass
class IntegrationResult:
    """統合結果"""

    success: bool
    integrated_items_count: int
    improvement_comments_added: int
    score_updates_count: int
    backup_file_path: str | None = None
    error_message: str | None = None
    integration_summary: dict[str, Any] | None = None

    def get_integration_rate(self, total_items: int) -> float:
        """統合率計算"""
        if total_items == 0:
            return 0.0
        return self.integrated_items_count / total_items


class ChecklistResultIntegrator:
    """A31結果統合サービス

    Claude分析結果をA31チェックリストに統合し、
    改善提案とスコア更新を自動実行するドメインサービス。
    """

    def __init__(self, backup_repository: IFileBackupRepository, project_root: Path | None = None) -> None:
        """統合サービス初期化

        Args:
            backup_repository (FileBackupRepository): バックアップリポジトリ（依存性注入）
            project_root: プロジェクトルートディレクトリ（互換性のため残存、新設計では不使用）
        """
        self._integration_history: list[IntegrationResult] = []

        # 統合統計
        self._integration_stats = {
            "total_integrations": 0,
            "successful_integrations": 0,
            "total_items_integrated": 0,
            "total_improvements_added": 0,
        }

        # 🔧 DDD準拠: 依存性注入によりバックアップリポジトリを受け取る
        self._backup_repository = backup_repository

    def integrate_analysis_results(
        self,
        request: IntegrationRequest,
    ) -> IntegrationResult:
        """分析結果統合実行

        Args:
            request: 統合リクエスト

        Returns:
            IntegrationResult: 統合結果
        """
        try:
            # バックアップ作成
            backup_path = None
            if request.backup_original:
                backup_path = self._create_backup(request.checklist_file_path)

            # チェックリストデータ読み込み
            checklist_data: dict[str, Any] = self._load_checklist_data(request.checklist_file_path)

            # 統合対象結果フィルタリング
            target_results = self._filter_integration_targets(request.session_result, request.confidence_threshold)

            # メイン統合処理
            integrated_items = 0
            improvement_comments = 0
            score_updates = 0

            for item_result in target_results.values():
                integration_success = self._integrate_single_item_result(
                    checklist_data, item_result, request.integration_mode
                )

                if integration_success:
                    integrated_items += 1
                    improvement_comments += len(item_result.improvements)

                    # スコア更新判定
                    if item_result.analysis_score > 0:
                        score_updates += 1

            # メタデータ追加
            if request.add_metadata:
                self._add_integration_metadata(checklist_data, request.session_result)

            # ファイル保存
            self._save_checklist_data(checklist_data, request.checklist_file_path)

            # 統合サマリー生成
            integration_summary = self._generate_integration_summary(request.session_result, target_results)

            # 結果構築
            result = IntegrationResult(
                success=True,
                integrated_items_count=integrated_items,
                improvement_comments_added=improvement_comments,
                score_updates_count=score_updates,
                backup_file_path=backup_path,
                integration_summary=integration_summary,
            )

            # 統計更新
            self._update_integration_stats(result)
            self._integration_history.append(result)

            return result

        except Exception as e:
            error_result = IntegrationResult(
                success=False,
                integrated_items_count=0,
                improvement_comments_added=0,
                score_updates_count=0,
                error_message=str(e),
            )

            self._integration_history.append(error_result)
            return error_result

    def _create_backup(self, original_file_path: str) -> str:
        """バックアップファイル作成

        プロジェクト固有のバックアップリポジトリを使用してバックアップを作成する。
        """
        original_path = Path(original_file_path)  # TODO: IPathServiceを使用するように修正

        # バックアップリポジトリを使用してプロジェクト固有の場所にバックアップ作成
        backup_name = f"A31_checklist_{original_path.stem}"
        backup_id = self._backup_repository.create_backup(original_path, backup_name)

        # バックアップ情報を取得してパスを返す
        backup_info = self._backup_repository.get_backup_info(backup_id)
        if backup_info and "backup_path" in backup_info:
            return backup_info["backup_path"]
        # フォールバック: バックアップIDが返された場合の対処
        return str(original_path) + ".backup"

    def _load_checklist_data(self, file_path: str) -> A31ChecklistData:
        """チェックリストデータ読み込み"""
        with Path(file_path).open(encoding="utf-8") as f:
            raw_data: dict[str, Any] = yaml.safe_load(f)

        return A31ChecklistData.from_yaml_data(raw_data)

    def _filter_integration_targets(
        self,
        session_result: SessionAnalysisResult,
        confidence_threshold: AnalysisConfidence,
    ) -> dict[str, ItemAnalysisResult]:
        """統合対象結果フィルタリング"""
        filtered_results = {}

        for item_id, item_result in session_result.item_results.items():
            # 信頼度フィルタリング
            if self._meets_confidence_threshold(item_result.confidence, confidence_threshold):
                filtered_results[item_id] = item_result

        return filtered_results

    def _meets_confidence_threshold(
        self,
        result_confidence: AnalysisConfidence,
        threshold: AnalysisConfidence,
    ) -> bool:
        """信頼度閾値判定"""
        confidence_levels = {
            AnalysisConfidence.LOW: 1,
            AnalysisConfidence.MEDIUM: 2,
            AnalysisConfidence.HIGH: 3,
            AnalysisConfidence.VERIFIED: 4,
        }

        return confidence_levels[result_confidence] >= confidence_levels[threshold]

    def _integrate_single_item_result(
        self,
        checklist_data: A31ChecklistData,
        item_result: ItemAnalysisResult,
        integration_mode: IntegrationMode,
    ) -> bool:
        """単一項目結果統合"""
        try:
            item_id = item_result.priority_item.item_id.value

            # チェックリスト内の該当項目を検索
            checklist_item = self._find_checklist_item(checklist_data, item_id)
            if not checklist_item:
                return False

            # 改善提案のコメント追加
            if item_result.improvements:
                self._add_improvement_comments(checklist_item, item_result.improvements, integration_mode)

            # スコア更新
            if item_result.analysis_score > 0:
                self._update_item_score(checklist_item, item_result.analysis_score, integration_mode)

            # 問題点記録
            if item_result.issues_found:
                self._add_issue_notes(checklist_item, item_result.issues_found, integration_mode)

            return True

        except Exception:
            return False

    def _find_checklist_item(
        self,
        checklist_data: A31ChecklistData,
        item_id: str,
    ) -> dict[str, Any] | None:
        """チェックリスト項目検索"""
        # チェックリストデータ内を項目ID で検索
        for phase_items in checklist_data.checklist_items.values():
            for item in phase_items:
                if isinstance(item, dict) and item.get("id") == item_id:
                    return item

        return None

    def _add_improvement_comments(
        self,
        checklist_item: dict[str, Any],
        improvements: list[AnalysisImprovement],
        integration_mode: IntegrationMode,
    ) -> None:
        """改善提案コメント追加（重複排除機能付き）"""
        if "claude_improvements" not in checklist_item:
            checklist_item["claude_improvements"] = []

        improvement_comments = []
        for improvement in improvements:
            comment = {
                "original": improvement.original_text,
                "improved": improvement.improved_text,
                "type": improvement.improvement_type,
                "confidence": improvement.confidence.value,
                "reasoning": improvement.reasoning,
                "generated_at": project_now().to_iso_string(),
            }
            improvement_comments.append(comment)

        if integration_mode == IntegrationMode.REPLACE_ALL:
            checklist_item["claude_improvements"] = improvement_comments
        else:
            # 重複チェックを実行してから追加
            existing_improvements = checklist_item["claude_improvements"]
            deduplicated_improvements = self._remove_duplicate_improvements(existing_improvements, improvement_comments)

            if integration_mode == IntegrationMode.MERGE_SMART:
                # MERGE_SMARTでは既存の重複も整理
                checklist_item["claude_improvements"] = deduplicated_improvements
            else:
                # 新しい非重複項目のみ追加
                new_improvements = [
                    imp
                    for imp in improvement_comments
                    if not self._is_duplicate_improvement(existing_improvements, imp)
                ]
                checklist_item["claude_improvements"].extend(new_improvements)

    def _remove_duplicate_improvements(
        self, existing_improvements: list[dict[str, Any]], new_improvements: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """重複する改善提案を除去し、最新かつ高品質なもののみを保持"""
        # 全ての改善提案を統合
        all_improvements = existing_improvements + new_improvements

        # 重複グループを作成（original + improved + type で判定）
        unique_improvements = {}

        for improvement in all_improvements:
            # 重複判定キー
            key = (
                improvement.get("original", "").strip(),
                improvement.get("improved", "").strip(),
                improvement.get("type", "").strip(),
            )

            if key not in unique_improvements:
                unique_improvements[key] = improvement
            else:
                # 既存の改善提案と比較して、より良いものを保持
                existing = unique_improvements[key]
                current = improvement

                # 信頼度比較
                confidence_priority = {"high": 3, "medium": 2, "low": 1}
                existing_conf = confidence_priority.get(existing.get("confidence", "low"), 1)
                current_conf = confidence_priority.get(current.get("confidence", "low"), 1)

                # より高い信頼度、または同じ信頼度なら新しいものを採用
                if current_conf > existing_conf or (
                    current_conf == existing_conf and current.get("generated_at", "") > existing.get("generated_at", "")
                ):
                    unique_improvements[key] = current

        # 生成日時でソート（新しい順）
        result = list(unique_improvements.values())
        result.sort(key=lambda x: x.get("generated_at", ""), reverse=True)

        return result

    def _is_duplicate_improvement(
        self, existing_improvements: list[dict[str, Any]], new_improvement: dict[str, Any]
    ) -> bool:
        """改善提案が重複しているかチェック"""
        new_key = (
            new_improvement.get("original", "").strip(),
            new_improvement.get("improved", "").strip(),
            new_improvement.get("type", "").strip(),
        )

        for existing in existing_improvements:
            existing_key = (
                existing.get("original", "").strip(),
                existing.get("improved", "").strip(),
                existing.get("type", "").strip(),
            )

            if new_key == existing_key:
                return True

        return False

    def _update_item_score(
        self,
        checklist_item: dict[str, Any],
        analysis_score: float,
        integration_mode: IntegrationMode,
    ) -> None:
        """項目スコア更新"""
        if "claude_analysis" not in checklist_item:
            checklist_item["claude_analysis"] = {}

        analysis_info = checklist_item["claude_analysis"]

        if integration_mode == IntegrationMode.REPLACE_ALL:
            analysis_info["score"] = analysis_score
        else:
            # 既存スコアとの統合
            existing_score = analysis_info.get("score", 0.0)
            if integration_mode == IntegrationMode.MERGE_SMART:
                # 高い方のスコアを採用
                analysis_info["score"] = max(existing_score, analysis_score)
            else:
                analysis_info["score"] = analysis_score

        analysis_info["last_updated"] = project_now().to_iso_string()

    def _add_issue_notes(
        self,
        checklist_item: dict[str, Any],
        issues: list[str],
        integration_mode: IntegrationMode,
    ) -> None:
        """問題点ノート追加"""
        if "claude_issues" not in checklist_item:
            checklist_item["claude_issues"] = []

        issue_entries = []
        for issue in issues:
            issue_entry = {"description": issue, "detected_at": project_now().to_iso_string()}
            issue_entries.append(issue_entry)

        if integration_mode == IntegrationMode.REPLACE_ALL:
            checklist_item["claude_issues"] = issue_entries
        else:
            checklist_item["claude_issues"].extend(issue_entries)

    def _add_integration_metadata(
        self,
        checklist_data: A31ChecklistData,
        session_result: SessionAnalysisResult,
    ) -> None:
        """統合メタデータ追加"""
        if not hasattr(checklist_data, "metadata") or checklist_data.metadata is None:
            checklist_data.metadata = {}

        metadata = checklist_data.metadata

        # Claude分析履歴追加
        if "claude_analysis_history" not in metadata:
            metadata["claude_analysis_history"] = []

        analysis_record = {
            "analysis_id": session_result.analysis_id.value,
            "analyzed_at": project_now().to_iso_string(),
            "completion_rate": session_result.get_completion_rate(),
            "success_rate": session_result.get_success_rate(),
            "average_score": session_result.get_average_analysis_score(),
            "total_improvements": session_result.get_total_improvements(),
        }

        metadata["claude_analysis_history"].append(analysis_record)

        # 最新分析情報更新
        metadata["last_claude_analysis"] = analysis_record

    def _save_checklist_data(
        self,
        checklist_data: A31ChecklistData,
        file_path: str,
    ) -> None:
        """チェックリストデータ保存"""

        # YAML形式で保存
        yaml_data: dict[str, Any] = checklist_data.to_yaml_data()

        with Path(file_path).open("w", encoding="utf-8") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def _generate_integration_summary(
        self,
        session_result: SessionAnalysisResult,
        integrated_results: dict[str, ItemAnalysisResult],
    ) -> dict[str, Any]:
        """統合サマリー生成"""
        return {
            "session_info": {
                "analysis_id": session_result.analysis_id.value,
                "project_name": session_result.project_name,
                "episode_number": session_result.episode_number,
                "overall_status": session_result.overall_status.value,
            },
            "integration_stats": {
                "total_analyzed_items": len(session_result.item_results),
                "integrated_items": len(integrated_results),
                "integration_rate": len(integrated_results) / max(1, len(session_result.item_results)),
                "average_confidence": self._calculate_average_confidence(integrated_results),
                "improvement_distribution": self._analyze_improvement_distribution(integrated_results),
            },
            "quality_metrics": {
                "average_analysis_score": session_result.get_average_analysis_score(),
                "high_confidence_improvements": len(session_result.get_high_confidence_improvements()),
                "total_issues_identified": sum(len(result.issues_found) for result in integrated_results.values()),
            },
        }

    def _calculate_average_confidence(
        self,
        results: dict[str, ItemAnalysisResult],
    ) -> float:
        """平均信頼度計算"""
        if not results:
            return 0.0

        confidence_scores = {
            AnalysisConfidence.LOW: 0.25,
            AnalysisConfidence.MEDIUM: 0.5,
            AnalysisConfidence.HIGH: 0.75,
            AnalysisConfidence.VERIFIED: 1.0,
        }

        total_confidence = sum(confidence_scores[result.confidence] for result in results.values())

        return total_confidence / len(results)

    def _analyze_improvement_distribution(
        self,
        results: dict[str, ItemAnalysisResult],
    ) -> dict[str, int]:
        """改善提案分布分析"""
        distribution = {}

        for result in results.values():
            for improvement in result.improvements:
                improvement_type = improvement.improvement_type
                distribution[improvement_type] = distribution.get(improvement_type, 0) + 1

        return distribution

    def _update_integration_stats(self, result: IntegrationResult) -> None:
        """統合統計更新"""
        self._integration_stats["total_integrations"] += 1

        if result.success:
            self._integration_stats["successful_integrations"] += 1
            self._integration_stats["total_items_integrated"] += result.integrated_items_count
            self._integration_stats["total_improvements_added"] += result.improvement_comments_added

    def get_integration_statistics(self) -> dict[str, Any]:
        """統合統計取得"""
        return self._integration_stats.copy()

    def get_integration_history(self) -> list[IntegrationResult]:
        """統合履歴取得"""
        return self._integration_history.copy()

# Backward compatibility alias
A31ResultIntegrator = ChecklistResultIntegrator
