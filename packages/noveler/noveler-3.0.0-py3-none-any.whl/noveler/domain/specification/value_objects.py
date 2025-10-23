"""Domain.specification.value_objects
Where: Domain value objects modelling specification data.
What: Define typed structures for specification identifiers and versions.
Why: Ensure specification data stays consistent across services.
"""

from __future__ import annotations

"""仕様書管理ドメイン値オブジェクト"""


from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True)
class SpecificationCoverage:
    """仕様カバレッジ値オブジェクト"""

    total_specifications: int
    covered_specifications: int
    uncovered_specifications: int
    partially_covered_specifications: int

    @property
    def coverage_percentage(self) -> float:
        """カバレッジ率を計算"""
        if self.total_specifications == 0:
            return 0.0
        return (self.covered_specifications / self.total_specifications) * 100

    @property
    def is_sufficient(self) -> bool:
        """十分なカバレッジか判定(80%以上)"""
        return self.coverage_percentage >= 80.0


@dataclass(frozen=True)
class TraceabilityLink:
    """トレーサビリティリンク値オブジェクト"""

    specification_id: str
    test_references: list[str]
    requirement_ids: list[str]
    implementation_references: list[str]

    @property
    def is_fully_traced(self) -> bool:
        """完全にトレースされているか確認"""
        return len(self.test_references) > 0 and len(self.implementation_references) > 0


@dataclass(frozen=True)
class ImpactAnalysisResult:
    """影響分析結果値オブジェクト"""

    specification_id: str
    affected_tests: list[str]
    affected_implementations: list[str]
    related_specifications: list[str]
    analysis_timestamp: datetime

    @property
    def total_impact_count(self) -> int:
        """総影響数を計算"""
        return len(self.affected_tests) + len(self.affected_implementations) + len(self.related_specifications)

    @property
    def has_impact(self) -> bool:
        """影響があるか確認"""
        return self.total_impact_count > 0


@dataclass(frozen=True)
class TestMarker:
    """テストマーカー値オブジェクト"""

    marker_type: str  # "spec" or "requirement"
    marker_value: str

    def __post_init__(self) -> None:
        if self.marker_type not in ["spec", "requirement"]:
            msg = "マーカータイプは'spec'または'requirement'である必要があります"
            raise ValueError(msg)

        if self.marker_type == "spec" and not self.marker_value.startswith("SPEC-"):
            msg = "仕様マーカーはSPEC-で始まる必要があります"
            raise ValueError(msg)

        if self.marker_type == "requirement" and not self.marker_value.startswith("REQ-"):
            msg = "要件マーカーはREQ-で始まる必要があります"
            raise ValueError(msg)


@dataclass(frozen=True)
class TraceabilityReport:
    """トレーサビリティレポート値オブジェクト"""

    report_date: datetime
    coverage: SpecificationCoverage
    covered_specifications: dict[str, TraceabilityLink]
    uncovered_specifications: list[str]
    orphaned_tests: list[str]  # 仕様に紐付いていないテスト

    def to_markdown(self) -> str:
        """Markdown形式でレポートを生成"""
        lines = [
            "# 仕様カバレッジレポート",
            "",
            f"生成日時: {self.report_date.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## カバレッジサマリー",
            f"- 総仕様数: {self.coverage.total_specifications}",
            f"- カバー済み: {self.coverage.covered_specifications} ({self.coverage.coverage_percentage:.1f}%)",
            f"- 未カバー: {self.coverage.uncovered_specifications}",
            f"- 部分カバー: {self.coverage.partially_covered_specifications}",
            "",
            "## カバー済み仕様",
        ]

        for spec_id, link in sorted(self.covered_specifications.items()):
            lines.append("")
            lines.append(f"### {spec_id}")
            if link.test_references:
                lines.append("#### テスト")
                lines.extend(f"- ✅ {test_ref}" for test_ref in link.test_references)
            if link.implementation_references:
                lines.append("#### 実装")
                lines.extend(f"- {impl_ref}" for impl_ref in link.implementation_references)

        if self.uncovered_specifications:
            lines.extend(
                [
                    "",
                    "## 未カバー仕様",
                ]
            )

            lines.extend(f"- ❌ {spec_id}" for spec_id in sorted(self.uncovered_specifications))

        if self.orphaned_tests:
            lines.extend(
                [
                    "",
                    "## 仕様未紐付けテスト",
                ]
            )

            lines.extend(f"- ⚠️ {test}" for test in sorted(self.orphaned_tests))

        return "\n".join(lines)
