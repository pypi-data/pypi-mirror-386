"""
CODEMAP連携静的解析違反検出テスト

ASTベースの高精度違反検出（CODEMAP基準）：
- import文の詳細解析（CODEMAP禁止パターン基準）
- ハードコーディング検出（CODEMAP基準）
- 関数呼び出しパターン解析
- 自動修正提案生成（CODEMAP推奨パターン基準）

Version: 2.0.0 - CODEMAP連携対応
"""
from __future__ import annotations

import ast
import pytest
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass

# CODEMAP読み取りユーティリティをインポート
sys.path.insert(0, str(Path(__file__).parents[3] / "src"))
from noveler.tools.codemap_reader import create_codemap_reader
from noveler.infrastructure.logging.unified_logger import get_logger


@dataclass
class ViolationReport:
    """違反レポート"""
    file_path: str
    line_number: int
    violation_type: str
    severity: str
    current_code: str
    suggested_fix: str
    context: str = ""


class ASTBasedComplianceAnalyzer:
    """ASTベース共通基盤コンプライアンス解析器"""

    def __init__(self):
        self.logger = get_logger(__name__)

        # 禁止パターン
        self.forbidden_imports = {
            'logging': 'import logging',
            'rich.console.Console': 'from rich.console import Console'
        }

        # 禁止関数呼び出し
        self.forbidden_calls = {
            'logging.getLogger',
            'Console',
            'print'  # 文脈により判定
        }

        # ハードコーディングパターン
        self.hardcoded_patterns = {
            '"40_原稿"',
            '"30_プロット"',
            '"20_設定"',
            '"10_企画"'
        }

        # 推奨パターン
        self.recommended_imports = {
            'noveler.infrastructure.logging.unified_logger': 'get_logger',
            'noveler.presentation.shared.shared_utilities': '_get_console',
            'noveler.infrastructure.factories.path_service_factory': 'create_path_service'
        }

    def analyze_file(self, file_path: Path) -> List[ViolationReport]:
        """ファイルの静的解析実行"""
        violations = []

        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)

            # 各種解析の実行
            violations.extend(self._analyze_imports(tree, file_path, content))
            violations.extend(self._analyze_function_calls(tree, file_path, content))
            violations.extend(self._analyze_string_literals(tree, file_path, content))
            violations.extend(self._analyze_assignments(tree, file_path, content))

        except Exception as e:
            self.logger.error(f"AST解析エラー {file_path}: {e}")

        return violations

    def _analyze_imports(self, tree: ast.AST, file_path: Path, content: str) -> List[ViolationReport]:
        """インポート文の解析"""
        violations = []
        lines = content.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # 禁止インポートの検出
                    if alias.name in self.forbidden_imports:
                        violations.append(ViolationReport(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            violation_type="forbidden_import",
                            severity="critical",
                            current_code=f"import {alias.name}",
                            suggested_fix="from noveler.infrastructure.logging.unified_logger import get_logger",
                            context=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                        ))

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    full_import = f"{node.module}.{node.names[0].name if node.names else ''}"

                    # 禁止インポートの検出
                    if full_import in self.forbidden_imports:
                        violations.append(ViolationReport(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            violation_type="forbidden_from_import",
                            severity="critical",
                            current_code=f"from {node.module} import {', '.join(n.name for n in node.names)}",
                            suggested_fix=self._get_recommended_import_fix(node.module, node.names),
                            context=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                        ))

                    # 相対インポートの検出
                    if node.module.startswith('.'):
                        violations.append(ViolationReport(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            violation_type="relative_import",
                            severity="high",
                            current_code=f"from {node.module} import {', '.join(n.name for n in node.names)}",
                            suggested_fix=self._convert_relative_to_absolute_import(node.module, node.names),
                            context=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                        ))

        return violations

    def _analyze_function_calls(self, tree: ast.AST, file_path: Path, content: str) -> List[ViolationReport]:
        """関数呼び出しの解析"""
        violations = []
        lines = content.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # 関数名の取得
                func_name = self._get_function_name(node.func)

                if func_name in self.forbidden_calls:
                    # Console()直接作成の検出
                    if func_name == 'Console':
                        violations.append(ViolationReport(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            violation_type="console_duplication",
                            severity="critical",
                            current_code="Console()",
                            suggested_fix="from noveler.presentation.shared.shared_utilities import _get_console; console = _get_console()",
                            context=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                        ))

                    # logging.getLogger使用の検出
                    elif func_name == 'logging.getLogger':
                        violations.append(ViolationReport(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            violation_type="legacy_getlogger",
                            severity="critical",
                            current_code="logging.getLogger(__name__)",
                            suggested_fix="get_logger(__name__)",
                            context=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                        ))

                    # print文の検出（文脈により判定）
                    elif func_name == 'print':
                        # MCPサーバー以外でのprint使用は推奨されない
                        if 'mcp_servers' not in str(file_path):
                            violations.append(ViolationReport(
                                file_path=str(file_path),
                                line_number=node.lineno,
                                violation_type="print_usage",
                                severity="medium",
                                current_code=f"print({self._get_print_args(node)})",
                                suggested_fix="console.print(...) # 共通Consoleを使用",
                                context=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                            ))

        return violations

    def _analyze_string_literals(self, tree: ast.AST, file_path: Path, content: str) -> List[ViolationReport]:
        """文字列リテラルの解析（ハードコーディング検出）"""
        violations = []
        lines = content.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, ast.Str):
                # Python 3.8以降
                string_value = f'"{node.s}"'
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                # Python 3.8以降
                string_value = f'"{node.value}"'
            else:
                continue

            # ハードコーディングパターンの検出
            if string_value in self.hardcoded_patterns:
                violations.append(ViolationReport(
                    file_path=str(file_path),
                    line_number=node.lineno,
                    violation_type="hardcoded_path",
                    severity="critical",
                    current_code=string_value,
                    suggested_fix=self._get_path_service_fix(string_value),
                    context=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                ))

        return violations

    def _analyze_assignments(self, tree: ast.AST, file_path: Path, content: str) -> List[ViolationReport]:
        """代入文の解析"""
        violations = []
        lines = content.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # console = Console() パターンの検出
                if (len(node.targets) == 1 and
                    isinstance(node.targets[0], ast.Name) and
                    node.targets[0].id == 'console' and
                    isinstance(node.value, ast.Call)):

                    func_name = self._get_function_name(node.value.func)
                    if func_name == 'Console':
                        violations.append(ViolationReport(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            violation_type="console_assignment_duplication",
                            severity="critical",
                            current_code="console = Console()",
                            suggested_fix="console = _get_console()  # 共通Consoleを使用",
                            context=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                        ))

                # logger = logging.getLogger() パターンの検出
                elif (len(node.targets) == 1 and
                      isinstance(node.targets[0], ast.Name) and
                      node.targets[0].id == 'logger' and
                      isinstance(node.value, ast.Call)):

                    func_name = self._get_function_name(node.value.func)
                    if func_name == 'logging.getLogger':
                        violations.append(ViolationReport(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            violation_type="logger_assignment_legacy",
                            severity="critical",
                            current_code="logger = logging.getLogger(__name__)",
                            suggested_fix="logger = get_logger(__name__)",
                            context=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                        ))

        return violations

    def _get_function_name(self, func_node: ast.AST) -> str:
        """関数名の取得"""
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            if isinstance(func_node.value, ast.Name):
                return f"{func_node.value.id}.{func_node.attr}"
            else:
                return func_node.attr
        return ""

    def _get_print_args(self, call_node: ast.Call) -> str:
        """print関数の引数取得（簡易版）"""
        if call_node.args:
            return "..."
        return ""

    def _get_recommended_import_fix(self, module: str, names: List[ast.alias]) -> str:
        """推奨インポート修正の取得"""
        if module == "rich.console" and any(n.name == "Console" for n in names):
            return "from noveler.presentation.shared.shared_utilities import _get_console"
        elif module == "logging":
            return "from noveler.infrastructure.logging.unified_logger import get_logger"
        else:
            return f"# TODO: {module} の適切な代替を検討"

    def _convert_relative_to_absolute_import(self, module: str, names: List[ast.alias]) -> str:
        """相対インポートの絶対インポート変換"""
        if module.startswith('..'):
            return f"from noveler.{module[2:]} import {', '.join(n.name for n in names)}"
        elif module.startswith('.'):
            return f"from noveler{module[1:]} import {', '.join(n.name for n in names)}"
        return f"# TODO: {module} の絶対インポート変換"

    def _get_path_service_fix(self, hardcoded_path: str) -> str:
        """PathService修正提案の取得"""
        path_mapping = {
            '"40_原稿"': "path_service.get_manuscript_dir()",
            '"30_プロット"': "path_service.get_plot_dir()",
            '"20_設定"': "path_service.get_settings_dir()",
            '"10_企画"': "path_service.get_planning_dir()"
        }
        return path_mapping.get(hardcoded_path, f"# TODO: {hardcoded_path} の PathService対応")


class TestStaticAnalysisCompliance:
    """静的解析による共通基盤コンプライアンステスト"""

    @pytest.fixture
    def analyzer(self):
        """静的解析器のフィクスチャ"""
        return ASTBasedComplianceAnalyzer()

    @pytest.fixture
    def project_root(self):
        """プロジェクトルートパス"""
        return Path(__file__).parent.parent.parent.parent

    @pytest.fixture
    def target_files(self, project_root):
        """解析対象ファイルの取得"""
        target_dirs = [
            project_root / "src" / "noveler",
            project_root / "src" / "scripts"
        ]

        python_files = []
        for target_dir in target_dirs:
            if target_dir.exists():
                python_files.extend(target_dir.rglob("*.py"))

        return python_files

    @pytest.mark.spec("SPEC-STA-COM-001")
    def test_ast_based_import_violation_detection(self, analyzer, target_files):
        """ASTベースインポート違反検出"""
        all_violations = []

        for file_path in target_files[:10]:  # 最初の10ファイルをサンプル解析
            violations = analyzer.analyze_file(file_path)
            import_violations = [v for v in violations if 'import' in v.violation_type]
            all_violations.extend(import_violations)

        # 違反レポートの生成
        print(f"\n=== AST-Based Import Violation Detection ===")
        print(f"Total import violations: {len(all_violations)}")

        critical_violations = [v for v in all_violations if v.severity == "critical"]
        high_violations = [v for v in all_violations if v.severity == "high"]

        print(f"Critical violations: {len(critical_violations)}")
        print(f"High priority violations: {len(high_violations)}")

        # サンプル違反の詳細表示
        for i, violation in enumerate(critical_violations[:3]):
            print(f"\n📁 Violation {i+1}:")
            print(f"   File: {Path(violation.file_path).name}")
            print(f"   Line: {violation.line_number}")
            print(f"   Type: {violation.violation_type}")
            print(f"   Current: {violation.current_code}")
            print(f"   Fix: {violation.suggested_fix}")

    @pytest.mark.spec("SPEC-STA-COM-002")
    def test_ast_based_console_duplication_detection(self, analyzer, target_files):
        """ASTベースConsole重複検出"""
        console_violations = []

        for file_path in target_files[:20]:
            violations = analyzer.analyze_file(file_path)
            console_specific = [v for v in violations if 'console' in v.violation_type]
            console_violations.extend(console_specific)

        print(f"\n=== AST-Based Console Duplication Detection ===")
        print(f"Console violations: {len(console_violations)}")

        # 重複作成の完全禁止（B30基準）
        critical_console_violations = [v for v in console_violations if v.severity == "critical"]

        if critical_console_violations:
            print(f"❌ Critical console violations found: {len(critical_console_violations)}")
            for violation in critical_console_violations[:2]:
                print(f"   - {Path(violation.file_path).name}:{violation.line_number}")
                print(f"     Current: {violation.current_code}")
                print(f"     Fix: {violation.suggested_fix}")
        else:
            print(f"✅ No critical console violations detected")

        # クリティカル違反は0件であることを確認
        assert len(critical_console_violations) == 0, (
            f"Console重複作成が検出されました: {len(critical_console_violations)}件"
        )

    @pytest.mark.spec("SPEC-STA-COM-003")
    def test_ast_based_hardcoding_detection(self, analyzer, target_files):
        """ASTベースハードコーディング検出"""
        hardcoding_violations = []

        for file_path in target_files[:15]:
            violations = analyzer.analyze_file(file_path)
            hardcoding_specific = [v for v in violations if v.violation_type == "hardcoded_path"]
            hardcoding_violations.extend(hardcoding_specific)

        print(f"\n=== AST-Based Hardcoding Detection ===")
        print(f"Hardcoding violations: {len(hardcoding_violations)}")

        # ハードコーディング詳細の表示
        for i, violation in enumerate(hardcoding_violations):
            print(f"\n📁 Hardcoding {i+1}:")
            print(f"   File: {Path(violation.file_path).name}")
            print(f"   Line: {violation.line_number}")
            print(f"   Hardcoded: {violation.current_code}")
            print(f"   PathService fix: {violation.suggested_fix}")

        # パスハードコーディング禁止（B30基準）
        assert len(hardcoding_violations) == 0, (
            f"パスハードコーディングが検出されました: {len(hardcoding_violations)}件"
        )

    @pytest.mark.spec("SPEC-STA-COM-004")
    def test_progressive_check_manager_ast_compliance(self, analyzer, project_root):
        """ProgressiveCheckManager AST完全コンプライアンス"""
        pcm_file = project_root / "src" / "scripts" / "domain" / "services" / "progressive_check_manager.py"

        if not pcm_file.exists():
            pytest.skip("ProgressiveCheckManager file not found")

        violations = analyzer.analyze_file(pcm_file)

        print(f"\n=== ProgressiveCheckManager AST Compliance ===")
        print(f"Total violations: {len(violations)}")

        # 各種違反の分類
        violation_by_type = {}
        for violation in violations:
            violation_type = violation.violation_type
            if violation_type not in violation_by_type:
                violation_by_type[violation_type] = []
            violation_by_type[violation_type].append(violation)

        # 違反タイプ別の報告
        for vtype, vlist in violation_by_type.items():
            print(f"  {vtype}: {len(vlist)} violations")
            for v in vlist[:2]:  # 最大2件表示
                print(f"    - Line {v.line_number}: {v.current_code}")

        # ProgressiveCheckManagerは100%コンプライアンスを期待
        critical_violations = [v for v in violations if v.severity == "critical"]
        assert len(critical_violations) == 0, (
            f"ProgressiveCheckManager AST critical violations: {len(critical_violations)}"
        )

    @pytest.mark.spec("SPEC-STA-COM-005")
    def test_generate_auto_fix_suggestions(self, analyzer, target_files):
        """自動修正提案生成テスト"""
        fix_suggestions = {}

        for file_path in target_files[:5]:  # サンプル解析
            violations = analyzer.analyze_file(file_path)

            if violations:
                file_fixes = []
                for violation in violations:
                    file_fixes.append({
                        'line': violation.line_number,
                        'type': violation.violation_type,
                        'current': violation.current_code,
                        'fix': violation.suggested_fix,
                        'severity': violation.severity
                    })
                fix_suggestions[str(file_path)] = file_fixes

        print(f"\n=== Auto-Fix Suggestions Generation ===")
        print(f"Files with fixable violations: {len(fix_suggestions)}")

        # 修正提案の詳細表示
        for file_path, fixes in list(fix_suggestions.items())[:2]:
            print(f"\n📁 {Path(file_path).name}")
            for fix in fixes[:3]:  # 最大3件表示
                print(f"   Line {fix['line']} ({fix['severity']})")
                print(f"   Current: {fix['current']}")
                print(f"   Fix: {fix['fix']}")

        # 自動修正可能率の計算
        total_fixes = sum(len(fixes) for fixes in fix_suggestions.values())
        auto_fixable = sum(
            1 for fixes in fix_suggestions.values()
            for fix in fixes
            if fix['fix'] and not fix['fix'].startswith('# TODO')
        )

        auto_fix_rate = auto_fixable / total_fixes if total_fixes > 0 else 1.0
        print(f"\nAuto-fixable rate: {auto_fix_rate:.2%}")

        # 50%以上が自動修正可能であることを期待
        assert auto_fix_rate >= 0.5, f"Auto-fix rate too low: {auto_fix_rate:.2%}"

    @pytest.mark.spec("SPEC-STA-COM-006")
    def test_compliance_trend_analysis(self, analyzer, target_files):
        """コンプライアンス傾向分析"""
        analysis_results = {
            'total_files': len(target_files),
            'analyzed_files': 0,
            'compliant_files': 0,
            'violation_distribution': {},
            'severity_distribution': {'critical': 0, 'high': 0, 'medium': 0}
        }

        # サンプル解析実行
        for file_path in target_files[:25]:
            analysis_results['analyzed_files'] += 1
            violations = analyzer.analyze_file(file_path)

            if not violations:
                analysis_results['compliant_files'] += 1

            # 違反分布の集計
            for violation in violations:
                vtype = violation.violation_type
                analysis_results['violation_distribution'][vtype] = \
                    analysis_results['violation_distribution'].get(vtype, 0) + 1

                analysis_results['severity_distribution'][violation.severity] += 1

        print(f"\n=== Compliance Trend Analysis ===")
        print(f"Total files: {analysis_results['total_files']}")
        print(f"Analyzed files: {analysis_results['analyzed_files']}")
        print(f"Compliant files: {analysis_results['compliant_files']}")

        compliance_rate = analysis_results['compliant_files'] / analysis_results['analyzed_files']
        print(f"Compliance rate: {compliance_rate:.2%}")

        print(f"\nViolation distribution:")
        for vtype, count in analysis_results['violation_distribution'].items():
            print(f"  {vtype}: {count}")

        print(f"\nSeverity distribution:")
        for severity, count in analysis_results['severity_distribution'].items():
            print(f"  {severity}: {count}")

        # 全体コンプライアンス率70%以上を期待
        assert compliance_rate >= 0.70, f"Overall compliance rate too low: {compliance_rate:.2%}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
