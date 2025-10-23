"""Domain.services.project_structure_validation_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""
SPEC-WORKFLOW-001: プロジェクト構造検証サービス

プロジェクト構造の包括的検証を行うドメインサービス。
DDD設計に基づくビジネスロジックの実装。
"""

from typing import TYPE_CHECKING, Any

from noveler.domain.repositories.project_structure_repository import (
    ProjectType,
    ValidationReport,
)
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

if TYPE_CHECKING:

    from pathlib import Path

    from noveler.domain.services.project_structure_value_objects import (
        RepairSuggestion,
        ValidationResult,
    )


# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class ProjectStructureValidationService:
    """プロジェクト構造検証ドメインサービス"""

    def __init__(self, repository: object, analyzer: object, repair_engine: object) -> None:
        """初期化

        Args:
            repository: プロジェクト構造リポジトリ
            analyzer: 構造準拠性分析器
            repair_engine: 自動修復エンジン
        """
        self._repository = repository
        self._analyzer = analyzer
        self._repair_engine = repair_engine

    def validate_project_structure(self, project_path: Path) -> ValidationResult:
        """プロジェクト構造を検証

        Args:
            project_path: プロジェクトパス

        Returns:
            検証結果

        Raises:
            FileNotFoundError: プロジェクトが存在しない場合
            ValueError: 無効なプロジェクト構造の場合
        """
        if not project_path.exists():
            msg = f"プロジェクトが存在しません: {project_path}"
            raise FileNotFoundError(msg)

        try:
            # プロジェクト構造を読み込み
            project_structure = self._repository.load_project_structure(project_path)

            # 標準構造を取得(デフォルトは小説プロジェクト)
            project_type = self._detect_project_type(project_path)
            standard_structure = self._repository.get_standard_structure(project_type)

            # 構造検証を実行
            validation_result = project_structure.validate_against_standard(standard_structure)

            # 検証レポートを保存
            report = ValidationReport(
                project_path=project_path, validation_result=validation_result, generated_at=project_now().datetime
            )

            self._repository.save_validation_report(report)

            return validation_result

        except Exception as e:
            msg = f"プロジェクト構造の検証に失敗しました: {e}"
            raise ValueError(msg) from e

    def generate_repair_plan(self, validation_result: ValidationResult) -> list[RepairSuggestion]:
        """修復計画を生成

        Args:
            validation_result: 検証結果

        Returns:
            修復提案のリスト
        """
        # 分析器を使用して優先修復提案を生成
        priority_repairs = self._analyzer.suggest_priority_fixes(validation_result.validation_errors)

        # 既存の修復提案と統合
        all_suggestions = validation_result.repair_suggestions + priority_repairs

        # 重複除去と優先度ソート
        unique_suggestions = self._deduplicate_suggestions(all_suggestions)
        unique_suggestions.sort(key=lambda s: s.priority, reverse=True)

        return unique_suggestions

    def execute_safe_repairs(
        self, project_path: Path, repair_suggestions: list[RepairSuggestion], auto_confirm: bool = False
    ) -> dict[str, Any]:
        """安全な自動修復を実行

        Args:
            project_path: プロジェクトパス
            repair_suggestions: 修復提案のリスト
            auto_confirm: 高リスク修復の自動確認

        Returns:
            修復実行結果の辞書
        """
        execution_summary = {
            "total_suggestions": len(repair_suggestions),
            "executed_suggestions": 0,
            "skipped_suggestions": 0,
            "backup_created": False,
            "execution_results": [],
            "overall_success": False,
        }

        if not repair_suggestions:
            execution_summary["overall_success"] = True
            return execution_summary

        try:
            # バックアップ作成
            if self._repair_engine.backup_enabled:
                backup_info = self._repair_engine.create_safety_backup(project_path)
                execution_summary["backup_created"] = True
                execution_summary["backup_path"] = str(backup_info.backup_path)

            # 修復提案を実行
            for suggestion in repair_suggestions:
                # 高リスク修復の確認
                if suggestion.requires_user_confirmation() and not auto_confirm:
                    execution_summary["skipped_suggestions"] += 1
                    execution_summary["execution_results"].append({"suggestion_id": suggestion.id, "status": "skipped"})
                    continue

                # 修復コマンドを実行
                result = self._repair_engine.execute_repair_commands(suggestion.repair_commands, project_path)

                execution_summary["executed_suggestions"] += 1
                execution_summary["execution_results"].append({"suggestion_id": suggestion.id, "status": result.status})

            # 全体的な成功判定
            successful_executions = len([r for r in execution_summary["execution_results"] if r["status"] == "success"])
            execution_summary["overall_success"] = successful_executions == execution_summary["executed_suggestions"]

        except Exception as e:
            execution_summary["error"] = str(e)
            execution_summary["overall_success"] = False

        return execution_summary

    def create_validation_report(self, project_path: Path, validation_result: ValidationResult) -> str:
        """検証レポートを作成

        Args:
            project_path: プロジェクトパス
            validation_result: 検証結果

        Returns:
            Markdown形式のレポート文字列
        """
        report_lines = [
            "# プロジェクト構造検証レポート",
            "",
            f"**プロジェクト**: {project_path.name}",
            f"**パス**: {project_path}",
            f"**検証日時**: {project_now().datetime.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**総合判定**: {'✅ 合格' if validation_result.is_valid else '❌ 不合格'}",
            "",
            "## 準拠スコア",
            "",
            f"- **総合スコア**: {validation_result.compliance_score.overall_score:.1%} ({validation_result.compliance_score.get_grade()})",
            f"- **ディレクトリ準拠**: {validation_result.compliance_score.directory_compliance:.1%}",
            f"- **ファイル準拠**: {validation_result.compliance_score.file_compliance:.1%}",
            f"- **設定準拠**: {validation_result.compliance_score.configuration_compliance:.1%}",
            "",
        ]

        # エラー情報
        if validation_result.validation_errors:
            report_lines.extend([f"## 検出された問題 ({len(validation_result.validation_errors)}件)", ""])
            for i, error in enumerate(validation_result.validation_errors, 1):
                severity_emoji = {"critical": "🚨", "high": "⚠️", "medium": "⚡", "low": "ℹ️", "info": "💡"}

                report_lines.extend(
                    [
                        f"### {i}. {severity_emoji.get(error.severity.value, '•')} {error.description}",
                        "",
                        f"- **重要度**: {error.severity.value.upper()}",
                        f"- **対象**: `{error.affected_path}`",
                        f"- **修復アクション**: {error.repair_action.value if error.repair_action else 'なし'}",
                        "",
                    ]
                )

        # 修復提案
        if validation_result.repair_suggestions:
            high_priority = validation_result.get_high_priority_repairs()
            report_lines.extend(["## 修復提案 (優先度順)", ""])
            for i, suggestion in enumerate(high_priority, 1):
                risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}

                report_lines.extend(
                    [
                        f"### {i}. {suggestion.description}",
                        "",
                        f"- **リスクレベル**: {risk_emoji.get(suggestion.risk_level.value, '⚪')} {suggestion.risk_level.value.upper()}",
                        f"- **推定時間**: {suggestion.estimated_time}",
                        f"- **影響項目**: {len(suggestion.affected_items)}個",
                        f"- **修復コマンド数**: {len(suggestion.repair_commands)}個",
                        "",
                    ]
                )

        # 推奨事項
        if validation_result.is_valid:
            report_lines.extend(
                ["## ✅ プロジェクト構造は良好です", "", "継続的な品質保持のため、定期的な検証を推奨します。", ""]
            )
        else:
            critical_errors = validation_result.get_critical_errors()
            if critical_errors:
                report_lines.extend(["## 🚨 緊急対応が必要", "", "以下の重要な問題を優先的に修正してください:", ""])
                report_lines.extend(
                    [
                        f"- {error.description}"
                        for error in critical_errors[:3]  # 上位3つ
                    ]
                )

                report_lines.append("")

        return "\n".join(report_lines)

    def get_compliance_analysis(self, project_path: Path) -> dict[str, Any]:
        """準拠性分析を取得

        Args:
            project_path: プロジェクトパス

        Returns:
            分析結果の辞書
        """
        try:
            project_structure = self._repository.load_project_structure(project_path)

            # 準拠レベル分析
            project_type = self._detect_project_type(project_path)
            standard_structure = self._repository.get_standard_structure(project_type)
            compliance_level = self._analyzer.analyze_compliance_level(project_structure, standard_structure)

            # 影響分析
            impact_analysis = self._analyzer.calculate_impact_analysis(project_structure)

            # 推奨事項
            recommendations = self._analyzer.generate_compliance_recommendations(project_structure)

            return {
                "compliance_level": compliance_level,
                "impact_analysis": impact_analysis,
                "recommendations": recommendations,
                "project_health": self._calculate_project_health(compliance_level, impact_analysis),
            }

        except Exception as e:
            return {
                "error": str(e),
                "compliance_level": 0.0,
                "impact_analysis": {},
                "recommendations": ["プロジェクト分析に失敗しました"],
            }

    def _detect_project_type(self, project_path: Path) -> ProjectType:
        """プロジェクトタイプを検出"""
        # B30準拠: CommonPathService経由でパス取得
        # DDD違反修正: Domain層からPresentation層への直接依存を除去
        # パス検出は抽象化されたサービス経由で実装

        # 暫定的に直接Path操作で代替（アーキテクチャ違反修正のため）
        manuscript_dir = project_path / "manuscripts"

        if manuscript_dir.exists():
            return ProjectType("novel")
        return ProjectType("novel")  # デフォルト

    def _deduplicate_suggestions(self, suggestions: list[RepairSuggestion]) -> list[RepairSuggestion]:
        """修復提案の重複を除去"""
        seen_ids = set()
        unique_suggestions = []

        for suggestion in suggestions:
            if suggestion.suggestion_id not in seen_ids:
                seen_ids.add(suggestion.suggestion_id)
                unique_suggestions.append(suggestion)

        return unique_suggestions

    def _calculate_project_health(self, compliance_level: float, impact_analysis: dict[str, Any]) -> str:
        """プロジェクト健全性を計算"""
        health_score = (
            compliance_level * 0.4
            + impact_analysis.get("structural_integrity", 0.0) * 0.3
            + impact_analysis.get("workflow_efficiency", 0.0) * 0.2
            + impact_analysis.get("maintainability", 0.0) * 0.1
        )

        if health_score >= 0.9:
            return "excellent"
        if health_score >= 0.8:
            return "good"
        if health_score >= 0.7:
            return "fair"
        if health_score >= 0.6:
            return "poor"
        return "critical"
