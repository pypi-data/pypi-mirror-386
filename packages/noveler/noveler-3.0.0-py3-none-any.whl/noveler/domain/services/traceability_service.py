#!/usr/bin/env python3

"""Domain.services.traceability_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""トレーサビリティサービス

仕様書とテストの紐付けを管理するドメインサービス
"""


from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict


class SpecInfo(TypedDict, total=False):
    """仕様書情報"""

    id: str
    title: str
    description: str
    requirements: list[str]


class TestInfo(TypedDict, total=False):
    """テスト情報"""

    spec_id: str
    file_path: str
    test_name: str
    markers: list[str]


if TYPE_CHECKING:

    from pathlib import Path

    from noveler.domain.repositories.specification_repository import SpecificationRepository
    from noveler.domain.repositories.test_repository import TestRepository


@dataclass
class TraceabilityReport:
    """トレーサビリティレポート"""

    spec_id: str
    test_files: list[str]
    coverage_percentage: float
    missing_tests: list[str]
    orphaned_tests: list[str]


class TraceabilityService:
    """トレーサビリティサービス

    仕様書とテストの紐付けを分析し、トレーサビリティレポートを生成する
    """

    def __init__(self, spec_repository: SpecificationRepository, test_repository: TestRepository) -> None:
        """初期化

        Args:
            spec_repository: 仕様書リポジトリ
            test_repository: テストリポジトリ
        """
        self.spec_repository = spec_repository
        self.test_repository = test_repository

    def generate_traceability_report(self, project_path: Path) -> list[TraceabilityReport]:
        """トレーサビリティレポートを生成

        Args:
            project_path: プロジェクトパス

        Returns:
            トレーサビリティレポートのリスト
        """
        specs = self.spec_repository.find_all_specs(project_path)
        tests = self.test_repository.find_all_tests(project_path)

        reports = []
        for spec in specs:
            report = self._analyze_spec_coverage(spec, tests)
            reports.append(report)

        return reports

    def _analyze_spec_coverage(self, spec: SpecInfo, tests: list[TestInfo]) -> TraceabilityReport:
        """仕様書のテストカバレッジを分析

        Args:
            spec: 仕様書情報
            tests: テスト情報のリスト

        Returns:
            トレーサビリティレポート
        """
        spec_id = spec["id"]
        related_tests = [test for test in tests if test.get("spec_id") == spec_id]

        test_files = [test["file_path"] for test in related_tests]
        coverage_percentage = self._calculate_coverage(spec, related_tests)
        missing_tests = self._find_missing_tests(spec, related_tests)
        orphaned_tests = self._find_orphaned_tests(tests, spec_id)

        return TraceabilityReport(
            spec_id=spec_id,
            test_files=test_files,
            coverage_percentage=coverage_percentage,
            missing_tests=missing_tests,
            orphaned_tests=orphaned_tests,
        )

    def _calculate_coverage(self, _spec: SpecInfo, tests: list[TestInfo]) -> float:
        """カバレッジを計算

        Args:
            spec: 仕様書情報
            tests: 関連するテスト情報

        Returns:
            カバレッジの割合
        """
        if not tests:
            return 0.0

        # 簡易実装:テストが存在すれば100%とする
        return 100.0 if tests else 0.0

    def _find_missing_tests(self, _spec: SpecInfo, _tests: list[TestInfo]) -> list[str]:
        """不足しているテストを特定

        Args:
            spec: 仕様書情報
            tests: 関連するテスト情報

        Returns:
            不足しているテストの名前リスト
        """
        # 簡易実装:空のリストを返す
        return []

    def _find_orphaned_tests(self, _all_tests: list[TestInfo], _current_spec_id: str) -> list[str]:
        """孤立したテストを特定

        Args:
            all_tests: 全テスト情報
            current_spec_id: 現在の仕様書ID

        Returns:
            孤立したテストのファイルパスリスト
        """
        # 簡易実装:空のリストを返す
        return []
