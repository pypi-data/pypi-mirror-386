"""トレーサビリティレポート生成ユースケース"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.infrastructure.unit_of_work import IUnitOfWork

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.specification.entities import SpecificationId
from noveler.domain.specification.value_objects import TraceabilityReport


class GenerateTraceabilityReportUseCase(AbstractUseCase[dict, TraceabilityReport]):
    """トレーサビリティレポート生成ユースケース"""

    def __init__(self,
        logger_service: "ILoggerService" = None,
        unit_of_work: "IUnitOfWork" = None,
        specification_repository = None,
        test_repository = None,
        traceability_service = None,
        **kwargs) -> None:
        super().__init__(**kwargs, **kwargs)
        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work

        self.specification_repository = (
            specification_repository or self.repository_factory.create_specification_repository()
        )
        self.test_repository = test_repository or self.repository_factory.create_test_repository()
        self.traceability_service = traceability_service

    async def execute(self, request: dict) -> TraceabilityReport:
        """ユースケースを実行"""
        output_path = request.get("output_path")
        return self._execute_internal(output_path)

    def _execute_internal(self, output_path: Path | None) -> TraceabilityReport:
        """トレーサビリティレポートを生成

        Args:
            output_path: レポート出力先パス(Noneの場合はファイル出力しない)

        Returns:
            TraceabilityReport: 生成されたレポート
        """
        # すべての仕様書とテスト仕様を取得
        specifications = self.specification_repository.find_all()
        test_specifications = self.test_repository.find_all()

        # レポート生成
        report = self.traceability_service.generate_traceability_report(
            specifications=specifications, test_specifications=test_specifications
        )

        # ファイル出力が指定されている場合
        if output_path:
            self._save_report(report, output_path)

        return report

    def execute_for_specification(self, spec_id: str, include_impact_analysis: bool) -> dict[str, Any]:
        """特定の仕様書に対するレポートを生成

        Args:
            spec_id: 仕様書ID
            include_impact_analysis: 影響分析を含めるか

        Returns:
            dict: 仕様書のトレーサビリティ情報
        """

        specification_id = SpecificationId(spec_id)
        specification = self.specification_repository.find_by_id(specification_id)

        if not specification:
            msg = f"仕様書 {spec_id} が見つかりません"
            raise ValueError(msg)

        # 基本情報
        result = {
            "specification_id": spec_id,
            "title": specification.title,
            "description": specification.description,
            "test_references": [str(ref) for ref in specification.test_references],
            "implementation_references": specification.implementation_references,
            "coverage_status": specification.get_test_coverage_status(),
        }

        # 影響分析を含める場合
        if include_impact_analysis:
            all_specifications = self.specification_repository.find_all()
            all_tests = self.test_repository.find_all()

            impact_analysis = self.traceability_service.analyze_specification_impact(
                spec_id=specification_id, all_specifications=all_specifications, all_tests=all_tests
            )

            result["impact_analysis"] = {
                "affected_tests": impact_analysis.affected_tests,
                "affected_implementations": impact_analysis.affected_implementations,
                "related_specifications": impact_analysis.related_specifications,
                "total_impact_count": impact_analysis.total_impact_count,
            }

        return result

    def check_coverage_threshold(self, min_coverage: float) -> tuple[bool, float]:
        """カバレッジ率が閾値を満たしているか確認

        Args:
            min_coverage: 最小カバレッジ率(%)

        Returns:
            tuple[bool, float]: (閾値を満たしているか, 現在のカバレッジ率)
        """
        specifications = self.specification_repository.find_all()
        coverage = self.traceability_service.calculate_coverage(specifications)

        is_sufficient = coverage.coverage_percentage >= min_coverage

        return is_sufficient, coverage.coverage_percentage

    def find_orphaned_tests(self) -> list[str]:
        """仕様に紐付いていないテストを検出

        Returns:
            list[str]: 孤立したテストのリスト
        """
        orphaned_tests = self.test_repository.find_orphaned_tests()
        return [str(test.get_test_reference()) for test in orphaned_tests]

    def _save_report(self, report: TraceabilityReport, output_path: Path) -> None:
        """レポートをファイルに保存"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # バッチ書き込みを使用
        Path(output_path).write_text(report.to_markdown(), encoding="utf-8")
