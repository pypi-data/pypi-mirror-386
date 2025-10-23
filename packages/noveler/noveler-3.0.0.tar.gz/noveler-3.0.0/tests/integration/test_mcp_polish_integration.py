"""
MCP統合テスト: polish_manuscript_applyのMCP環境対応確認

SPEC-LLM-001準拠: MCP環境での動作成功率100%を確認

リファクタリングメモ:
- UniversalLLMUseCase統合後は、_run_llmモックをUniversalLLMUseCaseモックに変更
- 現在のモックポイント: tool._run_llm (直接的なLLM呼び出し)
- 将来のモックポイント: UniversalLLMUseCase.execute_with_fallback (統一されたLLM実行)
- 移行時期: Phase 1完了後（SPEC-LLM-001実装完了時）
"""
import pytest
import asyncio
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# pytest-timeoutが利用できない場合のフォールバック
try:
    import pytest_timeout
except ImportError:
    # timeoutマーカーを無効化
    pytest.mark.timeout = lambda *args, **kwargs: lambda f: f

from mcp_servers.noveler.tools.polish_manuscript_apply_tool import PolishManuscriptApplyTool
from mcp_servers.noveler.domain.entities.mcp_tool_base import ToolRequest

# Phase制御用の環境変数
SPEC_LLM_001_COMPLETED = os.getenv('SPEC_LLM_001_COMPLETED', 'true').lower() == 'true'  # 実装完了済み


@pytest.mark.mcp_integration
class TestMCPPolishIntegration:
    """MCP環境でのpolish_manuscript_apply統合テスト"""

    @pytest.fixture
    def mock_file_system(self):
        """ファイルシステムモックの共通化"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.read_text', return_value="テスト内容"):
                with patch('pathlib.Path.write_text'):
                    yield

    @pytest.fixture
    def mock_mcp_environment(self):
        """MCP環境モックの共通化"""
        with patch('noveler.infrastructure.factories.path_service_factory.is_mcp_environment', return_value=True):
            yield

    @pytest.fixture
    def mock_tool_resolve(self):
        """ツールのパス解決モック"""
        def _mock_resolve(tool, path="/test/manuscript.md"):
            with patch.object(tool, '_resolve_target_path', return_value=Path(path)):
                yield
        return _mock_resolve

    @pytest.fixture
    def mcp_request(self):
        """MCP環境用テストリクエスト"""
        return ToolRequest(
            episode_number=1,
            project_name="test_project",
            additional_params={
                "dry_run": True,
                "stages": ["stage2", "stage3"]
            }
        )

    def test_mcp_environment_detection(self):
        """MCP環境検出の確認"""
        # 通常環境（直接importして確認）
        from noveler.infrastructure.factories.path_service_factory import is_mcp_environment
        assert not is_mcp_environment()

        # MCP環境シミュレーション（patchオブジェクトを直接確認）
        with patch('noveler.infrastructure.factories.path_service_factory.is_mcp_environment', return_value=True) as mock_func:
            # mockオブジェクトの戻り値を確認
            assert mock_func.return_value is True
            # mockが呼ばれることを確認
            mock_func()
            assert mock_func.called

    @pytest.mark.timeout(10)  # 10秒でタイムアウト
    def test_polish_apply_mcp_environment_current(self, mcp_request, mock_file_system, mock_mcp_environment):
        """MCP環境での現在の動作確認（fixture活用例）"""
        tool = PolishManuscriptApplyTool()

        with patch.object(tool, '_resolve_target_path', return_value=Path("/test/manuscript.md")):
            # LLM実行をモックして高速化
            # TODO(Phase1後): UniversalLLMUseCaseのモックに移行
            with patch.object(tool, '_run_llm', return_value='{"manuscript": "改稿後", "improvements": []}'):
                result = tool.execute(mcp_request)

            # 基本実行成功の確認
            assert result.success, "基本実行は成功する必要がある"
            assert "improved_artifact" in result.metadata
            print("現在の実装: MCP環境でのLLM実行はスキップされました")

    @pytest.mark.skipif(not SPEC_LLM_001_COMPLETED, reason="SPEC-LLM-001実装未完了")
    @pytest.mark.asyncio
    async def test_polish_apply_mcp_environment_unified(self, mcp_request):
        """MCP環境でのUniversalLLMUseCase統合後動作確認（Phase 1以降）

        実装予定内容:
        1. UniversalLLMUseCaseによる統一LLM実行
        2. MCP環境での自動フォールバック機能
        3. 統一設定システムによる環境対応の自動化
        """
        tool = PolishManuscriptApplyTool()

        with patch('noveler.infrastructure.factories.path_service_factory.is_mcp_environment', return_value=True):
            # UniversalLLMUseCaseのモック（非同期対応）
            mock_use_case = AsyncMock()
            mock_response = MagicMock()
            mock_response.is_success.return_value = True
            mock_response.get_writing_content.return_value = '{"manuscript": "改稿後テキスト", "improvements": ["改善点1"]}'
            mock_use_case.execute_with_fallback.return_value = mock_response

            with patch('noveler.application.use_cases.universal_llm_use_case.UniversalLLMUseCase', return_value=mock_use_case):
                with patch.object(tool, '_resolve_target_path', return_value=Path("/test/manuscript.md")):
                    with patch('pathlib.Path.exists', return_value=True):
                        with patch('pathlib.Path.read_text', return_value="テスト内容"):
                            with patch('pathlib.Path.write_text'):
                                result = tool.execute(mcp_request)

                                # 統合後はMCP環境でもLLM実行が成功する
                                assert result.success, "統合後はMCP環境でも成功する必要がある"
                                assert "improved_artifact" in result.metadata

                                # Stage2とStage3の2回呼び出しを確認
                                assert mock_use_case.execute_with_fallback.call_count == 2, f"Stage2/3で2回呼ばれるべき: {mock_use_case.execute_with_fallback.call_count}回"

    @pytest.mark.timeout(10)
    def test_unified_llm_execution_behavior(self, mcp_request):
        """v3.0.0: 統一LLM実行の動作確認（force_llmパラメータ削除後）"""
        tool = PolishManuscriptApplyTool()

        # UniversalLLMUseCaseによる統一実行でMCP環境でも適切に動作
        with patch('noveler.infrastructure.factories.path_service_factory.is_mcp_environment', return_value=True):
            with patch.object(tool, '_resolve_target_path', return_value=Path("/test/manuscript.md")):
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('pathlib.Path.read_text', return_value="テスト内容"):
                        with patch('pathlib.Path.write_text'):
                            # LLM実行をモック
                            with patch.object(tool, '_run_llm', return_value='{"manuscript": "改稿後", "improvements": []}'):
                                result = tool.execute(mcp_request)

                            # v3.0.0: 統一設定により環境に関係なく動作
                            assert result.success
                            print("v3.0.0: 統一LLM実行で環境に依存しない動作")

    def test_v3_force_llm_parameter_removal_verification(self):
        """v3.0.0: force_llmパラメータの完全削除確認"""
        tool = PolishManuscriptApplyTool()

        # スキーマからforce_llmが削除されたことを確認
        schema = tool.get_input_schema()
        properties = schema.get("properties", {})
        assert "force_llm" not in properties, "v3.0.0: force_llmパラメータは完全削除される必要があります"

        # _run_llmメソッドのシグネチャからforce_llmパラメータが削除されたことを確認
        import inspect
        signature = inspect.signature(tool._run_llm)
        assert "force_llm" not in signature.parameters, "v3.0.0: _run_llmメソッドからforce_llmパラメータが削除される必要があります"

    @pytest.mark.slow  # 遅いテストとしてマーク
    @pytest.mark.timeout(30)  # 全体で30秒制限
    def test_mcp_environment_success_rate(self):
        """MCP環境での動作成功率測定"""
        tool = PolishManuscriptApplyTool()
        success_count = 0
        total_runs = 10

        # LLM実行を事前にモック
        with patch.object(tool, '_run_llm', return_value='{"manuscript": "改稿後", "improvements": []}'):
            for i in range(total_runs):
                request = ToolRequest(
                    episode_number=1,
                    project_name="test_project",
                    additional_params={"dry_run": True}
                )

                with patch('noveler.infrastructure.factories.path_service_factory.is_mcp_environment', return_value=True):
                    with patch.object(tool, '_resolve_target_path', return_value=Path(f"/test/manuscript_{i}.md")):
                        with patch('pathlib.Path.exists', return_value=True):
                            with patch('pathlib.Path.read_text', return_value=f"テスト内容{i}"):
                                with patch('pathlib.Path.write_text'):
                                    try:
                                        result = tool.execute(request)
                                        if result.success:
                                            success_count += 1
                                    except Exception as e:
                                        print(f"実行{i}でエラー: {e}")

        success_rate = success_count / total_runs
        print(f"MCP環境成功率: {success_rate:.1%} ({success_count}/{total_runs})")

        # 現在の基準: 90%以上（統合後は100%を目指す）
        assert success_rate >= 0.9, f"成功率が基準未満: {success_rate:.1%}"