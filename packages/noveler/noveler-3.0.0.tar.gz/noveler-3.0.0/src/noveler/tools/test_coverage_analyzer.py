"""Tools.test_coverage_analyzer
Where: Tool analysing test coverage reports.
What: Parses coverage data and highlights gaps.
Why: Helps teams improve testing completeness.
"""

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from noveler.presentation.shared.shared_utilities import console

try:
    from noveler.infrastructure.logging.unified_logger import get_logger
except ImportError:  # pragma: no cover - fallback for minimal environments
    from noveler.domain.interfaces.logger_interface import NullLogger

    def get_logger(_: str) -> NullLogger:
        """Return a no-op logger when the unified logger is unavailable."""
        return NullLogger()


logger = get_logger(__name__)


@dataclass
class CoverageAnalysisResult:
    """カバレッジ分析結果"""

    total_implementation_files: int
    total_test_files: int
    coverage_ratio: float
    untested_critical_files: list[str]
    untested_regular_files: list[str]
    missing_test_directories: list[str]
    spec_compliant_tests: int
    total_tests: int
    spec_compliance_ratio: float
    recommendations: list[str]


class TestCoverageAnalyzer:
    """テストカバレッジ分析器

    責務:
    - 実装ファイルとテストファイルの対応関係分析
    - 未テストファイルの特定と重要度評価
    - テスト品質分析（SPEC準拠性等）
    - 改善提案の自動生成
    """

    def __init__(self, project_root: Path | None = None) -> None:
        """初期化

        Args:
            project_root: プロジェクトルート（未指定時は自動検出）
        """
        self.project_root = project_root or Path.cwd()
        self.scripts_dir = self.project_root / "scripts"
        self.tests_dir = self.project_root / "tests"
        self.critical_patterns = [
            "noveler/application/checkers/",
            "noveler/application/services/",
            "noveler/application/orchestrators/",
            "noveler/application/use_cases/",
            "noveler/domain/entities/",
            "noveler/domain/services/",
        ]

    def analyze_coverage(self) -> CoverageAnalysisResult:
        """カバレッジ分析実行

        Returns:
            CoverageAnalysisResult: 分析結果
        """
        logger.info("テストカバレッジ分析開始")
        implementation_files = self._get_implementation_files()
        test_files = self._get_test_files()
        untested_files = self._identify_untested_files(implementation_files, test_files)
        (untested_critical, untested_regular) = self._categorize_untested_files(untested_files)
        missing_test_dirs = self._analyze_missing_test_directories(implementation_files)
        (spec_compliant_tests, total_tests) = self._analyze_spec_compliance()
        recommendations = self._generate_recommendations(untested_critical, untested_regular, missing_test_dirs)
        result = CoverageAnalysisResult(
            total_implementation_files=len(implementation_files),
            total_test_files=len(test_files),
            coverage_ratio=self._calculate_coverage_ratio(implementation_files, test_files),
            untested_critical_files=untested_critical,
            untested_regular_files=untested_regular,
            missing_test_directories=missing_test_dirs,
            spec_compliant_tests=spec_compliant_tests,
            total_tests=total_tests,
            spec_compliance_ratio=self._calculate_spec_ratio(spec_compliant_tests, total_tests),
            recommendations=recommendations,
        )
        logger.info(f"カバレッジ分析完了: {result.coverage_ratio:.1f}%")
        return result

    def _get_implementation_files(self) -> list[Path]:
        """実装ファイル一覧取得"""
        implementation_files = []
        for py_file in self.scripts_dir.rglob("*.py"):
            if py_file.name != "__init__.py" and "__pycache__" not in str(py_file):
                implementation_files.append(py_file)
        return implementation_files

    def _get_test_files(self) -> list[Path]:
        """テストファイル一覧取得"""
        test_files = []
        if self.tests_dir.exists():
            for test_file in self.tests_dir.rglob("test_*.py"):
                test_files.append(test_file)
        return test_files

    def _identify_untested_files(self, implementation_files: list[Path], test_files: list[Path]) -> list[Path]:
        """未テストファイル特定"""
        test_targets = set()
        for test_file in test_files:
            relative_test_path = test_file.relative_to(self.tests_dir)
            if relative_test_path.parts[0] == "unit":
                impl_parts = relative_test_path.parts[1:]
                impl_name = impl_parts[-1].replace("test_", "").replace("_test", "")
                impl_path = self.scripts_dir / Path(*impl_parts[:-1]) / impl_name
                test_targets.add(impl_path)
        untested = []
        for impl_file in implementation_files:
            if impl_file not in test_targets:
                untested.append(impl_file)
        return untested

    def _categorize_untested_files(self, untested_files: list[Path]) -> tuple[list[str], list[str]]:
        """未テストファイルの重要度分類"""
        critical = []
        regular = []
        for file_path in untested_files:
            file_str = str(file_path)
            is_critical = any(pattern in file_str for pattern in self.critical_patterns)
            if is_critical:
                critical.append(file_str)
            else:
                regular.append(file_str)
        return (critical, regular)

    def _analyze_missing_test_directories(self, implementation_files: list[Path]) -> list[str]:
        """テストディレクトリ不足分析"""
        impl_dirs = set()
        for impl_file in implementation_files:
            relative_path = impl_file.relative_to(self.scripts_dir)
            impl_dirs.add(relative_path.parent)
        missing_dirs = []
        for impl_dir in impl_dirs:
            test_dir = self.tests_dir / "unit" / impl_dir
            if not test_dir.exists():
                missing_dirs.append(str(test_dir))
        return missing_dirs

    def _analyze_spec_compliance(self) -> tuple[int, int]:
        """SPEC準拠性分析"""
        spec_count = 0
        total_count = 0
        try:
            spec_result = subprocess.run(
                ["grep", "-r", "@pytest.mark.spec", str(self.tests_dir)], check=False, capture_output=True, text=True
            )
            spec_count = len(spec_result.stdout.splitlines()) if spec_result.returncode == 0 else 0
            test_result = subprocess.run(
                ["grep", "-r", "def test_", str(self.tests_dir)], check=False, capture_output=True, text=True
            )
            total_count = len(test_result.stdout.splitlines()) if test_result.returncode == 0 else 0
        except Exception as e:
            logger.warning(f"SPEC準拠性分析エラー: {e}")
        return (spec_count, total_count)

    def _calculate_coverage_ratio(self, implementation_files: list[Path], test_files: list[Path]) -> float:
        """カバレッジ比率計算"""
        if len(implementation_files) == 0:
            return 0.0
        return len(test_files) / len(implementation_files) * 100

    def _calculate_spec_ratio(self, spec_tests: int, total_tests: int) -> float:
        """SPEC準拠比率計算"""
        if total_tests == 0:
            return 0.0
        return spec_tests / total_tests * 100

    def _generate_recommendations(
        self, critical_untested: list[str], regular_untested: list[str], missing_dirs: list[str]
    ) -> list[str]:
        """改善提案生成"""
        recommendations = []
        if critical_untested:
            recommendations.append(f"🚨 重要モジュール{len(critical_untested)}件が未テスト - 優先対応必要")
            recommendations.extend([f"  - {file}" for file in critical_untested[:5]])
        if regular_untested:
            recommendations.append(f"📝 一般モジュール{len(regular_untested)}件が未テスト")
        if missing_dirs:
            recommendations.append(f"📁 テストディレクトリ{len(missing_dirs)}件が不足")
            recommendations.extend([f"  mkdir -p {dir}" for dir in missing_dirs[:3]])
        if len(critical_untested) > 10:
            recommendations.append("⚡ 並列テスト作成で効率化を推奨")
        return recommendations

    def export_results(self, result: CoverageAnalysisResult, output_path: Path | None = None) -> None:
        """分析結果エクスポート"""
        if output_path is None:
            output_path = self.project_root / "temp" / "coverage_analysis.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(asdict(result), f, ensure_ascii=False, indent=2)
        logger.info(f"分析結果をエクスポート: {output_path}")

    def print_summary(self, result: CoverageAnalysisResult) -> None:
        """サマリー表示"""
        console.print("\nfrom noveler.infrastructure.logging.unified_logger import get_logger\n" + "=" * 60)
        console.print("📊 テストカバレッジ分析結果")
        console.print("=" * 60)
        console.print(f"📁 実装ファイル数: {result.total_implementation_files}")
        console.print(f"🧪 テストファイル数: {result.total_test_files}")
        console.print(f"📊 カバレッジ比率: {result.coverage_ratio:.1f}%")
        if result.coverage_ratio >= 80:
            console.print("🎉 優秀なカバレッジ")
        elif result.coverage_ratio >= 60:
            console.print("✅ 良好なカバレッジ")
        else:
            console.print("⚠️  カバレッジ改善推奨")
        console.print("\n📋 SPEC準拠性:")
        console.print(f"  準拠テスト: {result.spec_compliant_tests}/{result.total_tests}")
        console.print(f"  準拠率: {result.spec_compliance_ratio:.1f}%")
        if result.untested_critical_files:
            console.print(f"\n🚨 重要未テストファイル ({len(result.untested_critical_files)}件):")
            for file in result.untested_critical_files[:5]:
                console.print(f"  - {file}")
        if result.recommendations:
            console.print("\n💡 改善提案:")
            for rec in result.recommendations:
                console.print(f"  {rec}")
        console.print("=" * 60)


def main():
    """メイン実行"""
    analyzer = TestCoverageAnalyzer()
    try:
        result = analyzer.analyze_coverage()
        analyzer.print_summary(result)
        analyzer.export_results(result)
        if result.coverage_ratio < 50 or len(result.untested_critical_files) > 5:
            sys.exit(1)
        else:
            sys.exit(0)
    except Exception:
        logger.exception("カバレッジ分析エラー")
        sys.exit(1)


if __name__ == "__main__":
    main()
