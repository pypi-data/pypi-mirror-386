# File: tests/unit/mcp_servers/noveler/tools/test_enhanced_test_result_analysis.py
# Purpose: Enhanced Test Result Analysis機能の単体テスト（GREEN状態）
# Context: SPEC-TEST-001に基づき、差分分析・エラーグルーピング・階層化コンテキストを検証

from __future__ import annotations

import time
from pathlib import Path

import pytest

from mcp_servers.noveler.domain.entities.mcp_tool_base import ToolRequest
from mcp_servers.noveler.tools.test_result_analysis_components import IncrementalAnalyzer
from mcp_servers.noveler.tools.test_result_analysis_tool import ResultAnalysisTool
from noveler.infrastructure.services.test_result_cache_service import (
    TestResultCacheService as CacheService,
)


@pytest.fixture()
def path_service(tmp_path_factory: pytest.TempPathFactory) -> "_CachePathService":
    base_dir = tmp_path_factory.mktemp("test_result_analysis")
    return _CachePathService(base_dir)


@pytest.fixture(autouse=True)
def _apply_path_service(path_service: "_CachePathService", monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_servers.noveler.tools.test_result_analysis_tool.create_path_service",
        lambda: path_service,
    )


class _CachePathService:
    """Minimal path service used to pre-populate cache fixtures."""

    def __init__(self, root: Path) -> None:
        self._root = root
        (self._root / "management").mkdir(parents=True, exist_ok=True)

    @property
    def project_root(self) -> Path:
        return self._root

    def get_management_dir(self) -> Path:
        path = self._root / "management"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_and_clear_fallback_events(self):
        return []


@pytest.mark.spec("SPEC-TEST-001")
class TestDeltaAnalysis:
    """差分分析機能のテスト"""

    def test_analyze_delta_with_no_previous_results(self) -> None:
        """初回実行時（前回結果なし）の差分分析"""
        tool = ResultAnalysisTool()
        current_results = {
            "summary": {"total": 10, "passed": 7, "failed": 3},
            "tests": [
                {"nodeid": "test_a.py::test_1", "outcome": "failed"},
                {"nodeid": "test_a.py::test_2", "outcome": "passed"},
                {"nodeid": "test_a.py::test_3", "outcome": "failed"},
            ],
        }

        request = ToolRequest(
            episode_number=1,
            additional_params={
                "test_result_json": current_results,
                "enable_delta_analysis": True,
                "context_detail_level": 3,
            },
        )
        response = tool.execute(request)

        delta = response.metadata["delta_analysis"]
        assert sorted(delta["newly_failed"]) == ["test_a.py::test_1", "test_a.py::test_3"]
        assert delta["newly_passed"] == []
        assert delta["improvement_rate"] == 0.0

    def test_analyze_delta_with_improvements(self) -> None:
        """改善ケース（失敗→成功）の検出"""
        tool = ResultAnalysisTool()
        previous_results = {
            "tests": [
                {"nodeid": "test_a.py::test_1", "outcome": "failed"},
                {"nodeid": "test_a.py::test_2", "outcome": "failed"},
            ],
        }
        current_results = {
            "tests": [
                {"nodeid": "test_a.py::test_1", "outcome": "passed"},
                {"nodeid": "test_a.py::test_2", "outcome": "failed"},
            ],
        }

        response = tool.execute(
            ToolRequest(
                episode_number=1,
                additional_params={
                    "test_result_json": current_results,
                    "previous_test_result_json": previous_results,
                    "enable_delta_analysis": True,
                    "context_detail_level": 3,
                },
            )
        )

        delta = response.metadata["delta_analysis"]
        assert delta["newly_passed"] == ["test_a.py::test_1"]
        assert delta["still_failing"] == ["test_a.py::test_2"]
        assert delta["regressions"] == []
        assert delta["improvement_rate"] == pytest.approx(50.0)

    def test_analyze_delta_with_regressions(self) -> None:
        """リグレッション（成功→失敗）の検出"""
        tool = ResultAnalysisTool()
        previous_results = {
            "tests": [
                {"nodeid": "test_a.py::test_1", "outcome": "passed"},
            ],
        }
        current_results = {
            "tests": [
                {"nodeid": "test_a.py::test_1", "outcome": "failed"},
            ],
        }

        response = tool.execute(
            ToolRequest(
                episode_number=1,
                additional_params={
                    "test_result_json": current_results,
                    "previous_test_result_json": previous_results,
                    "enable_delta_analysis": True,
                    "context_detail_level": 3,
                },
            )
        )

        delta = response.metadata["delta_analysis"]
        assert delta["regressions"] == ["test_a.py::test_1"]
        assert delta["newly_failed"] == []

    def test_analyze_delta_uses_cached_previous_results(self, path_service: "_CachePathService") -> None:
        """キャッシュに保存された前回結果が自動的に使用される"""
        tool = ResultAnalysisTool()

        cache_service = CacheService(path_service)
        cache_service.store_latest(
            {
                "summary": {"total": 2, "passed": 1, "failed": 1},
                "tests": [
                    {
                        "nodeid": "test_a.py::test_1",
                        "outcome": "failed",
                        "call": {"longrepr": "AssertionError: expected 1"},
                        "setup": None,
                    }
                ],
            },
            max_history=1,
        )

        assert cache_service.load_latest() is not None

        current_results = {
            "tests": [
                {"nodeid": "test_a.py::test_1", "outcome": "passed"},
            ],
        }

        response = tool.execute(
            ToolRequest(
                episode_number=None,
                additional_params={
                    "test_result_json": current_results,
                    "enable_delta_analysis": True,
                    "context_detail_level": 1,
                    "store_results": False,
                },
            )
        )

        delta = response.metadata["delta_analysis"]
        assert "counts" in delta
        assert delta["counts"]["regressions"] == 0
        assert delta["counts"]["still_failing"] == 0


@pytest.mark.spec("SPEC-TEST-001")
class TestErrorGrouping:
    """エラーグルーピング機能のテスト"""

    def test_group_identical_errors(self) -> None:
        tool = ResultAnalysisTool()
        test_results = {
            "tests": [
                {
                    "nodeid": "test_a.py::test_1",
                    "outcome": "failed",
                    "call": {"longrepr": "AssertionError: Expected 1, got 2"},
                },
                {
                    "nodeid": "test_a.py::test_2",
                    "outcome": "failed",
                    "call": {"longrepr": "AssertionError: Expected 1, got 2"},
                },
                {
                    "nodeid": "test_a.py::test_3",
                    "outcome": "failed",
                    "call": {"longrepr": "AssertionError: Expected 1, got 2"},
                },
            ],
        }

        response = tool.execute(
            ToolRequest(
                episode_number=1,
                additional_params={
                    "test_result_json": test_results,
                    "enable_error_grouping": True,
                    "context_detail_level": 3,
                },
            )
        )

        groups = response.metadata["error_groups"]
        assert len(groups) == 1
        group = groups[0]
        assert group["count"] == 3
        assert "assertionerror" in group["pattern"]

    def test_group_similar_errors_by_pattern(self) -> None:
        tool = ResultAnalysisTool()
        test_results = {
            "tests": [
                {
                    "nodeid": "test_a.py::test_1",
                    "outcome": "failed",
                    "call": {"longrepr": "ImportError: No module named 'foo'"},
                },
                {
                    "nodeid": "test_b.py::test_2",
                    "outcome": "failed",
                    "call": {"longrepr": "ImportError: No module named 'bar'"},
                },
                {
                    "nodeid": "test_c.py::test_3",
                    "outcome": "failed",
                    "call": {"longrepr": "AttributeError: 'NoneType' has no attribute 'x'"},
                },
            ],
        }

        response = tool.execute(
            ToolRequest(
                episode_number=1,
                additional_params={
                    "test_result_json": test_results,
                    "enable_error_grouping": True,
                    "context_detail_level": 3,
                },
            )
        )

        groups = response.metadata["error_groups"]
        assert len(groups) == 2
        import_group = next(group for group in groups if group["error_type"] == "import_error")
        assert import_group["count"] == 2
        assert sorted(import_group["affected_modules"]) == ["test_a.py", "test_b.py"]

    def test_group_errors_with_empty_list(self) -> None:
        tool = ResultAnalysisTool()
        test_results = {"tests": []}

        response = tool.execute(
            ToolRequest(
                episode_number=1,
                additional_params={
                    "test_result_json": test_results,
                    "enable_error_grouping": True,
                    "store_results": False,
                },
            )
        )

        assert response.metadata["error_groups"] == []


@pytest.mark.spec("SPEC-TEST-001")
class TestHierarchicalContext:
    """階層的コンテキスト機能のテスト"""

    def test_context_level_1_summary_only(self) -> None:
        tool = ResultAnalysisTool()
        test_results = {
            "summary": {"total": 100, "passed": 90, "failed": 10},
            "tests": [{"nodeid": f"test_{i}.py::test_case", "outcome": "failed"} for i in range(10)],
        }

        response = tool.execute(
            ToolRequest(
                episode_number=1,
                additional_params={
                    "test_result_json": test_results,
                    "context_detail_level": 1,
                },
            )
        )

        context = response.metadata["context"]
        assert context["detail_level"] == 1
        assert "high_priority_issues" not in context
        assert "issues" not in context
        assert "summary" in context
        assert context["summary"]["failed"] == 10

    def test_context_level_2_important_details(self) -> None:
        tool = ResultAnalysisTool()
        test_results = {
            "summary": {"total": 100, "passed": 80, "failed": 20, "error": 2},
            "tests": [
                {
                    "nodeid": "critical_test.py::test_1",
                    "outcome": "failed",
                    "call": {"longrepr": "ImportError: Critical module missing"},
                },
                {
                    "nodeid": "critical_test.py::test_2",
                    "outcome": "failed",
                    "call": {"longrepr": "AssertionError: mismatch"},
                },
            ],
        }

        response = tool.execute(
            ToolRequest(
                episode_number=1,
                additional_params={
                    "test_result_json": test_results,
                    "context_detail_level": 2,
                    "enable_error_grouping": True,
                },
            )
        )

        context = response.metadata["context"]
        assert context["detail_level"] == 2
        assert context["high_priority_issues"]
        assert "issues" not in context
        assert context["top_error_groups"][0]["count"] >= 1

    def test_context_level_3_full_details(self) -> None:
        tool = ResultAnalysisTool()
        test_results = {
            "summary": {"total": 5, "passed": 3, "failed": 2},
            "tests": [
                {
                    "nodeid": "test_full.py::test_a",
                    "outcome": "failed",
                    "call": {"longrepr": "AssertionError: expected True, got False"},
                },
                {
                    "nodeid": "test_full.py::test_b",
                    "outcome": "error",
                    "setup": {"longrepr": "ImportError: cannot import name 'x'"},
                },
            ],
        }

        response = tool.execute(
            ToolRequest(
                episode_number=1,
                additional_params={
                    "test_result_json": test_results,
                    "context_detail_level": 3,
                    "enable_error_grouping": True,
                },
            )
        )

        context = response.metadata["context"]
        assert context["detail_level"] == 3
        assert len(context["issues"]) >= 2
        assert sum(group["count"] for group in context["error_groups"]) == 2


@pytest.mark.spec("SPEC-TEST-001")
class TestBackwardCompatibility:
    """後方互換性のテスト"""

    def test_existing_api_without_new_features(self) -> None:
        tool = ResultAnalysisTool()
        test_results = {
            "summary": {"total": 5, "passed": 3, "failed": 2},
            "tests": [
                {"nodeid": "test_a.py::test_1", "outcome": "failed"},
                {"nodeid": "test_a.py::test_2", "outcome": "passed"},
            ],
        }

        request = ToolRequest(
            episode_number=1,
            additional_params={
                "test_result_json": test_results,
                "focus_on_failures": True,
                "max_issues": 20,
                "include_suggestions": True,
            },
        )
        response = tool.execute(request)

        assert response.success is True
        assert response.issues
        assert response.score is not None

    def test_new_optional_parameters_in_schema(self) -> None:
        tool = ResultAnalysisTool()
        schema = tool.get_input_schema()
        properties = schema["properties"]
        for key in ("enable_delta_analysis", "enable_error_grouping", "context_detail_level"):
            assert key in properties
            assert properties[key]["description"]


@pytest.mark.spec("SPEC-TEST-001")
class TestPerformance:
    """パフォーマンステスト"""

    def test_delta_analysis_performance(self) -> None:
        analyzer = IncrementalAnalyzer()
        previous = {
            "tests": [{"nodeid": f"test_{i}.py::test", "outcome": "passed"} for i in range(1000)],
        }
        current = {
            "tests": [
                {
                    "nodeid": f"test_{i}.py::test",
                    "outcome": "failed" if i % 5 == 0 else "passed",
                }
                for i in range(1000)
            ],
        }

        start = time.perf_counter()
        delta = analyzer.analyze_delta(current, previous)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.5
        assert len(delta.newly_failed) <= 200

    def test_memory_usage_for_cache(self) -> None:
        analyzer = IncrementalAnalyzer()
        analyzer.analyze_delta({"tests": []})
        assert not hasattr(analyzer, "__dict__")
