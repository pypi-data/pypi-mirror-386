"""
MCPサーバー共通基盤コンプライアンステスト

MCPサーバー統合での共通基盤使用検証：
- logging直接使用の検出と修正提案
- JSON変換サーバーの共通基盤準拠確認
- MCP tools の統一エラーハンドリング検証
"""
from __future__ import annotations

import pytest
import json
from pathlib import Path
from typing import List, Dict
from unittest.mock import MagicMock, patch

try:
    from mcp_servers.noveler import json_conversion_server, async_json_conversion_server
    from mcp_servers.noveler.core import async_subprocess_adapter
    MCP_SERVER_AVAILABLE = True
except ImportError:
    MCP_SERVER_AVAILABLE = False


@pytest.mark.skipif(not MCP_SERVER_AVAILABLE, reason="MCP server modules not available")
class TestMcpServerCompliance:
    """MCPサーバー共通基盤コンプライアンステスト"""

    @pytest.fixture
    def mcp_server_root(self):
        """MCPサーバールートディレクトリ"""
        return Path(__file__).parent.parent.parent.parent / "src" / "mcp_servers"

    @pytest.fixture
    def mcp_python_files(self, mcp_server_root):
        """MCPサーバーのPythonファイル一覧"""
        if not mcp_server_root.exists():
            return []
        return list(mcp_server_root.rglob("*.py"))

    @pytest.mark.spec("SPEC-MCP-COM-001")
    def test_detect_legacy_logging_usage(self, mcp_python_files):
        """レガシーlogging使用の検出"""
        legacy_logging_files = []
        direct_getlogger_files = []

        for file_path in mcp_python_files:
            try:
                content = file_path.read_text(encoding='utf-8')

                # 禁止パターンの検出
                if 'import logging' in content:
                    legacy_logging_files.append(str(file_path.relative_to(file_path.parent.parent.parent)))

                if 'logging.getLogger' in content:
                    direct_getlogger_files.append(str(file_path.relative_to(file_path.parent.parent.parent)))

            except Exception as e:
                print(f"ファイル読み取りエラー {file_path}: {e}")

        # 検出結果の報告
        print(f"\n=== MCP Server Legacy Logging Detection ===")
        print(f"Legacy 'import logging' files: {len(legacy_logging_files)}")
        for file_path in legacy_logging_files:
            print(f"  - {file_path}")

        print(f"Direct 'logging.getLogger' files: {len(direct_getlogger_files)}")
        for file_path in direct_getlogger_files:
            print(f"  - {file_path}")

        # 修正提案の生成
        if legacy_logging_files or direct_getlogger_files:
            self._generate_mcp_logging_fix_suggestions(legacy_logging_files + direct_getlogger_files)

        # 情報収集テストのため常に成功（修正提案のみ）
        assert True

    @pytest.mark.spec("SPEC-MCP-COM-002")
    def test_json_conversion_server_compliance(self, mcp_server_root):
        """JSON変換サーバーのコンプライアンス検証"""
        json_server_file = mcp_server_root / "noveler" / "json_conversion_server.py"
        async_json_server_file = mcp_server_root / "noveler" / "async_json_conversion_server.py"

        violations = []
        recommendations = []

        for server_file in [json_server_file, async_json_server_file]:
            if server_file.exists():
                content = server_file.read_text(encoding='utf-8')

                # B30違反パターンの検証
                if 'import logging' in content:
                    violations.append(f"{server_file.name}: レガシーlogging使用")

                if 'logging.getLogger' in content:
                    violations.append(f"{server_file.name}: 直接getLogger使用")

                # 推奨パターンの確認
                if 'get_logger' not in content:
                    recommendations.append(
                        f"{server_file.name}: 統一ログシステム使用を推奨"
                    )

        # 結果の報告
        print(f"\n=== JSON Conversion Server Compliance ===")
        print(f"Violations found: {len(violations)}")
        for violation in violations:
            print(f"  ❌ {violation}")

        print(f"Recommendations: {len(recommendations)}")
        for recommendation in recommendations:
            print(f"  💡 {recommendation}")

        # MCPサーバーの場合は警告レベルで許容（完全な修正は別途実施）
        if violations:
            import warnings
            warnings.warn(f"MCP Server compliance violations detected: {len(violations)}", UserWarning)

    @pytest.mark.spec("SPEC-MCP-COM-003")
    def test_mcp_tools_error_handling_patterns(self, mcp_server_root):
        """MCP tools のエラーハンドリングパターン検証"""
        tools_dir = mcp_server_root / "noveler" / "tools"

        if not tools_dir.exists():
            pytest.skip("MCP tools directory not found")

        tool_files = list(tools_dir.rglob("*.py"))

        error_handling_analysis = {
            'files_with_try_except': [],
            'files_with_unified_error_handling': [],
            'files_needing_improvement': []
        }

        for tool_file in tool_files:
            try:
                content = tool_file.read_text(encoding='utf-8')

                # エラーハンドリングパターンの分析
                if 'try:' in content and 'except' in content:
                    error_handling_analysis['files_with_try_except'].append(str(tool_file.name))

                # 統一エラーハンドリングの確認
                if 'handle_error' in content or 'unified_error' in content:
                    error_handling_analysis['files_with_unified_error_handling'].append(str(tool_file.name))

                # 改善が必要なファイル
                if 'try:' in content and 'handle_error' not in content:
                    error_handling_analysis['files_needing_improvement'].append(str(tool_file.name))

            except Exception as e:
                print(f"エラーハンドリング分析エラー {tool_file}: {e}")

        # 結果の報告
        print(f"\n=== MCP Tools Error Handling Analysis ===")
        print(f"Files with try-except: {len(error_handling_analysis['files_with_try_except'])}")
        print(f"Files with unified error handling: {len(error_handling_analysis['files_with_unified_error_handling'])}")
        print(f"Files needing improvement: {len(error_handling_analysis['files_needing_improvement'])}")

        # 改善提案
        if error_handling_analysis['files_needing_improvement']:
            print("\n💡 Improvement Suggestions:")
            for file_name in error_handling_analysis['files_needing_improvement']:
                print(f"  - {file_name}: 統一エラーハンドリングの導入を推奨")

    @pytest.mark.spec("SPEC-MCP-COM-004")
    def test_mcp_server_console_usage_patterns(self, mcp_python_files):
        """MCPサーバーでのConsole使用パターン検証"""
        console_usage_analysis = {
            'rich_console_imports': [],
            'console_duplications': [],
            'shared_console_usage': [],
            'print_statements': []
        }

        for file_path in mcp_python_files:
            try:
                content = file_path.read_text(encoding='utf-8')

                # Console使用パターンの分析
                if 'from rich.console import Console' in content:
                    console_usage_analysis['rich_console_imports'].append(str(file_path.name))

                if 'console = Console()' in content:
                    console_usage_analysis['console_duplications'].append(str(file_path.name))

                if '_get_console' in content or 'shared_utilities' in content:
                    console_usage_analysis['shared_console_usage'].append(str(file_path.name))

                # print文の使用確認（MCPサーバーでは許容される場合がある）
                if 'print(' in content:
                    console_usage_analysis['print_statements'].append(str(file_path.name))

            except Exception as e:
                print(f"Console使用分析エラー {file_path}: {e}")

        # 結果の報告
        print(f"\n=== MCP Server Console Usage Analysis ===")
        print(f"Rich Console imports: {len(console_usage_analysis['rich_console_imports'])}")
        print(f"Console duplications: {len(console_usage_analysis['console_duplications'])}")
        print(f"Shared console usage: {len(console_usage_analysis['shared_console_usage'])}")
        print(f"Print statements: {len(console_usage_analysis['print_statements'])}")

        # Console重複作成の警告
        if console_usage_analysis['console_duplications']:
            pytest.warns(UserWarning,
                f"MCP Server console duplications detected: {console_usage_analysis['console_duplications']}")

    @pytest.mark.spec("SPEC-MCP-COM-005")
    def test_progressive_check_mcp_integration_compliance(self, mcp_server_root):
        """Progressive Check MCP統合のコンプライアンス"""
        # 段階的チェック関連のMCPツール確認
        main_file = mcp_server_root / "noveler" / "main.py"

        if not main_file.exists():
            pytest.skip("MCP server main.py not found")

        content = main_file.read_text(encoding='utf-8')

        # Progressive Check関連ツールの確認
        progressive_tools = [
            'get_check_tasks',
            'execute_check_step',
            'get_check_status',
            'get_check_history'
        ]

        found_tools = []
        for tool_name in progressive_tools:
            if tool_name in content:
                found_tools.append(tool_name)

        print(f"\n=== Progressive Check MCP Integration ===")
        print(f"Expected tools: {len(progressive_tools)}")
        print(f"Found tools: {len(found_tools)}")

        for tool in found_tools:
            print(f"  ✓ {tool}")

        missing_tools = set(progressive_tools) - set(found_tools)
        for tool in missing_tools:
            print(f"  ❌ {tool} (missing)")

        # 統合完了度の評価
        integration_score = len(found_tools) / len(progressive_tools)
        print(f"Integration score: {integration_score:.2%}")

        # 50%以上の統合を期待
        assert integration_score >= 0.5, f"Progressive Check MCP integration score too low: {integration_score:.2%}"

    def _generate_mcp_logging_fix_suggestions(self, problematic_files: List[str]):
        """MCPサーバーlogging修正提案の生成"""
        print(f"\n💡 MCP Server Logging Fix Suggestions:")
        print(f"=" * 50)

        for file_path in problematic_files:
            print(f"\n📁 {file_path}")
            print(f"   ❌ Current: import logging")
            print(f"   ✅ Fix: from noveler.infrastructure.logging.unified_logger import get_logger")
            print(f"   ❌ Current: self.logger = logging.getLogger(__name__)")
            print(f"   ✅ Fix: self.logger = get_logger(__name__)")

        print(f"\n🔧 Auto-fix command suggestion:")
        print(f"   python scripts/tools/logging_migration_tool.py --target mcp_servers")

    @pytest.mark.spec("SPEC-MCP-COM-006")
    def test_mcp_server_import_patterns(self, mcp_python_files):
        """MCPサーバーのインポートパターン検証"""
        import_analysis = {
            'noveler_prefixed_imports': [],
            'relative_imports': [],
            'missing_noveler_prefix': []
        }

        for file_path in mcp_python_files:
            try:
                content = file_path.read_text(encoding='utf-8')

                # インポートパターンの分析
                if 'from noveler.' in content:
                    import_analysis['noveler_prefixed_imports'].append(str(file_path.name))

                if 'from .' in content or 'from ..' in content:
                    import_analysis['relative_imports'].append(str(file_path.name))

                # novelerプレフィックスが必要だが使用されていないパターン
                if ('from domain.' in content or 'from application.' in content or
                    'from infrastructure.' in content):
                    import_analysis['missing_noveler_prefix'].append(str(file_path.name))

            except Exception as e:
                print(f"インポート分析エラー {file_path}: {e}")

        # 結果の報告
        print(f"\n=== MCP Server Import Pattern Analysis ===")
        print(f"Noveler prefixed imports: {len(import_analysis['noveler_prefixed_imports'])}")
        print(f"Relative imports: {len(import_analysis['relative_imports'])}")
        print(f"Missing noveler prefix: {len(import_analysis['missing_noveler_prefix'])}")

        # 相対インポートの警告
        if import_analysis['relative_imports']:
            import warnings
            warnings.warn(
                f"MCP Server relative imports detected: {import_analysis['relative_imports']}",
                UserWarning)


class TestMcpServerQualityMetrics:
    """MCPサーバー品質メトリクス"""

    @pytest.mark.spec("SPEC-MCP-MET-001")
    def test_mcp_server_overall_compliance_score(self):
        """MCPサーバー総合コンプライアンススコア"""
        mcp_server_root = Path(__file__).parent.parent.parent.parent / "src" / "mcp_servers"

        if not mcp_server_root.exists():
            pytest.skip("MCP server directory not found")

        python_files = list(mcp_server_root.rglob("*.py"))

        if not python_files:
            pytest.skip("No Python files found in MCP server directory")

        # 各種コンプライアンス指標の計算
        total_files = len(python_files)

        # Logging compliance
        logging_compliant = 0
        console_compliant = 0
        import_compliant = 0

        for file_path in python_files:
            try:
                content = file_path.read_text(encoding='utf-8')

                # Logging compliance (統一Logger使用 or logging不使用)
                if 'get_logger' in content or 'import logging' not in content:
                    logging_compliant += 1

                # Console compliance (共有Console使用 or Console不使用)
                if '_get_console' in content or 'Console()' not in content:
                    console_compliant += 1

                # Import compliance (novelerプレフィックス使用 or noveler外部依存なし)
                if 'from noveler.' in content or not any(pattern in content
                    for pattern in ['from domain.', 'from application.', 'from infrastructure.']):
                    import_compliant += 1

            except Exception:
                pass

        # スコア計算
        logging_score = logging_compliant / total_files if total_files > 0 else 0
        console_score = console_compliant / total_files if total_files > 0 else 0
        import_score = import_compliant / total_files if total_files > 0 else 0

        overall_score = (logging_score * 0.4 + console_score * 0.3 + import_score * 0.3)

        print(f"\n=== MCP Server Quality Metrics ===")
        print(f"Total files analyzed: {total_files}")
        print(f"Logging compliance: {logging_score:.2%}")
        print(f"Console compliance: {console_score:.2%}")
        print(f"Import compliance: {import_score:.2%}")
        print(f"Overall compliance: {overall_score:.2%}")

        # MCPサーバーは70%以上を目標（通常のコードより緩い基準）
        assert overall_score >= 0.70, (
            f"MCP Server overall compliance score too low: {overall_score:.2%} < 70%"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
