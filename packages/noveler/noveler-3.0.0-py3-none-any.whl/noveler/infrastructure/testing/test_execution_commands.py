#!/usr/bin/env python3
"""テスト実行コマンド群

Command Patternによる複雑度軽減実装
各処理を独立したCommandクラスに分離
"""

import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from noveler.application.use_cases.test_execution_use_case import (
    ExecuteTestsUseCase,
    ExecutionRequest,
    ExecutionStatus,
)


@dataclass
class TestExecutionContext:
    """テスト実行コンテキスト - 各コマンド間でデータを共有"""

    guide_root: Path
    target: str | None
    verbose: bool
    coverage: bool

    # 処理データ
    test_base_dir: Path | None = None
    test_path: str | None = None
    use_case: ExecuteTestsUseCase | None = None
    request: ExecutionRequest | None = None
    response: object | None = None
    status_icons: dict[ExecutionStatus, str] | None = None


@dataclass
class TestExecutionResult:
    """テスト実行結果"""

    success: bool
    message: str
    context: TestExecutionContext | None = None


class TestExecutionCommand(ABC):
    """テスト実行コマンドの基底クラス"""

    @abstractmethod
    def execute(self, context: TestExecutionContext) -> TestExecutionResult:
        """コマンドを実行する"""


class TestDirectoryValidationCommand(TestExecutionCommand):
    """テストディレクトリ検証コマンド"""

    def execute(self, context: TestExecutionContext) -> TestExecutionResult:
        """テストディレクトリの存在を検証"""
        try:
            context.test_base_dir = context.guide_root / "scripts" / "tests"

            if not context.test_base_dir.exists():
                return TestExecutionResult(success=False, message="テストディレクトリが見つかりません")

            return TestExecutionResult(success=True, message="テストディレクトリ検証完了")
        except Exception:
            return TestExecutionResult(success=False, message="テストディレクトリ検証中にエラーが発生しました")


class TestPathResolutionCommand(TestExecutionCommand):
    """テストパス解決コマンド"""

    def execute(self, context: TestExecutionContext) -> TestExecutionResult:
        """テストパスを解決"""
        try:
            if context.target:
                if context.target.endswith(".py"):
                    # 絶対パスまたは相対パスとして解釈
                    target_path = Path(context.target)
                    if target_path.is_absolute():
                        context.test_path = str(target_path)
                    else:
                        # 相対パスの場合、test_base_dirからの相対パスとして解釈
                        context.test_path = str(context.test_base_dir / context.target)
                else:
                    # モジュール名の場合
                    context.test_path = context.target
            else:
                context.test_path = str(context.test_base_dir)

            return TestExecutionResult(success=True, message="テストパス解決完了")
        except Exception:
            return TestExecutionResult(success=False, message="テストパス解決中にエラーが発生しました")


class UseCaseInitializationCommand(TestExecutionCommand):
    """ユースケース初期化コマンド"""

    def execute(self, context: TestExecutionContext) -> TestExecutionResult:
        """ユースケースとリクエストを初期化"""
        try:
            # ユースケースを作成
            context.use_case = ExecuteTestsUseCase()

            # リクエストを作成
            context.request = ExecutionRequest(
                test_path=context.test_path,
                verbose=context.verbose,
                enable_coverage=context.coverage,
                coverage_threshold=60.0,  # デフォルトのカバレッジ閾値
                enable_bdd=False,  # 通常のpytestテスト
            )

            # 状態アイコンを定義
            context.status_icons = {
                ExecutionStatus.PASSED: "✅",
                ExecutionStatus.FAILED: "❌",
                ExecutionStatus.SKIPPED: "⏭️",
                ExecutionStatus.ERROR: "💥",
            }

            return TestExecutionResult(success=True, message="ユースケース初期化完了")
        except Exception:
            return TestExecutionResult(success=False, message="ユースケース初期化中にエラーが発生しました")


class TestRunCommand(TestExecutionCommand):
    """テスト実行コマンド"""

    def execute(self, context: TestExecutionContext) -> TestExecutionResult:
        """テストを実行"""
        try:

            if context.verbose:
                pass

            # ユースケースが正しく初期化されているか確認
            if not context.use_case:
                return TestExecutionResult(success=False, message="テスト実行ユースケースが初期化されていません")

            if not context.request:
                return TestExecutionResult(success=False, message="テスト実行リクエストが初期化されていません")

            # リアルタイム実行表示

            # テスト開始時刻を記録
            # import time  # Moved to top-level

            start_time = time.time()
            #  # Moved to top-level
            if context.verbose:
                datetime.fromtimestamp(start_time, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                # print(f"📂 テスト対象: {context.target}") # Moved to top-level
                if context.coverage:
                    pass

            # テストを実行
            context.response = context.use_case.execute(context.request)

            # 実行時間を計算
            end_time = time.time()
            end_time - start_time


            if not context.response:
                return TestExecutionResult(success=False, message="テスト実行レスポンスがNullです")

            # 実行結果の即座表示
            if hasattr(context.response, "success") and context.response.success is not None:
                pass

            # 実行時間の表示
            if hasattr(context.response, "execution_time") and context.response.execution_time is not None:
                pass
            else:
                pass

            # 基本統計の即座表示
            if hasattr(context.response, "total_tests") and context.response.total_tests is not None:
                total = context.response.total_tests
                passed = getattr(context.response, "passed_tests", 0)
                getattr(context.response, "failed_tests", 0)
                getattr(context.response, "skipped_tests", 0)


                if total > 0:
                    (passed / total) * 100

            if context.verbose:
                if hasattr(context.response, "status"):
                    pass

            return TestExecutionResult(success=True, message="テスト実行完了")
        except Exception:
            if context.verbose:
                traceback.print_exc()

    # return TestExecutionResult(success=False, message="テスト実行中にエラーが発生しました") # Moved to top-level


class TestResultDisplayCommand(TestExecutionCommand):
    """テスト結果表示コマンド"""

    def execute(self, context: TestExecutionContext) -> TestExecutionResult:
        """テスト結果を表示"""
        try:
            response = context.response

            # レスポンスの存在チェック
            if not response:
                return TestExecutionResult(success=False, message="テスト実行レスポンスが存在しません")

            # ステータスアイコンの存在チェック
            if not context.status_icons:
                return TestExecutionResult(success=False, message="ステータスアイコンが設定されていません")

            # ステータスの安全な取得
            # ExecutionResponseにはstatusフィールドがないため、successから推定
            inferred_status = ExecutionStatus.PASSED if response.success else ExecutionStatus.FAILED
            context.status_icons.get(inferred_status, "❓")
            inferred_status.value if hasattr(inferred_status, "value") else str(inferred_status)

            # 基本結果を表示

            # 実行時間の安全な表示
            if hasattr(response, "execution_time") and response.execution_time is not None:
                pass

            # テスト数の安全な表示
            if hasattr(response, "total_tests") and response.total_tests is not None:
                pass

            if hasattr(response, "passed_tests") and response.passed_tests is not None:
                pass

            if hasattr(response, "failed_tests") and response.failed_tests is not None:
                pass

            if hasattr(response, "skipped_tests") and response.skipped_tests is not None:
                pass

            # 合格率の安全な表示
            if hasattr(response, "pass_rate") and response.pass_rate is not None:
                pass

            # デバッグ情報(verbose時)
            if context.verbose:
                pass

            return TestExecutionResult(success=True, message="テスト結果表示完了")
        except Exception:
            if context.verbose:
                # import traceback  # Moved to top-level

                traceback.print_exc()

    # return TestExecutionResult(success=False, message="テスト結果表示中にエラーが発生しました") # Moved to top-level


class CoverageReportDisplayCommand(TestExecutionCommand):
    """カバレッジレポート表示コマンド"""

    def execute(self, context: TestExecutionContext) -> TestExecutionResult:
        """カバレッジレポートを表示"""
        try:
            response = context.response

            # レスポンスの存在チェック
            if not response:
                if context.verbose:
                    pass
                return TestExecutionResult(success=True, message="カバレッジレポートなし(レスポンスなし)")

            # カバレッジレポートの存在チェック
            if not hasattr(response, "coverage_report") or not response.coverage_report:
                if context.verbose:
                    pass
                return TestExecutionResult(success=True, message="カバレッジレポートなし")

            coverage_report = response.coverage_report


            # 全体カバレッジの安全な表示
            if hasattr(coverage_report, "total_coverage") and coverage_report.total_coverage is not None:
                pass

            # 閾値の安全な表示
            if hasattr(coverage_report, "threshold") and coverage_report.threshold is not None:
                pass

            # ファイル別カバレッジの安全な表示
            if hasattr(coverage_report, "file_coverages") and coverage_report.file_coverages:
                try:
                    # 上位5件のファイルを表示
                    for fc in sorted(
                        coverage_report.file_coverages, key=lambda x: getattr(x, "coverage", 0), reverse=True
                    )[:5]:
                        if hasattr(fc, "filename") and hasattr(fc, "coverage"):
                            pass
                except Exception:
                    if context.verbose:
                        pass
                    # フォールバック: 単純にリスト表示
                    for _i, fc in enumerate(coverage_report.file_coverages[:5]):
                        if hasattr(fc, "filename") and hasattr(fc, "coverage"):
                            pass

            return TestExecutionResult(success=True, message="カバレッジレポート表示完了")
        except Exception:
            if context.verbose:
                # import traceback  # Moved to top-level

                traceback.print_exc()

    # return TestExecutionResult(success=False, message="カバレッジレポート表示中にエラーが発生しました") # Moved to top-level


class FailedTestDetailDisplayCommand(TestExecutionCommand):
    """失敗テスト詳細表示コマンド"""

    def execute(self, context: TestExecutionContext) -> TestExecutionResult:
        """失敗したテストの詳細を表示(リファクタリング済み:複雑度20→6に削減)"""
        try:
            # 前提条件の検証
            validation_result = self._validate_prerequisites(context)
            if validation_result:
                return validation_result

            # ExecutionStatusのインポート
            execution_status = self._import_execution_status(context)
            if not execution_status:
                return TestExecutionResult(success=True, message="失敗テスト詳細表示なし(インポートエラー)")

            # 失敗テストの表示
            failed_found = self._display_failed_tests(context, execution_status)

            if not failed_found:
                pass

            return TestExecutionResult(success=True, message="失敗テスト詳細表示完了")
        except Exception as e:
            return self._handle_execution_error(e, context)

    def _validate_prerequisites(self, context: TestExecutionContext) -> TestExecutionResult | None:
        """前提条件を検証"""
        response = context.response

        # レスポンスの存在チェック
        if not response:
            if context.verbose:
                pass
            return TestExecutionResult(success=True, message="失敗テスト詳細なし(レスポンスなし)")

        # 失敗テスト数のチェック
        failed_count = getattr(response, "failed_tests", 0)
        if failed_count == 0:
            if context.verbose:
                pass
            return TestExecutionResult(success=True, message="失敗したテストなし")

        # テスト結果の存在チェック
        test_results = getattr(response, "test_results", None)
        if not test_results:
            if context.verbose:
                pass
            return TestExecutionResult(success=True, message="失敗したテストなし(結果データなし)")

        return None

    def _import_execution_status(self, context: TestExecutionContext) -> ExecutionStatus | None:
        """ExecutionStatusをインポート"""
        try:
            # from noveler.application.use_cases.test_execution_use_case import ExecutionStatus  # Moved to top-level
            return ExecutionStatus
        except ImportError:
            if context.verbose:
                pass
            return None

    def _display_failed_tests(self, context: TestExecutionContext, execution_status: ExecutionStatus) -> bool:
        """失敗したテストを表示"""

        failed_found = False
        test_results = getattr(context.response, "test_results", [])

        for result in test_results:
            try:
                if self._is_failed_test(result, execution_status):
                    failed_found = True
                    self._display_single_failed_test(result)
            except Exception:
                if context.verbose:
                    pass

        return failed_found

    def _is_failed_test(self, result: object, execution_status: ExecutionStatus) -> bool:
        """テストが失敗しているかチェック"""
        return hasattr(result, "status") and result.status == execution_status.FAILED

    def _display_single_failed_test(self, result: object) -> None:
        """単一の失敗テストを表示"""
        # テスト名の表示
        getattr(result, "test_name", "不明なテスト")

        # エラーメッセージの表示
        if hasattr(result, "error_message") and result.error_message:
            self._display_error_message(result.error_message)

    def _display_error_message(self, error_message: str) -> None:
        """エラーメッセージを整形して表示"""
        error_lines = str(error_message).split("\n")
        for line in error_lines[:3]:  # 最初の3行のみ表示
            if line.strip():
                pass
        if len(error_lines) > 3:
            pass

    def _handle_execution_error(self, error: Exception, context: TestExecutionContext) -> TestExecutionResult:
        """実行エラーを処理"""
        if context.verbose:
            # import traceback  # Moved to top-level
            traceback.print_exc()
        return TestExecutionResult(success=False, message="失敗テスト詳細表示中にエラーが発生しました")

    #  # Moved to top-level


class TestExecutionController:
    """テスト実行コントローラー"""

    def __init__(self, guide_root: Path) -> None:
        self.guide_root = guide_root
        self.commands = [
            TestDirectoryValidationCommand(),
            TestPathResolutionCommand(),
            UseCaseInitializationCommand(),
            TestRunCommand(),
            TestResultDisplayCommand(),
            CoverageReportDisplayCommand(),
            FailedTestDetailDisplayCommand(),
        ]

    def execute(self, target: str | None, verbose: bool, coverage: bool = False) -> bool:
        """テストを実行"""
        context = TestExecutionContext(guide_root=self.guide_root, target=target, verbose=verbose, coverage=coverage)

        for command in self.commands:
            try:
                result = command.execute(context)
                if not result.success:
                    # エラーメッセージは各コマンドで表示済み
                    return False

            except Exception:
                return False

        # 最終的な成功/失敗を判定
        return context.response and context.response.success
