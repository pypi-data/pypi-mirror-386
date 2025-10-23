"""Domain.services.structure_compliance_analyzer
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""
SPEC-WORKFLOW-001: 構造準拠性分析器

プロジェクト構造の準拠性を分析するドメインサービス。
DDD設計に基づく構造分析ビジネスロジックの実装。
"""


from collections import defaultdict
from datetime import timedelta

from noveler.domain.services.project_structure_value_objects import (
    ErrorSeverity,
    ProjectStructure,
    RepairCommand,
    RepairSuggestion,
    RiskLevel,
    ValidationError,
    ValidationErrorType,
)


class StructureComplianceAnalyzer:
    """構造準拠性分析器ドメインサービス"""

    def analyze_compliance_level(self, project_structure: ProjectStructure, standard_structure: dict) -> float:
        """準拠レベルを分析

        Args:
            project_structure: プロジェクト構造
            standard_structure: 標準構造

        Returns:
            準拠レベル(0.0-1.0)
        """
        # ディレクトリ準拠率
        dir_score = project_structure.directory_structure.get_compliance_rate()

        # ファイル準拠率
        file_score = project_structure.file_inventory.get_compliance_rate()

        # 設定ファイル準拠率
        config_score = self._calculate_configuration_compliance(project_structure, standard_structure)

        # 命名規則準拠率
        naming_score = self._calculate_naming_compliance(project_structure, standard_structure)

        # 重み付き平均(ディレクトリとファイルを重視)
        weighted_score = dir_score * 0.3 + file_score * 0.3 + config_score * 0.25 + naming_score * 0.15

        return min(1.0, max(0.0, weighted_score))

    def identify_critical_issues(self, validation_errors: list[ValidationError]) -> list[ValidationError]:
        """重要問題を特定

        Args:
            validation_errors: 検証エラーのリスト

        Returns:
            重要度の高いエラーのリスト
        """
        # 重要度でフィルタリングとソート
        critical_errors = [
            error for error in validation_errors if error.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]
        ]

        # 重要度順にソート
        severity_order = {
            ErrorSeverity.CRITICAL: 0,
            ErrorSeverity.HIGH: 1,
            ErrorSeverity.MEDIUM: 2,
            ErrorSeverity.LOW: 3,
            ErrorSeverity.INFO: 4,
        }

        critical_errors.sort(key=lambda e: severity_order.get(e.severity, 5))

        return critical_errors

    def suggest_priority_fixes(self, validation_errors: list[ValidationError]) -> list[RepairSuggestion]:
        """優先修復提案を生成

        Args:
            validation_errors: 検証エラーのリスト

        Returns:
            優先度順の修復提案リスト
        """
        suggestions = []

        # エラータイプ別にグループ化
        error_groups = defaultdict(list)
        for error in validation_errors:
            error_groups[error.error_type].append(error)

        suggestion_id = 1

        # エラータイプ別に修復提案を生成
        for error_type, errors in error_groups.items():
            suggestion = self._create_repair_suggestion_for_error_type(error_type, errors, suggestion_id)
            if suggestion:
                suggestions.append(suggestion)
                suggestion_id += 1

        # 優先度スコア順にソート
        suggestions.sort(key=lambda s: s.priority_score, reverse=True)

        return suggestions

    def calculate_impact_analysis(self, project_structure: ProjectStructure) -> dict[str, float]:
        """影響分析を計算

        Args:
            project_structure: プロジェクト構造

        Returns:
            影響分析結果の辞書
        """
        analysis = {
            "structural_integrity": 0.0,
            "workflow_efficiency": 0.0,
            "maintainability": 0.0,
            "collaboration_readiness": 0.0,
        }

        # 構造的整合性(必須ディレクトリ・ファイルの存在率)
        dir_compliance = project_structure.directory_structure.get_compliance_rate()
        file_compliance = project_structure.file_inventory.get_compliance_rate()
        analysis["structural_integrity"] = (dir_compliance + file_compliance) / 2

        # ワークフロー効率性(設定ファイルの有効性)
        valid_configs = len([cf for cf in project_structure.configuration_files if cf.is_valid])
        total_configs = len(project_structure.configuration_files)
        if total_configs > 0:
            analysis["workflow_efficiency"] = valid_configs / total_configs
        else:
            analysis["workflow_efficiency"] = 0.5  # 設定ファイルがない場合の中間値

        # 保守性(無効ファイル・ディレクトリの少なさ)
        invalid_items = len(project_structure.directory_structure.invalid_dirs) + len(
            project_structure.file_inventory.invalid_files
        )

        total_items = len(project_structure.directory_structure.existing_dirs) + len(
            project_structure.file_inventory.existing_files
        )

        if total_items > 0:
            analysis["maintainability"] = max(0.0, 1.0 - (invalid_items / total_items))
        else:
            analysis["maintainability"] = 1.0

        # コラボレーション準備状況(総合評価)
        analysis["collaboration_readiness"] = (
            analysis["structural_integrity"] * 0.4
            + analysis["workflow_efficiency"] * 0.4
            + analysis["maintainability"] * 0.2
        )

        return analysis

    def generate_compliance_recommendations(
        self, project_structure: ProjectStructure, _target_compliance: float
    ) -> list[str]:
        """準拠改善推奨事項を生成

        Args:
            project_structure: プロジェクト構造
            target_compliance: 目標準拠レベル

        Returns:
            推奨事項のリスト
        """
        recommendations = []

        # ディレクトリ構造の改善
        missing_dirs = project_structure.directory_structure.get_missing_directories()
        if missing_dirs:
            recommendations.append(f"必須ディレクトリを作成してください: {', '.join(missing_dirs)}")

        # ファイル構造の改善
        missing_files = project_structure.file_inventory.get_missing_files()
        if missing_files:
            recommendations.append(f"必須ファイルを作成してください: {', '.join(missing_files)}")

        # 無効項目の整理
        invalid_dirs = project_structure.directory_structure.invalid_dirs
        if invalid_dirs:
            recommendations.append(f"不要なディレクトリを整理してください: {', '.join(invalid_dirs)}")

        invalid_files = project_structure.file_inventory.invalid_files
        if invalid_files:
            recommendations.append(
                f"不要なファイルを整理してください: {', '.join(invalid_files[:3])}"
                + (f" 他{len(invalid_files) - 3}個" if len(invalid_files) > 3 else "")
            )

        # 設定ファイルの修正
        invalid_configs = [cf for cf in project_structure.configuration_files if not cf.is_valid]
        if invalid_configs:
            config_paths = [str(cf.path) for cf in invalid_configs[:3]]
            recommendations.append(
                f"設定ファイルのエラーを修正してください: {', '.join(config_paths)}"
                + (f" 他{len(invalid_configs) - 3}個" if len(invalid_configs) > 3 else "")
            )

        # 優先度の高い推奨事項を先頭に
        if not recommendations:
            recommendations.append("プロジェクト構造は良好です。継続的な保守を心がけてください。")

        return recommendations

    def _calculate_configuration_compliance(
        self, project_structure: ProjectStructure, _standard_structure: dict
    ) -> float:
        """設定ファイル準拠率を計算"""
        if not project_structure.configuration_files:
            return 0.5  # 設定ファイルがない場合の中間値

        valid_count = 0
        total_count = len(project_structure.configuration_files)

        for config_file in project_structure.configuration_files:
            if config_file.is_valid and len(config_file.schema_errors) == 0:
                valid_count += 1

        return valid_count / total_count if total_count > 0 else 0.0

    def _calculate_naming_compliance(self, project_structure: ProjectStructure, _standard_structure: dict) -> float:
        """命名規則準拠率を計算"""
        # 簡易実装:ファイル名の基本的なチェック
        total_files = len(project_structure.file_inventory.existing_files)
        if total_files == 0:
            return 1.0

        compliant_files = 0

        for filename in project_structure.file_inventory.existing_files:
            # 基本的な命名規則チェック
            if self._is_valid_filename(filename):
                compliant_files += 1

        return compliant_files / total_files

    def _is_valid_filename(self, filename: str) -> bool:
        """ファイル名の基本的な妥当性をチェック"""
        # 基本的なルール
        if not filename or filename.startswith("."):
            return False

        # 無効文字のチェック
        invalid_chars = ["<", ">", ":", '"', "|", "?", "*"]
        if any(char in filename for char in invalid_chars):
            return False

        # 日本語ファイル名対応
        if filename.endswith((".yaml", ".md")):
            return True

        return True

    def _create_repair_suggestion_for_error_type(
        self, error_type: ValidationErrorType, errors: list[ValidationError], suggestion_id: int
    ) -> RepairSuggestion:
        """エラータイプ別の修復提案を作成"""

        if error_type == ValidationErrorType.MISSING_DIRECTORY:
            return RepairSuggestion(
                suggestion_id=f"repair_{suggestion_id:03d}",
                description="欠損ディレクトリの作成",
                affected_items=[error.affected_path for error in errors],
                repair_commands=[
                    RepairCommand(
                        command_type="mkdir",
                        command=f"mkdir -p {error.affected_path}",
                        target_path=error.affected_path,
                        backup_required=False,
                    )
                    for error in errors
                ],
                risk_level=RiskLevel.LOW,
                estimated_time=timedelta(seconds=5 * len(errors)),
            )

        if error_type == ValidationErrorType.MISSING_REQUIRED_FILE:
            return RepairSuggestion(
                suggestion_id=f"repair_{suggestion_id:03d}",
                description="必須ファイルのテンプレート作成",
                affected_items=[error.affected_path for error in errors],
                repair_commands=[
                    RepairCommand(
                        command_type="create_template",
                        command=f"create_template {error.affected_path}",
                        target_path=error.affected_path,
                        backup_required=False,
                    )
                    for error in errors
                ],
                risk_level=RiskLevel.MEDIUM,
                estimated_time=timedelta(minutes=2 * len(errors)),
            )

        # その他のエラータイプに対する基本的な提案
        return RepairSuggestion(
            suggestion_id=f"repair_{suggestion_id:03d}",
            description=f"{error_type.value}の修正",
            affected_items=[error.affected_path for error in errors],
            repair_commands=[],
            risk_level=RiskLevel.MEDIUM,
            estimated_time=timedelta(minutes=5),
        )
