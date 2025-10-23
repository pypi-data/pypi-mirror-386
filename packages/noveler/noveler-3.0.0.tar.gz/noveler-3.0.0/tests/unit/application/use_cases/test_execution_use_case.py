"""
テスト実行ユースケースのユニットテスト


仕様書: SPEC-APPLICATION-USE-CASES
"""

from unittest.mock import MagicMock, patch

import pytest

from noveler.application.use_cases.test_execution_use_case import (
    CoverageReport,
    ExecuteTestsUseCase,
    ExecutionRequest,
    ExecutionResponse,
    ExecutionResult,
    ExecutionStatus,
)


class TestExecutionRequest:
    """ExecutionRequestのテスト"""

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-CREATE_WITH_DEFAULTS")
    def test_create_with_defaults(self) -> None:
        """デフォルト値でリクエストを作成"""
        request = ExecutionRequest()

        assert request.test_path is None
        assert request.enable_coverage is False
        assert request.verbose is False
        assert request.enable_bdd is False
        assert request.coverage_threshold is None

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-CREATE_WITH_SPECIFIC")
    def test_create_with_specific_test_path(self) -> None:
        """特定のテストパスを指定してリクエストを作成"""
        request = ExecutionRequest(test_path="tests/unit/test_example.py", enable_coverage=True, verbose=True)

        assert request.test_path == "tests/unit/test_example.py"
        assert request.enable_coverage is True
        assert request.verbose is True

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-CREATE_WITH_BDD_ENAB")
    def test_create_with_bdd_enabled(self) -> None:
        """BDDテストを有効にしてリクエストを作成"""
        request = ExecutionRequest(enable_bdd=True, test_path="tests/e2e/features/")

        assert request.enable_bdd is True
        assert request.test_path == "tests/e2e/features/"

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-CREATE_WITH_COVERAGE")
    def test_create_with_coverage_threshold(self) -> None:
        """カバレッジ閾値を指定してリクエストを作成"""
        request = ExecutionRequest(enable_coverage=True, coverage_threshold=80.0)

        assert request.enable_coverage is True
        assert request.coverage_threshold == 80.0


class TestExecutionResult:
    """ExecutionResultのテスト"""

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-CREATE_SUCCESS_RESUL")
    def test_create_success_result(self) -> None:
        """成功結果を作成"""
        result = ExecutionResult(test_name="test_example", status=ExecutionStatus.PASSED, duration=0.05, message=None)

        assert result.test_name == "test_example"
        assert result.status == ExecutionStatus.PASSED
        assert result.duration == 0.05
        assert result.message is None
        assert result.is_passed is True
        assert result.is_failed is False

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-CREATE_FAILED_RESULT")
    def test_create_failed_result(self) -> None:
        """失敗結果を作成"""
        result = ExecutionResult(
            test_name="test_example",
            status=ExecutionStatus.FAILED,
            duration=0.03,
            message="AssertionError: Expected 1 but got 2",
        )

        assert result.status == ExecutionStatus.FAILED
        assert result.message == "AssertionError: Expected 1 but got 2"
        assert result.is_passed is False
        assert result.is_failed is True

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-CREATE_SKIPPED_RESUL")
    def test_create_skipped_result(self) -> None:
        """スキップ結果を作成"""
        result = ExecutionResult(
            test_name="test_example",
            status=ExecutionStatus.SKIPPED,
            duration=0.0,
            message="Test requires specific environment",
        )

        assert result.status == ExecutionStatus.SKIPPED
        assert result.is_passed is False
        assert result.is_failed is False


class TestCoverageReport:
    """CoverageReportのテスト"""

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-CREATE_COVERAGE_REPO")
    def test_create_coverage_report(self) -> None:
        """カバレッジレポートを作成"""
        report = CoverageReport(
            total_coverage=85.5,
            file_coverage={"module1.py": 90.0, "module2.py": 80.0, "module3.py": 86.5},
            uncovered_lines={"module1.py": [25, 26, 30], "module2.py": [45, 46, 47, 48]},
        )

        assert report.total_coverage == 85.5
        assert report.file_coverage["module1.py"] == 90.0
        assert len(report.uncovered_lines["module2.py"]) == 4
        assert report.meets_threshold(80.0) is True
        assert report.meets_threshold(90.0) is False


class TestExecutionResponse:
    """ExecutionResponseのテスト"""

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-CREATE_SUCCESSFUL_RE")
    def test_create_successful_response(self) -> None:
        """成功レスポンスを作成"""
        results = [
            ExecutionResult("test_1", ExecutionStatus.PASSED, 0.05, None),
            ExecutionResult("test_2", ExecutionStatus.PASSED, 0.03, None),
            ExecutionResult("test_3", ExecutionStatus.SKIPPED, 0.0, "Skipped"),
        ]

        response = ExecutionResponse(
            success=True,
            test_results=results,
            total_tests=3,
            passed_tests=2,
            failed_tests=0,
            skipped_tests=1,
            execution_time=0.08,
            coverage_report=None,
            error_message=None,
        )

        assert response.success is True
        assert response.total_tests == 3
        assert response.passed_tests == 2
        assert response.failed_tests == 0
        assert response.skipped_tests == 1
        assert response.execution_time == 0.08
        assert response.get_pass_rate() == pytest.approx(66.67, 0.01)

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-CREATE_FAILED_RESPON")
    def test_create_failed_response(self) -> None:
        """失敗レスポンスを作成"""
        results = [
            ExecutionResult("test_1", ExecutionStatus.PASSED, 0.05, None),
            ExecutionResult("test_2", ExecutionStatus.FAILED, 0.03, "Assertion failed"),
            ExecutionResult("test_3", ExecutionStatus.FAILED, 0.04, "TypeError"),
        ]

        response = ExecutionResponse(
            success=False,
            test_results=results,
            total_tests=3,
            passed_tests=1,
            failed_tests=2,
            skipped_tests=0,
            execution_time=0.12,
            coverage_report=None,
            error_message=None,
        )

        assert response.success is False
        assert response.failed_tests == 2
        assert response.get_pass_rate() == pytest.approx(33.33, 0.01)

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-CREATE_ERROR_RESPONS")
    def test_create_error_response(self) -> None:
        """エラーレスポンスを作成"""
        response = ExecutionResponse(
            success=False,
            test_results=[],
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            skipped_tests=0,
            execution_time=0.0,
            coverage_report=None,
            error_message="Failed to run pytest: Module not found",
        )

        assert response.success is False
        assert response.error_message == "Failed to run pytest: Module not found"
        assert response.get_pass_rate() == 0.0


class TestExecuteTestsUseCase:
    """ExecuteTestsUseCaseのテスト"""

    @pytest.fixture
    def use_case(self):
        """ユースケースのフィクスチャ"""
        return ExecuteTestsUseCase()

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-EXECUTE_ALL_TESTS_SU")
    def test_execute_all_tests_successfully(self, use_case: object) -> None:
        """全てのテストを正常に実行"""
        request = ExecutionRequest()

        with patch("subprocess.run") as mock_run:
            # pytestの実行結果をモック
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""
                ============================= test session starts ==============================
                collected 5 items

                tests/unit/test_example.py::test_one PASSED                             [ 20%]
                tests/unit/test_example.py::test_two PASSED                             [ 40%]
                tests/unit/test_example.py::test_three PASSED                           [ 60%]
                tests/unit/test_example.py::test_four PASSED                            [ 80%]
                tests/unit/test_example.py::test_five PASSED                            [100%]

                ============================== 5 passed in 0.25s ===============================
                """,
                stderr="",
            )

            response = use_case.execute(request)

        assert response.success is True
        assert response.total_tests == 5
        assert response.passed_tests == 5
        assert response.failed_tests == 0
        assert response.execution_time > 0
        assert len(response.test_results) == 5

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-EXECUTE_SPECIFIC_TES")
    def test_execute_specific_test_file(self, use_case: object) -> None:
        """特定のテストファイルを実行"""
        request = ExecutionRequest(test_path="tests/unit/test_specific.py", verbose=True)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""
                ============================= test session starts ==============================
                collected 2 items

                tests/unit/test_specific.py::test_one PASSED                            [ 50%]
                tests/unit/test_specific.py::test_two PASSED                            [100%]

                ============================== 2 passed in 0.10s ===============================
                """,
                stderr="",
            )

            response = use_case.execute(request)

        assert response.success is True
        assert response.total_tests == 2
        assert response.passed_tests == 2
        # 実行コマンドに指定したパスが含まれることを確認
        mock_run.assert_called_once()
        assert "tests/unit/test_specific.py" in mock_run.call_args[0][0]
        assert "-v" in mock_run.call_args[0][0]  # verbose オプション

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-EXECUTE_WITH_COVERAG")
    def test_execute_with_coverage(self, use_case: object) -> None:
        """カバレッジ計測付きでテストを実行"""
        request = ExecutionRequest(enable_coverage=True, coverage_threshold=80.0)

        with patch("subprocess.run") as mock_run:
            # カバレッジ付きの実行結果をモック
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""
                ============================= test session starts ==============================
                collected 3 items

                tests/unit/test_example.py::test_one PASSED                             [ 33%]
                tests/unit/test_example.py::test_two PASSED                             [ 66%]
                tests/unit/test_example.py::test_three PASSED                           [100%]

                ---------- coverage: platform linux, python 3.9.0-final-0 -----------
                Name                  Stmts   Miss  Cover
                -----------------------------------------
                module1.py               50      5    90%
                module2.py               40      8    80%
                module3.py               30      4    87%
                -----------------------------------------
                TOTAL                   120     17    86%

                ============================== 3 passed in 0.15s ===============================
                """,
                stderr="",
            )

            response = use_case.execute(request)

        assert response.success is True
        assert response.total_tests == 3
        assert response.coverage_report is not None
        assert response.coverage_report.total_coverage == 86.0
        assert response.coverage_report.meets_threshold(80.0) is True
        # 実行コマンドにカバレッジオプションが含まれることを確認
        mock_run.assert_called_once()
        assert "--cov" in " ".join(mock_run.call_args[0][0])

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-EXECUTE_WITH_FAILED_")
    def test_execute_with_failed_tests(self, use_case: object) -> None:
        """失敗したテストがある場合の実行"""
        request = ExecutionRequest()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,  # 失敗を示す終了コード
                stdout="""
                ============================= test session starts ==============================
                collected 4 items

                tests/unit/test_example.py::test_one PASSED                             [ 25%]
                tests/unit/test_example.py::test_two FAILED                             [ 50%]
                tests/unit/test_example.py::test_three PASSED                           [ 75%]
                tests/unit/test_example.py::test_four FAILED                            [100%]

                =================================== FAILURES ===================================
                _________________________________ test_two _________________________________
                AssertionError: assert 1 == 2

                _________________________________ test_four ________________________________
                TypeError: unsupported operand type(s)

                ========================= 2 failed, 2 passed in 0.20s ==========================
                """,
                stderr="",
            )

            response = use_case.execute(request)

        assert response.success is False
        assert response.total_tests == 4
        assert response.passed_tests == 2
        assert response.failed_tests == 2
        assert response.get_pass_rate() == 50.0
        # 失敗したテストの詳細が含まれることを確認
        failed_tests = [r for r in response.test_results if r.is_failed]
        assert len(failed_tests) == 2

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-EXECUTE_BDD_TESTS")
    def test_execute_bdd_tests(self, use_case: object) -> None:
        """BDDテストを実行"""
        request = ExecutionRequest(enable_bdd=True, test_path="tests/e2e/features/")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""
                ============================= test session starts ==============================
                collected 2 items

                tests/e2e/features/episode_creation.feature::test_create_new_episode PASSED [ 50%]
                tests/e2e/features/episode_creation.feature::test_create_duplicate PASSED   [100%]

                ============================== 2 passed in 0.30s ===============================
                """,
                stderr="",
            )

            response = use_case.execute(request)

        assert response.success is True
        assert response.total_tests == 2
        # BDD実行時はpytest-bddプラグインが使用されることを確認
        mock_run.assert_called_once()
        assert "tests/e2e/features/" in mock_run.call_args[0][0]

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-EXECUTE_WITH_PYTEST_")
    def test_execute_with_pytest_error(self, use_case: object) -> None:
        """pytest実行エラーが発生した場合"""
        request = ExecutionRequest()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("pytest not found")

            response = use_case.execute(request)

        assert response.success is False
        assert response.error_message is not None
        assert "pytest not found" in response.error_message
        assert response.total_tests == 0

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-EXECUTE_WITH_COVERAG")
    def test_execute_with_coverage_below_threshold(self, use_case: object) -> None:
        """カバレッジが閾値を下回る場合"""
        request = ExecutionRequest(
            enable_coverage=True,
            coverage_threshold=90.0,  # 高い閾値
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""
                ============================= test session starts ==============================
                collected 2 items

                tests/unit/test_example.py::test_one PASSED                             [ 50%]
                tests/unit/test_example.py::test_two PASSED                             [100%]

                ---------- coverage: platform linux, python 3.9.0-final-0 -----------
                TOTAL                   100     20    80%

                ============================== 2 passed in 0.10s ===============================
                """,
                stderr="",
            )

            response = use_case.execute(request)

        # テストは成功しているが、カバレッジが閾値を下回っている
        assert response.success is True  # テスト自体は成功
        assert response.coverage_report.total_coverage == 80.0
        assert response.coverage_report.meets_threshold(90.0) is False

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-PARSE_TEST_RESULTS")
    def test_parse_test_results(self, use_case: object) -> None:
        """テスト結果のパース処理をテスト"""
        output = """
        tests/unit/test_example.py::test_one PASSED                             [ 25%]
        tests/unit/test_example.py::test_two FAILED                             [ 50%]
        tests/unit/test_example.py::test_three SKIPPED                          [ 75%]
        tests/unit/test_example.py::test_four PASSED                            [100%]
        """

        results = use_case._parse_test_results(output)

        assert len(results) == 4
        assert results[0].test_name == "tests/unit/test_example.py::test_one"
        assert results[0].status == ExecutionStatus.PASSED
        assert results[1].status == ExecutionStatus.FAILED
        assert results[2].status == ExecutionStatus.SKIPPED
        assert results[3].status == ExecutionStatus.PASSED

    @pytest.mark.spec("SPEC-EXECUTION_USE_CASE-PARSE_COVERAGE_REPOR")
    def test_parse_coverage_report(self, use_case: object) -> None:
        """カバレッジレポートのパース処理をテスト"""
        output = """
        ---------- coverage: platform linux, python 3.9.0-final-0 -----------
        Name                  Stmts   Miss  Cover
        -----------------------------------------
        module1.py               50      5    90%
        module2.py               40      8    80%
        module3.py               30      4    87%
        -----------------------------------------
        TOTAL                   120     17    86%
        """

        report = use_case._parse_coverage_report(output)

        assert report is not None
        assert report.total_coverage == 86.0
        assert report.file_coverage["module1.py"] == 90.0
        assert report.file_coverage["module2.py"] == 80.0
        assert report.file_coverage["module3.py"] == 87.0
