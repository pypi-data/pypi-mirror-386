#!/usr/bin/env python3

"""Domain.services.b20_pre_implementation_check_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""B20実装着手前チェック管理サービス

仕様書: B20開発作業指示書準拠
"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from noveler.domain.interfaces.logger_service import ILoggerService, NullLoggerService
from noveler.domain.value_objects.b20_development_stage import B20DevelopmentStage, DevelopmentStage, StageRequirement

if TYPE_CHECKING:

    from pathlib import Path


@dataclass
class PreImplementationCheckResult:
    """実装着手前チェック結果"""

    is_implementation_allowed: bool
    current_stage: DevelopmentStage
    completed_requirements: list[StageRequirement]
    pending_requirements: list[StageRequirement]
    next_required_actions: list[str]
    completion_percentage: float
    warnings: list[str]
    errors: list[str]
    codemap_status: dict[str, Any]


@dataclass
class ConflictAnalysisResult:
    """競合分析結果"""

    has_import_conflicts: bool
    import_conflict_details: list[str]
    has_ddd_layer_violations: bool
    ddd_violation_details: list[str]
    has_existing_implementation_conflicts: bool
    existing_conflict_details: list[str]
    circular_import_risks: list[str]


class B20PreImplementationCheckService:
    """B20実装着手前チェック管理サービス"""

    def __init__(self, project_root: Path, logger: ILoggerService | None = None) -> None:
        """初期化

        Args:
            project_root: プロジェクトルート
            logger: ロガーインスタンス（依存性注入）
        """
        self.project_root = project_root
        # B20/DDD準拠: Domain層はInfrastructure層に依存しない（依存性注入）
        self.logger = logger or NullLoggerService()

    def execute_pre_implementation_check(
        self, feature_name: str, target_layer: str, implementation_path: Path | None = None
    ) -> PreImplementationCheckResult:
        """実装着手前チェックの実行

        Args:
            feature_name: 実装予定機能名
            target_layer: 対象DDD層（domain/application/infrastructure/presentation）
            implementation_path: 実装予定パス（オプション）
        """
        if self.logger:
            self.logger.info("実装着手前チェック開始: %s", feature_name)

        # 現在の開発段階を取得
        current_stage = self._analyze_current_development_stage(feature_name)

        # 各要件のチェック
        spec_check_result = self._check_specification_requirement(feature_name)
        codemap_check_result = self._check_codemap_requirements()
        conflict_analysis_result = self._analyze_implementation_conflicts(
            feature_name, target_layer, implementation_path
        )

        # 結果統合
        warnings = []
        errors: list[Any] = []

        # 仕様書チェック結果の統合
        if not spec_check_result["exists"]:
            errors.append(f"仕様書が見つかりません: {feature_name}")
        elif spec_check_result["has_warnings"]:
            warnings.extend(spec_check_result["warnings"])

        # CODEMAPチェック結果の統合
        if not codemap_check_result["is_up_to_date"]:
            errors.append("CODEMAPが最新ではありません")

        # 競合分析結果の統合
        if conflict_analysis_result.has_import_conflicts:
            errors.extend([f"インポート競合: {detail}" for detail in conflict_analysis_result.import_conflict_details])

        if conflict_analysis_result.has_ddd_layer_violations:
            errors.extend([f"DDD層違反: {detail}" for detail in conflict_analysis_result.ddd_violation_details])

        if conflict_analysis_result.has_existing_implementation_conflicts:
            warnings.extend(
                [f"既存実装競合: {detail}" for detail in conflict_analysis_result.existing_conflict_details]
            )

        if conflict_analysis_result.circular_import_risks:
            warnings.extend(
                [f"循環インポートリスク: {risk}" for risk in conflict_analysis_result.circular_import_risks]
            )

        # 実装許可判定
        is_implementation_allowed = len(errors) == 0 and current_stage.is_implementation_allowed()

        return PreImplementationCheckResult(
            is_implementation_allowed=is_implementation_allowed,
            current_stage=current_stage.current_stage,
            completed_requirements=list(current_stage.completed_requirements),
            pending_requirements=list(current_stage.pending_requirements),
            next_required_actions=current_stage.get_next_required_actions(),
            completion_percentage=current_stage.get_completion_percentage(),
            warnings=warnings,
            errors=errors,
            codemap_status=codemap_check_result,
        )

    def _analyze_current_development_stage(self, feature_name: str) -> B20DevelopmentStage:
        """現在の開発段階分析"""
        # 仕様書の存在チェック
        spec_exists = self._check_specification_exists(feature_name)

        if not spec_exists:
            return B20DevelopmentStage.create_specification_stage()

        # CODEMAPの状態チェック
        codemap_updated = self._check_codemap_is_updated()
        import_conflicts_checked = self._check_import_conflicts_analyzed()
        ddd_placement_validated = self._check_ddd_placement_validated()
        existing_impl_checked = self._check_existing_implementation_analyzed()

        completed_requirements = {StageRequirement.SPEC_DOCUMENT_EXISTS}

        if codemap_updated:
            completed_requirements.add(StageRequirement.CODEMAP_UPDATED)

        if import_conflicts_checked:
            completed_requirements.add(StageRequirement.IMPORT_CONFLICTS_CHECKED)

        if ddd_placement_validated:
            completed_requirements.add(StageRequirement.DDD_LAYER_PLACEMENT_VALIDATED)

        if existing_impl_checked:
            completed_requirements.add(StageRequirement.EXISTING_IMPLEMENTATION_CHECKED)

        # テスト実装完了チェック
        test_completed = self._check_test_implementation_completed(feature_name)
        if test_completed:
            completed_requirements.add(StageRequirement.TEST_IMPLEMENTATION_COMPLETED)

        # 段階決定
        all_requirements = {
            StageRequirement.SPEC_DOCUMENT_EXISTS,
            StageRequirement.CODEMAP_UPDATED,
            StageRequirement.IMPORT_CONFLICTS_CHECKED,
            StageRequirement.DDD_LAYER_PLACEMENT_VALIDATED,
            StageRequirement.EXISTING_IMPLEMENTATION_CHECKED,
            StageRequirement.TEST_IMPLEMENTATION_COMPLETED,
        }

        pending_requirements = all_requirements - completed_requirements

        # 段階判定ロジック
        if StageRequirement.SPEC_DOCUMENT_EXISTS not in completed_requirements:
            current_stage = DevelopmentStage.SPECIFICATION_REQUIRED
        elif not {
            StageRequirement.CODEMAP_UPDATED,
            StageRequirement.IMPORT_CONFLICTS_CHECKED,
            StageRequirement.DDD_LAYER_PLACEMENT_VALIDATED,
            StageRequirement.EXISTING_IMPLEMENTATION_CHECKED,
        }.issubset(completed_requirements):
            current_stage = DevelopmentStage.CODEMAP_CHECK_REQUIRED
        elif StageRequirement.TEST_IMPLEMENTATION_COMPLETED not in completed_requirements:
            current_stage = DevelopmentStage.IMPLEMENTATION_ALLOWED
        else:
            current_stage = DevelopmentStage.COMMIT_ALLOWED

        return B20DevelopmentStage(
            current_stage=current_stage,
            completed_requirements=frozenset(completed_requirements),
            pending_requirements=frozenset(pending_requirements),
            stage_metadata={"feature_name": feature_name},
        )

    def _check_specification_requirement(self, feature_name: str) -> dict[str, Any]:
        """仕様書要件チェック"""
        specs_dir = self.project_root / "specs"

        normalized_feature = self._normalize_keyword(feature_name)
        if not normalized_feature or not specs_dir.exists():
            return {"exists": False, "has_warnings": False, "warnings": [], "spec_files": []}

        found_specs = [
            spec_file
            for spec_file in specs_dir.glob("*.md")
            if normalized_feature in self._normalize_keyword(spec_file.stem)
        ]

        if not found_specs:
            return {"exists": False, "has_warnings": False, "warnings": [], "spec_files": []}

        # 仕様書内容の基本検証
        warnings = [
            f"仕様書が短すぎます: {spec_file.name}"
            for spec_file in found_specs
            if spec_file.stat().st_size < 100  # 100バイト未満
        ]

        return {
            "exists": True,
            "has_warnings": len(warnings) > 0,
            "warnings": warnings,
            "spec_files": [str(f) for f in found_specs],
        }

    def _check_codemap_requirements(self) -> dict[str, Any]:
        """CODEMAP要件チェック"""
        codemap_file = self.project_root / "CODEMAP.yaml"

        if not codemap_file.exists():
            return {"is_up_to_date": False, "exists": False, "last_updated": None, "needs_update": True}

        # CODEMAP更新状態の簡易チェック
        # 実際の実装では、GitコミットIDとの比較を行う

        return {
            "is_up_to_date": True,  # 実装時により詳細なチェックを追加
            "exists": True,
            "last_updated": codemap_file.stat().st_mtime,
            "needs_update": False,
        }

    def _analyze_implementation_conflicts(
        self, feature_name: str, target_layer: str, implementation_path: Path | None
    ) -> ConflictAnalysisResult:
        """実装競合分析"""
        # インポート競合チェック
        import_conflicts = self._check_import_conflicts(target_layer, implementation_path)

        # DDD層違反チェック
        ddd_violations = self._check_ddd_layer_violations(target_layer, implementation_path)

        # 既存実装競合チェック
        existing_conflicts = self._check_existing_implementation_conflicts(feature_name, target_layer)

        # 循環インポートリスクチェック
        circular_risks = self._check_circular_import_risks(target_layer, implementation_path)

        return ConflictAnalysisResult(
            has_import_conflicts=len(import_conflicts) > 0,
            import_conflict_details=import_conflicts,
            has_ddd_layer_violations=len(ddd_violations) > 0,
            ddd_violation_details=ddd_violations,
            has_existing_implementation_conflicts=len(existing_conflicts) > 0,
            existing_conflict_details=existing_conflicts,
            circular_import_risks=circular_risks,
        )

    def _check_specification_exists(self, feature_name: str) -> bool:
        """仕様書存在チェック"""
        result = self._check_specification_requirement(feature_name)
        return result["exists"]

    def _normalize_keyword(self, text: str) -> str:
        """検索用キーワードを正規化"""
        return re.sub(r"[^a-z0-9]", "", text.lower())

    def _check_codemap_is_updated(self) -> bool:
        """CODEMAP更新状態チェック"""
        result = self._check_codemap_requirements()
        return result["is_up_to_date"]

    def _check_import_conflicts_analyzed(self) -> bool:
        """インポート競合分析済みチェック"""
        # 実装時に実際のチェックロジックを追加
        return True  # 暫定

    def _check_ddd_placement_validated(self) -> bool:
        """DDD層配置検証済みチェック"""
        # 実装時に実際のチェックロジックを追加
        return True  # 暫定

    def _check_existing_implementation_analyzed(self) -> bool:
        """既存実装分析済みチェック"""
        # 実装時に実際のチェックロジックを追加
        return True  # 暫定

    def _check_test_implementation_completed(self, feature_name: str) -> bool:
        """テスト実装完了チェック"""
        # テストファイルの存在確認
        test_patterns = [f"**/test*{feature_name}*.py", f"**/*{feature_name}*test*.py"]

        for pattern in test_patterns:
            test_files = list(self.project_root.glob(pattern))
            if test_files:
                return True

        return False

    def _check_import_conflicts(self, _target_layer: str, _implementation_path: Path | None) -> list[str]:
        """インポート競合チェック"""
        return []

        # 実装時に詳細なチェックロジックを追加
        # - 相対インポート使用チェック
        # - scriptsプレフィックス使用チェック
        # - 層間依存違反チェック


    def _check_ddd_layer_violations(self, target_layer: str, _implementation_path: Path | None) -> list[str]:
        """DDD層違反チェック"""
        violations: list[Any] = []

        # 層間依存チェック
        valid_dependencies = {
            "presentation": ["application"],
            "application": ["domain"],
            "infrastructure": ["domain", "application"],
            "domain": [],
        }

        if target_layer not in valid_dependencies:
            violations.append(f"無効な対象層: {target_layer}")

        return violations

    def _check_existing_implementation_conflicts(self, feature_name: str, target_layer: str) -> list[str]:
        """既存実装競合チェック"""
        layer_path = self.project_root / "scripts" / target_layer
        if not layer_path.exists():
            return []

        return [
            f"類似ファイル存在: {py_file.relative_to(self.project_root)}"
            for py_file in layer_path.rglob("*.py")
            if feature_name.lower() in py_file.name.lower()
        ]

    def _check_circular_import_risks(self, _target_layer: str, _implementation_path: Path | None) -> list[str]:
        """循環インポートリスクチェック"""
        return []

        # 実装時に詳細なリスク分析を追加
        # - 既存モジュール間の依存関係分析
        # - 新規実装による循環リスク予測
