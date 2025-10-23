"""Domain.specification.services
Where: Domain services managing specification operations.
What: Handle retrieval, validation, and updates for specifications.
Why: Provide reusable logic for specification workflows.
"""

from __future__ import annotations

"""仕様書管理ドメインサービス"""


from typing import TYPE_CHECKING

from noveler.domain.specification.value_objects import (
    ImpactAnalysisResult,
    SpecificationCoverage,
    TraceabilityLink,
    TraceabilityReport,
)
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

if TYPE_CHECKING:
    from noveler.domain.specification.entities import Specification, SpecificationTest

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class SpecificationTraceabilityService:
    """仕様書トレーサビリティサービス"""

    def calculate_coverage(self, specifications: list[Specification]) -> SpecificationCoverage:
        """仕様カバレッジを計算"""
        total = len(specifications)
        covered = 0
        uncovered = 0
        partially_covered = 0

        for spec in specifications:
            coverage_status = spec.get_test_coverage_status()
            if coverage_status == "実装済み":
                covered += 1
            elif coverage_status == "部分実装":
                partially_covered += 1
            else:
                uncovered += 1

        return SpecificationCoverage(
            total_specifications=total,
            covered_specifications=covered,
            uncovered_specifications=uncovered,
            partially_covered_specifications=partially_covered,
        )

    def create_traceability_link(self, specification: Specification) -> TraceabilityLink:
        """仕様のトレーサビリティリンクを作成"""
        test_refs = [str(ref) for ref in specification.test_references]
        req_ids = [req.value for req in specification.requirement_ids]

        return TraceabilityLink(
            specification_id=specification.id.value,
            test_references=test_refs,
            requirement_ids=req_ids,
            implementation_references=specification.implementation_references,
        )

    def analyze_specification_impact(
        self, spec_id: str, all_specifications: list[Specification]
    ) -> ImpactAnalysisResult:
        """仕様変更の影響を分析"""
        target_spec = None
        for spec in all_specifications:
            if spec.id == spec_id:
                target_spec = spec
                break

        if not target_spec:
            return ImpactAnalysisResult(
                specification_id=spec_id.value,
                affected_tests=[],
                affected_implementations=[],
                related_specifications=[],
                analysis_timestamp=project_now().datetime,
            )

        # 影響を受けるテストを収集
        affected_tests = [str(ref) for ref in target_spec.test_references]

        # 関連する仕様を収集(同じ要件IDを持つ仕様)
        related_specs = []
        for spec in all_specifications:
            if spec.id != spec_id:
                # 共通の要件IDがあるか確認
                common_reqs = set(target_spec.requirement_ids) & set(spec.requirement_ids)
                if common_reqs:
                    related_specs.append(spec.id.value)

        return ImpactAnalysisResult(
            specification_id=spec_id.value,
            affected_tests=affected_tests,
            affected_implementations=target_spec.implementation_references,
            related_specifications=related_specs,
            analysis_timestamp=project_now().datetime,
        )

    def generate_traceability_report(
        self, specifications: list[Specification], test_specifications: list[SpecificationTest]
    ) -> TraceabilityReport:
        """トレーサビリティレポートを生成"""
        coverage = self.calculate_coverage(specifications)

        # カバー済み仕様のリンクを作成
        covered_specs = {}
        uncovered_specs = []

        for spec in specifications:
            if spec.has_tests():
                link = self.create_traceability_link(spec)
                covered_specs[spec.id.value] = link
            else:
                uncovered_specs.append(spec.id.value)

        # 仕様に紐付いていないテストを検出
        all_linked_test_refs = set()
        for spec in specifications:
            for test_ref in spec.test_references:
                all_linked_test_refs.add(str(test_ref))

        orphaned_tests = []
        for test_spec in test_specifications:
            test_ref_str = str(test_spec.get_test_reference())
            if test_ref_str not in all_linked_test_refs:
                orphaned_tests.append(test_ref_str)

        return TraceabilityReport(
            report_date=project_now().datetime,
            coverage=coverage,
            covered_specifications=covered_specs,
            uncovered_specifications=uncovered_specs,
            orphaned_tests=orphaned_tests,
        )


class SpecificationSyncService:
    """仕様書とテストの同期サービス"""

    def sync_test_to_specifications(
        self, test_spec: SpecificationTest, specifications: dict[str, Specification]
    ) -> list[Specification]:
        """テストから仕様への同期"""
        updated_specs = []
        test_ref = test_spec.get_test_reference()

        for spec_id in test_spec.specification_ids:
            if spec_id.value in specifications:
                spec = specifications[spec_id.value]
                spec.add_test_reference(test_ref)
                updated_specs.append(spec)

        return updated_specs

    def sync_specification_to_tests(
        self, specification: Specification, test_specifications: dict[str, SpecificationTest]
    ) -> list[SpecificationTest]:
        """仕様からテストへの同期"""
        updated_tests = []

        for test_ref in specification.test_references:
            key = f"{test_ref.file_path}::{test_ref.function_name}"
            if key in test_specifications:
                test_spec = test_specifications[key]
                test_spec.add_specification(specification.id)
                updated_tests.append(test_spec)

        return updated_tests

    def detect_sync_issues(
        self, specifications: list[Specification], test_specifications: list[SpecificationTest]
    ) -> dict[str, list[str]]:
        """同期の問題を検出"""
        issues = {
            "missing_test_references": [],
            "missing_specification_references": [],
            "orphaned_specifications": [],
            "orphaned_tests": [],
        }

        # 仕様に記載されているがテストに存在しない参照
        all_test_refs = {str(ts.get_test_reference()) for ts in test_specifications}
        for spec in specifications:
            for test_ref in spec.test_references:
                if str(test_ref) not in all_test_refs:
                    issues["missing_test_references"].append(f"{spec.id.value} -> {test_ref}")

        # テストに記載されているが仕様に存在しない参照
        spec_dict = {s.id.value: s for s in specifications}
        for test_spec in test_specifications:
            for spec_id in test_spec.specification_ids:
                if spec_id.value not in spec_dict:
                    issues["missing_specification_references"].append(
                        f"{test_spec.get_test_reference()} -> {spec_id.value}"
                    )

        return issues
