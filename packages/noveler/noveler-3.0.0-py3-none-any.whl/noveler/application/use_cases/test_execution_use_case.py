"""
テスト実行ユースケース

テストの実行、カバレッジ計測、結果のレポート作成を行う
"""

import re
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum


class ExecutionStatus(Enum):
    """テストの実行状態"""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass(frozen=True)
class ExecutionResult:
    """個別テストの実行結果"""

    test_name: str
    status: ExecutionStatus
    duration: float
    message: str | None = None

    @property
    def is_passed(self) -> bool:
        """テストが成功したか"""
        return self.status == ExecutionStatus.PASSED

    @property
    def is_failed(self) -> bool:
        """テストが失敗したか"""
        return self.status == ExecutionStatus.FAILED


@dataclass(frozen=True)
class CoverageReport:
    """カバレッジレポート"""

    total_coverage: float
    file_coverage: dict[str, float] = field(default_factory=dict)
    uncovered_lines: dict[str, list[int]] = field(default_factory=dict)

    def meets_threshold(self, threshold: float) -> bool:
        """指定された閾値を満たしているか"""
        return self.total_coverage >= threshold


@dataclass(frozen=True)
class ExecutionRequest:
    """テスト実行リクエスト"""

    test_path: str | None = None  # 特定のテストファイル/ディレクトリ
    enable_coverage: bool = False  # カバレッジ計測を有効化
    verbose: bool = False  # 詳細出力
    enable_bdd: bool = False  # BDDテストの実行
    coverage_threshold: float | None = None  # カバレッジ閾値


@dataclass(frozen=True)
class ExecutionResponse:
    """テスト実行レスポンス"""

    success: bool
    test_results: list[ExecutionResult]
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    execution_time: float
    coverage_report: CoverageReport | None = None
    error_message: str | None = None

    def get_pass_rate(self) -> float:
        """合格率を取得"""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100


class ExecuteTestsUseCase:
    """テスト実行ユースケース"""

    def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """テストを実行"""
        try:
            start_time = time.time()

            # pytestコマンドを構築
            cmd = self._build_pytest_command(request)

            # デバッグ用:実行コマンドを出力
            if request.verbose:
                pass

            # pytestを実行(信頼できるコマンドのみ)
            result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=600)

            execution_time = time.time() - start_time

            # デバッグ用:出力を表示
            if request.verbose:
                pass

            # 結果を解析
            test_results = self._parse_test_results(result.stdout)
            coverage_report = None

            if request.enable_coverage:
                coverage_report = self._parse_coverage_report(result.stdout)

            # 統計を計算
            passed = sum(1 for r in test_results if r.status == ExecutionStatus.PASSED)
            failed = sum(1 for r in test_results if r.status == ExecutionStatus.FAILED)
            skipped = sum(1 for r in test_results if r.status == ExecutionStatus.SKIPPED)

            return ExecutionResponse(
                success=(result.returncode == 0),
                test_results=test_results,
                total_tests=len(test_results),
                passed_tests=passed,
                failed_tests=failed,
                skipped_tests=skipped,
                execution_time=execution_time,
                coverage_report=coverage_report,
                error_message=None,
            )

        except Exception as e:
            return ExecutionResponse(
                success=False,
                test_results=[],
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                execution_time=0.0,
                coverage_report=None,
                error_message=str(e),
            )

    def _build_pytest_command(self, request: ExecutionRequest) -> list[str]:
        """pytestコマンドを構築"""
        cmd = ["python", "-m", "pytest"]

        # テストパスを追加
        if request.test_path:
            cmd.append(request.test_path)

        # 詳細出力
        if request.verbose:
            cmd.append("-v")

        # BDDテストの場合は特別な設定が必要な場合がある
        if request.enable_bdd and request.test_path and "features" in request.test_path:
            # pytest-bddは自動的に.featureファイルを処理
            pass

        # カバレッジオプション
        if request.enable_coverage:
            cmd.extend(["--cov", "scripts", "--cov-report", "term"])
            if request.coverage_threshold:
                cmd.extend(["--cov-fail-under", str(request.coverage_threshold)])

        return cmd

    def _parse_test_results(self, output: str) -> list[ExecutionResult]:
        """テスト結果を解析"""
        results = []

        # pytest-8.x の出力形式に対応したパターン
        # 例: "noveler/tests/integration/test_claude_export.py::test_claude_export PASSED [ 50%]"
        pattern = r"([^\s:]+::[^\s:]+)\s+(PASSED|FAILED|SKIPPED|ERROR)(?:\s+\[\s*\d+%\])?"
        matches = re.findall(pattern, output)

        for test_name, status_str in matches:
            status = ExecutionStatus(status_str.lower())

            # 失敗メッセージを抽出(あれば)
            message = None
            if status == ExecutionStatus.FAILED:
                # 失敗の詳細を探す
                failure_pattern = (
                    rf"{re.escape(test_name)}.*?(?:AssertionError|TypeError|ValueError|Exception):\s*(.+?)(?=\n|$)"
                )

                failure_match = re.search(failure_pattern, output, re.DOTALL)
                if failure_match:
                    message = failure_match.group(1).strip()

            results.append(
                ExecutionResult(
                    test_name=test_name,
                    status=status,
                    duration=0.0,  # 実際の実行時間は別途取得が必要
                    message=message,
                )
            )

        return results

    def _parse_coverage_report(self, output: str) -> CoverageReport | None:
        """カバレッジレポートを解析"""
        # TOTALの行を探す
        total_pattern = r"TOTAL\s+\d+\s+\d+\s+(\d+)%"
        total_match = re.search(total_pattern, output)

        if not total_match:
            return None

        total_coverage = float(total_match.group(1))

        # 各ファイルのカバレッジを解析
        file_coverage = {}
        file_pattern = r"(\w+\.py)\s+\d+\s+\d+\s+(\d+)%"
        file_matches = re.findall(file_pattern, output)

        for filename, coverage in file_matches:
            file_coverage[filename] = float(coverage)

        return CoverageReport(
            total_coverage=total_coverage,
            file_coverage=file_coverage,
            uncovered_lines={},  # 簡略化のため空
        )
