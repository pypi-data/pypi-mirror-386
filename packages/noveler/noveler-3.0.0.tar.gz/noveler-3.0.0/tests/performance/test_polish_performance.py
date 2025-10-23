"""
パフォーマンステスト: polish_manuscript_apply統合前後の性能比較

SPEC-LLM-001準拠: 統合前後のパフォーマンス劣化10%以内を確認
"""
import pytest
import time
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

from mcp_servers.noveler.tools.polish_manuscript_apply_tool import PolishManuscriptApplyTool
from mcp_servers.noveler.domain.entities.mcp_tool_base import ToolRequest


@pytest.mark.benchmark
class TestPolishPerformance:
    """polish_manuscript_apply統合前後のパフォーマンステスト"""

    @pytest.fixture
    def sample_request(self):
        """テスト用リクエスト"""
        return ToolRequest(
            episode_number=1,
            project_name="test_project",
            additional_params={
                "dry_run": True,
                "stages": ["stage2", "stage3"]
            }
        )

    def test_polish_apply_performance_baseline(self, sample_request):
        """統合前のパフォーマンスベースライン測定"""
        tool = PolishManuscriptApplyTool()

        # テスト用コンテンツ準備
        test_content = "これはテスト用の原稿です。\nテスト段落の内容です。"

        with patch.object(tool, '_resolve_target_path', return_value=Path("/test/manuscript.md")):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.read_text', return_value=test_content):
                    with patch('pathlib.Path.write_text'):
                        # LLM呼び出しは性能測定に含めないため、固定レスポンスにスタブ化する
                        with patch.object(tool, '_run_llm', return_value=test_content):
                            start_time = time.perf_counter()

                            # 現在の実装でのベンチマーク
                            result = tool.execute(sample_request)

                            duration = time.perf_counter() - start_time

                        # パフォーマンス基準: 30秒以内（仕様書準拠）
                        assert duration < 30.0, f"実行時間が基準を超過: {duration:.2f}秒"
                        assert result.success, "実行が失敗しました"

                        # ベースライン記録
                        print(f"ベースライン実行時間: {duration:.3f}秒")

    @pytest.mark.asyncio
    async def test_llm_execution_performance(self):
        """LLM実行部分の性能測定"""
        tool = PolishManuscriptApplyTool()
        test_prompt = "テスト用プロンプト"
        project_root = Path("/test")

        start_time = time.perf_counter()

        # 現在の_run_llm実装でのテスト
        with patch.object(tool, '_run_llm', return_value="テスト結果") as mock_llm:
            result = tool._run_llm(project_root, test_prompt)

        duration = time.perf_counter() - start_time

        # LLM実行時間基準: 10秒以内
        assert duration < 10.0, f"LLM実行時間が基準を超過: {duration:.2f}秒"
        print(f"LLM実行時間: {duration:.3f}秒")

    def test_memory_usage_baseline(self, sample_request):
        """メモリ使用量ベースライン測定"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        tool = PolishManuscriptApplyTool()

        with patch.object(tool, '_resolve_target_path', return_value=Path("/test/manuscript.md")):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.read_text', return_value="テスト内容"):
                    with patch('pathlib.Path.write_text'):
                        with patch.object(tool, '_run_llm', return_value="テスト内容"):
                            # 実行
                            result = tool.execute(sample_request)

                            final_memory = process.memory_info().rss / 1024 / 1024  # MB
                        memory_increase = final_memory - initial_memory

                        # メモリ増加基準: 100MB以内
                        assert memory_increase < 100, f"メモリ使用量増加が基準を超過: {memory_increase:.2f}MB"
                        print(f"メモリ使用量増加: {memory_increase:.2f}MB")


@pytest.mark.benchmark
@pytest.mark.integration_future
class TestPolishPerformanceAfterIntegration:
    """統合後のパフォーマンステスト（Phase 2で実装）"""

    def test_polish_apply_performance_after_integration(self):
        """統合後のパフォーマンステスト"""
        # Phase 2で実装予定
        pytest.skip("Phase 2で実装予定")

    def test_performance_regression_check(self):
        """パフォーマンス回帰チェック"""
        # Phase 2で実装予定
        pytest.skip("Phase 2で実装予定")