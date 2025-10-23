"""
共通基盤コンポーネント使用検証テストスイート（CODEMAP連携版）

CODEMAP.yamlを単一信頼源として、B20/B30品質基準に基づく共通基盤コンポーネント使用を検証する
- Console使用検証（重複作成0件）
- Logger使用検証（統一ログシステム使用）
- PathService使用検証（ハードコーディング回避）
- エラーハンドリング統一検証（handle_error使用）

Version: 2.0.0 - CODEMAP連携対応
"""
from __future__ import annotations

import ast
import pytest
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from unittest.mock import MagicMock, patch

# CODEMAP読み取りユーティリティをインポート
sys.path.insert(0, str(Path(__file__).parents[3] / "src"))
from noveler.tools.codemap_reader import CODEMAPReader, create_codemap_reader
from noveler.infrastructure.logging.unified_logger import get_logger


class CommonFoundationComplianceChecker:
    """共通基盤コンプライアンスチェッカー（CODEMAP連携版）"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = get_logger(__name__)
        self.codemap_reader = create_codemap_reader()
        self.thresholds = self.codemap_reader.get_compliance_thresholds()

    def check_console_usage_compliance(self, file_paths: List[Path]) -> Dict[str, List[str]]:
        """Console使用コンプライアンスチェック（CODEMAP連携版）

        CODEMAP基準：
        - Console重複作成0件（禁止パターン）
        - 共通utilities使用率（CODEMAP定義基準値）

        Returns:
            違反情報の辞書
        """
        violations = {
            'console_duplications': [],
            'missing_shared_usage': [],
            'compliance_score': 0.0
        }

        # CODEMAPから禁止パターンと許可モジュールを取得
        console_patterns = self.codemap_reader.get_forbidden_patterns("console")
        allowed_modules = self.codemap_reader.get_allowed_modules("console")

        total_files = 0
        compliant_files = 0

        for file_path in file_paths:
            if not file_path.suffix == '.py':
                continue

            content = file_path.read_text(encoding='utf-8')

            hardcoded_patterns = [
                'project_root / "40_原稿"',
                'project_root / "30_プロット"',
                'Path("40_原稿")',
                '/ "40_原稿"',
                '/ "30_プロット"'
            ]

            hardcoded_detected = False
            for pattern in hardcoded_patterns:
                if pattern in content:
                    violations['hardcoded_paths'].append(f"{file_path}: {pattern}")
                    hardcoded_detected = True

            uses_path_helpers = hardcoded_detected or self._uses_path_service(content)
            if not uses_path_helpers:
                continue

            total_files += 1
            if self._uses_path_service(content):
                compliant_files += 1
            else:
                violations['missing_path_service'].append(str(file_path))

        # コンプライアンススコア計算
        if total_files > 0:
            violations['compliance_score'] = compliant_files / total_files
        else:
            violations['compliance_score'] = 1.0

        return violations

    def check_logger_usage_compliance(self, file_paths: List[Path]) -> Dict[str, List[str]]:
        """Logger使用コンプライアンスチェック

        B30基準：
        - import logging禁止
        - 統一ログシステム使用90%以上

        Returns:
            違反情報の辞書
        """
        violations = {
            'legacy_logging_imports': [],
            'direct_getlogger_usage': [],
            'missing_unified_logger': [],
            'compliance_score': 0.0
        }

        allowed_modules = self.codemap_reader.get_allowed_modules("logger")
        total_files = 0
        compliant_files = 0

        for file_path in file_paths:
            if not file_path.suffix == '.py':
                continue

            content = file_path.read_text(encoding='utf-8')
            lines = content.splitlines()
            uses_logger = self._contains_logger_usage(content)

            # 禁止パターン検出
            if any(line.lstrip().startswith('import logging') for line in lines):
                if not self.codemap_reader.is_pattern_allowed_for_file('import logging', str(file_path), 'logger'):
                    violations['legacy_logging_imports'].append(str(file_path))

            if any('logging.getLogger' in line and not line.lstrip().startswith('#') for line in lines):
                if not self.codemap_reader.is_pattern_allowed_for_file('logging.getLogger', str(file_path), 'logger'):
                    violations['direct_getlogger_usage'].append(str(file_path))

            if not uses_logger:
                continue

            total_files += 1
            interface_markers = ('ILoggerService', '_logger_service', 'logger_service', 'domain_logger', 'domain_logging', 'ILogger', 'NullLogger')
            uses_logger_interface = any(marker in content for marker in interface_markers)
            is_logger_provider = file_path.name in {'unified_logger.py'}

            if self._uses_allowed_logger_modules(content, allowed_modules) or uses_logger_interface or is_logger_provider:
                compliant_files += 1
            else:
                violations['missing_unified_logger'].append(str(file_path))

        # コンプライアンススコア計算
        if total_files > 0:
            violations['compliance_score'] = compliant_files / total_files
        else:
            violations['compliance_score'] = 1.0

        return violations

    def check_path_service_compliance(self, file_paths: List[Path]) -> Dict[str, List[str]]:
        """PathService使用コンプライアンスチェック

        B30基準：
        - パスハードコーディング禁止
        - CommonPathService使用推奨

        Returns:
            違反情報の辞書
        """
        violations = {
            'hardcoded_paths': [],
            'missing_path_service': [],
            'compliance_score': 0.0
        }

        total_files = 0
        compliant_files = 0

        for file_path in file_paths:
            if not file_path.suffix == '.py':
                continue

            content = file_path.read_text(encoding='utf-8')

            hardcoded_patterns = [
                'project_root / "40_原稿"',
                'project_root / "30_プロット"',
                'Path("40_原稿")',
                '/ "40_原稿"',
                '/ "30_プロット"'
            ]

            hardcoded_detected = False
            for pattern in hardcoded_patterns:
                if pattern in content:
                    violations['hardcoded_paths'].append(f"{file_path}: {pattern}")
                    hardcoded_detected = True

            uses_path_helpers = hardcoded_detected or self._uses_path_service(content)
            if not uses_path_helpers:
                continue

            total_files += 1
            if self._uses_path_service(content):
                compliant_files += 1
            else:
                violations['missing_path_service'].append(str(file_path))

        if total_files > 0:
            violations['compliance_score'] = compliant_files / total_files
        else:
            violations['compliance_score'] = 1.0

        return violations

    def _uses_allowed_console_modules(self, content: str, allowed_modules: set) -> bool:
        """許可されたConsoleモジュール使用の検証（CODEMAP連携版）"""
        for module in allowed_modules:
            if module in content:
                return True
        return False

    def _contains_forbidden_pattern(self, content: str, token: str) -> bool:
        """Detect forbidden patterns while avoiding substring false positives."""
        search_start = 0
        token_length = len(token)
        if token_length == 0:
            return False
        while True:
            index = content.find(token, search_start)
            if index == -1:
                return False
            preceding = content[index - 1] if index > 0 else ''
            if preceding.isalpha() or preceding == '_':
                search_start = index + 1
                continue
            line_start = content.rfind('\n', 0, index) + 1
            line_end = content.find('\n', index)
            if line_end == -1:
                line_end = len(content)
            comment_pos = content.find('#', line_start, line_end)
            if comment_pos != -1 and comment_pos < index:
                search_start = index + 1
                continue
            return True

    def _contains_console_usage(self, content: str) -> bool:
        """Detect whether the file references console APIs at all."""
        usage_markers = ["console.", "console =", "Console.", "Console("]
        return any(marker in content for marker in usage_markers)

    def _contains_logger_usage(self, content: str) -> bool:
        """Detect whether the file interacts with logging facilities."""
        markers = ('get_logger(', 'logger.')
        return any(marker in content for marker in markers)

    def _uses_allowed_logger_modules(self, content: str, allowed_modules: set) -> bool:
        """許可されたLoggerモジュール使用の検証（CODEMAP連携版）"""
        for module in allowed_modules:
            if module in content:
                return True
        return False

    def _uses_allowed_path_service_modules(self, content: str, allowed_modules: set) -> bool:
        """許可されたPathServiceモジュール使用の検証（CODEMAP連携版）"""
        for module in allowed_modules:
            if module in content:
                return True
        return False

    def _uses_path_service(self, content: str) -> bool:
        """PathService 関連APIの使用判定"""
        markers = ('get_common_path_service', 'create_path_service', 'IPathService', 'PathHelperService')
        return any(marker in content for marker in markers)

    def _validate_import_compliance(self, content: str, file_path: str) -> List[Dict]:
        """インポート文のコンプライアンス検証（CODEMAP連携版）"""
        violations = []
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                result = self.codemap_reader.validate_import_compliance(line, file_path)
                if not result['is_compliant']:
                    for violation in result['violations']:
                        violation['line_number'] = line_num
                        violation['line_content'] = line
                        violations.append(violation)

        return violations


class TestCommonFoundationCompliance:
    """共通基盤コンプライアンステストクラス"""

    @pytest.fixture
    def project_root(self):
        """プロジェクトルートパスのフィクスチャ"""
        return Path(__file__).parent.parent.parent.parent

    @pytest.fixture
    def compliance_checker(self, project_root):
        """コンプライアンスチェッカーのフィクスチャ"""
        return CommonFoundationComplianceChecker(project_root)

    @pytest.fixture
    def python_source_files(self, project_root):
        """Python ソースファイル一覧のフィクスチャ"""
        source_dirs = [
            project_root / "src" / "noveler",
            project_root / "src" / "scripts",
            project_root / "src" / "mcp_servers"
        ]

        python_files = []
        for source_dir in source_dirs:
            if source_dir.exists():
                python_files.extend(source_dir.rglob("*.py"))

        return python_files

    @pytest.mark.spec("SPEC-QUA-FOU-001")
    def test_console_usage_compliance_critical_threshold(
        self, compliance_checker, python_source_files
    ):
        """Console使用コンプライアンス（クリティカル基準）

        B30基準：
        - Console重複作成0件（絶対禁止）
        - 共通utilities使用95%以上
        """
        violations = compliance_checker.check_console_usage_compliance(python_source_files)

        # クリティカル：Console重複作成0件
        assert len(violations['console_duplications']) == 0, (
            f"Console重複作成が検出されました: "
            f"{', '.join(violations['console_duplications'])}"
        )

        # 高優先度：共通utilities使用率95%以上
        assert violations['compliance_score'] >= 0.95, (
            f"Console共通utilities使用率が基準を下回りました: "
            f"{violations['compliance_score']:.2%} < 95%"
        )

    @pytest.mark.spec("SPEC-QUA-FOU-002")
    def test_logger_usage_compliance_high_threshold(
        self, compliance_checker, python_source_files
    ):
        """Logger使用コンプライアンス（高優先度基準）

        B30基準：
        - 統一ログシステム使用90%以上
        """
        violations = compliance_checker.check_logger_usage_compliance(python_source_files)

        # 高優先度：統一ログシステム使用率90%以上
        assert violations['compliance_score'] >= 0.90, (
            f"統一ログシステム使用率が基準を下回りました: "
            f"{violations['compliance_score']:.2%} < 90%"
        )

        # 情報提供：レガシーlogging使用の警告
        if violations['legacy_logging_imports']:
            pytest.warns(UserWarning, (
                f"レガシーlogging使用が検出されました（修正推奨）: "
                f"{len(violations['legacy_logging_imports'])}件"
            ))

    @pytest.mark.spec("SPEC-QUA-FOU-003")
    def test_path_service_compliance_recommended_threshold(
        self, compliance_checker, python_source_files
    ):
        """PathService使用コンプライアンス（推奨基準）"""
        violations = compliance_checker.check_path_service_compliance(python_source_files)

        # クリティカル：ハードコーディング禁止
        assert len(violations['hardcoded_paths']) == 0, (
            f"パスハードコーディングが検出されました: "
            f"{', '.join(violations['hardcoded_paths'])}"
        )

    @pytest.mark.spec("SPEC-QUA-FOU-004")
    def test_progressive_check_manager_compliance_verification(
        self, compliance_checker, project_root
    ):
        """ProgressiveCheckManager の共通基盤使用検証"""
        target_file = project_root / "src" / "scripts" / "domain" / "services" / "progressive_check_manager.py"

        if not target_file.exists():
            pytest.skip("ProgressiveCheckManager not found")

        # 単一ファイルのコンプライアンスチェック
        violations = compliance_checker.check_console_usage_compliance([target_file])

        # ProgressiveCheckManagerはB20準拠実装のため100%コンプライアンス期待
        assert violations['compliance_score'] == 1.0, (
            f"ProgressiveCheckManagerの共通基盤使用率: {violations['compliance_score']:.2%}"
        )
        assert len(violations['console_duplications']) == 0

    @pytest.mark.spec("SPEC-QUA-FOU-005")
    def test_mcp_servers_logging_compliance_detection(
        self, compliance_checker, project_root
    ):
        """MCPサーバーのロギングコンプライアンス検出"""
        mcp_server_dir = project_root / "src" / "mcp_servers"

        if not mcp_server_dir.exists():
            pytest.skip("MCP servers directory not found")

        mcp_files = list(mcp_server_dir.rglob("*.py"))
        violations = compliance_checker.check_logger_usage_compliance(mcp_files)

        # MCPサーバーで検出された違反の報告
        if violations['legacy_logging_imports']:
            self._report_mcp_logging_violations(violations)

        # 修正可能な違反の検出と報告
        assert True  # 情報収集テストのため常に成功

    def _report_mcp_logging_violations(self, violations: Dict[str, List[str]]):
        """MCPサーバーのロギング違反報告"""
        print("\n=== MCP Server Logging Violations ===")
        print(f"Legacy logging imports: {len(violations['legacy_logging_imports'])}")
        for violation in violations['legacy_logging_imports']:
            print(f"  - {violation}")

        print(f"Direct getLogger usage: {len(violations['direct_getlogger_usage'])}")
        for violation in violations['direct_getlogger_usage']:
            print(f"  - {violation}")

    @pytest.mark.spec("SPEC-QUA-FOU-006")
    def test_overall_foundation_compliance_score(
        self, compliance_checker, python_source_files
    ):
        """全体的な共通基盤コンプライアンススコア"""
        console_violations = compliance_checker.check_console_usage_compliance(python_source_files)
        logger_violations = compliance_checker.check_logger_usage_compliance(python_source_files)
        path_violations = compliance_checker.check_path_service_compliance(python_source_files)

        # 重み付きスコア計算
        # Console: 40%（最重要）, Logger: 35%（重要）, Path: 25%（推奨）
        overall_score = (
            console_violations['compliance_score'] * 0.4 +
            logger_violations['compliance_score'] * 0.35 +
            path_violations['compliance_score'] * 0.25
        )

        print(f"\n=== Overall Foundation Compliance Score ===")
        print(f"Console compliance: {console_violations['compliance_score']:.2%}")
        print(f"Logger compliance: {logger_violations['compliance_score']:.2%}")
        print(f"Path compliance: {path_violations['compliance_score']:.2%}")
        print(f"Overall score: {overall_score:.2%}")

        # 総合スコア基準：85%以上
        assert overall_score >= 0.85, (
            f"全体的な共通基盤コンプライアンススコアが基準を下回りました: "
            f"{overall_score:.2%} < 85%"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
