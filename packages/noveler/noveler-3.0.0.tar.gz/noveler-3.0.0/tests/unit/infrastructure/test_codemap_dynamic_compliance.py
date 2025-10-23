"""
CODEMAP連携動的コンプライアンステストスイート

CODEMAP.yamlを単一信頼源とした共通基盤コンポーネント使用検証の動的テスト。
設定変更時にコード修正不要な動的テストシステム。

Version: 1.0.0 - CODEMAP連携版
Author: Claude Code
Date: 2025-09-09
"""
from __future__ import annotations

import pytest
import sys
from pathlib import Path
from typing import Dict, List
from unittest.mock import MagicMock

# CODEMAP読み取りユーティリティをインポート
sys.path.insert(0, str(Path(__file__).parents[3] / "src"))
from noveler.tools.codemap_reader import create_codemap_reader
from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)


class CODEMAPDynamicComplianceChecker:
    """CODEMAP連携動的コンプライアンスチェッカー"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.codemap_reader = create_codemap_reader()
        self.logger = logger

    def check_dynamic_compliance(self, target_files: List[Path]) -> Dict[str, any]:
        """動的コンプライアンスチェック（CODEMAP基準）"""
        results = {
            'console_violations': [],
            'logger_violations': [],
            'path_violations': [],
            'error_handler_violations': [],
            'compliance_scores': {},
            'thresholds': {}
        }

        # CODEMAPから基準値を取得
        thresholds = self.codemap_reader.get_compliance_thresholds()
        results['thresholds'] = {
            'console_shared_usage_rate': thresholds.console_shared_usage_rate,
            'logger_unified_usage_rate': thresholds.logger_unified_usage_rate,
            'path_service_usage_rate': thresholds.path_service_usage_rate,
            'console_duplication_max': thresholds.console_duplication_max,
            'legacy_logging_max': thresholds.legacy_logging_max,
            'path_hardcoding_max': thresholds.path_hardcoding_max
        }

        # 各コンポーネントの動的チェック
        results['console_violations'] = self._check_console_compliance(target_files)
        results['logger_violations'] = self._check_logger_compliance(target_files)
        results['path_violations'] = self._check_path_compliance(target_files)
        results['error_handler_violations'] = self._check_error_handler_compliance(target_files)

        # コンプライアンススコアの計算
        results['compliance_scores'] = self._calculate_compliance_scores(target_files)

        return results

    def _check_console_compliance(self, target_files: List[Path]) -> List[Dict]:
        """Consoleコンプライアンスチェック"""
        violations = []
        console_patterns = self.codemap_reader.get_forbidden_patterns("console")

        for file_path in target_files:
            if not file_path.suffix == '.py':
                continue

            try:
                content = file_path.read_text(encoding='utf-8')
                file_path_str = str(file_path)

                # 禁止パターンチェック
                for pattern in console_patterns:
                    if pattern.pattern in content:
                        # 例外チェック
                        if not self.codemap_reader.is_pattern_allowed_for_file(
                            pattern.pattern, file_path_str, "console"
                        ):
                            violations.append({
                                'file': file_path_str,
                                'component': 'console',
                                'pattern': pattern.pattern,
                                'message': pattern.message,
                                'severity': pattern.severity,
                                'suggested_fix': pattern.suggested_fix
                            })
            except Exception as e:
                self.logger.warning(f"Error checking console compliance for {file_path}: {e}")

        return violations

    def _check_logger_compliance(self, target_files: List[Path]) -> List[Dict]:
        """Loggerコンプライアンスチェック"""
        violations = []
        logger_patterns = self.codemap_reader.get_forbidden_patterns("logger")

        for file_path in target_files:
            if not file_path.suffix == '.py':
                continue

            try:
                content = file_path.read_text(encoding='utf-8')
                file_path_str = str(file_path)

                # 禁止パターンチェック
                for pattern in logger_patterns:
                    if pattern.pattern in content:
                        # 例外チェック
                        if not self.codemap_reader.is_pattern_allowed_for_file(
                            pattern.pattern, file_path_str, "logger"
                        ):
                            violations.append({
                                'file': file_path_str,
                                'component': 'logger',
                                'pattern': pattern.pattern,
                                'message': pattern.message,
                                'severity': pattern.severity,
                                'suggested_fix': pattern.suggested_fix
                            })
            except Exception as e:
                self.logger.warning(f"Error checking logger compliance for {file_path}: {e}")

        return violations

    def _check_path_compliance(self, target_files: List[Path]) -> List[Dict]:
        """Pathコンプライアンスチェック"""
        violations = []
        path_patterns = self.codemap_reader.get_forbidden_patterns("paths")

        for file_path in target_files:
            if not file_path.suffix == '.py':
                continue

            try:
                content = file_path.read_text(encoding='utf-8')
                file_path_str = str(file_path)

                # 禁止パターンチェック
                for pattern in path_patterns:
                    if pattern.pattern in content:
                        violations.append({
                            'file': file_path_str,
                            'component': 'paths',
                            'pattern': pattern.pattern,
                            'message': pattern.message,
                            'severity': pattern.severity,
                            'suggested_fix': pattern.suggested_fix
                        })
            except Exception as e:
                self.logger.warning(f"Error checking path compliance for {file_path}: {e}")

        return violations

    def _check_error_handler_compliance(self, target_files: List[Path]) -> List[Dict]:
        """ErrorHandlerコンプライアンスチェック"""
        violations = []
        error_handler_definition = self.codemap_reader.get_component_definition("error_handler")

        if not error_handler_definition:
            return violations

        allowed_modules = self.codemap_reader.get_allowed_modules("error_handler")

        for file_path in target_files:
            if not file_path.suffix == '.py':
                continue

            try:
                content = file_path.read_text(encoding='utf-8')

                # エラーハンドリングが必要なパターンを検出
                if any(pattern in content for pattern in ['try:', 'except:', 'raise ', 'Exception']):
                    # 統一エラーハンドリング使用チェック
                    uses_unified_handler = any(module in content for module in allowed_modules)
                    if not uses_unified_handler:
                        violations.append({
                            'file': str(file_path),
                            'component': 'error_handler',
                            'pattern': 'missing_unified_error_handler',
                            'message': '統一エラーハンドリング未使用',
                            'severity': 'warning',
                            'suggested_fix': f"from {error_handler_definition.primary_module} import {error_handler_definition.primary_function}"
                        })
            except Exception as e:
                self.logger.warning(f"Error checking error handler compliance for {file_path}: {e}")

        return violations

    def _calculate_compliance_scores(self, target_files: List[Path]) -> Dict[str, float]:
        """コンプライアンススコア計算"""
        scores = {
            'console_shared_usage_rate': 0.0,
            'logger_unified_usage_rate': 0.0,
            'path_service_usage_rate': 0.0,
            'error_handling_unified_rate': 0.0
        }

        total_files = len([f for f in target_files if f.suffix == '.py'])
        if total_files == 0:
            return scores

        # Console使用率
        console_compliant = 0
        console_allowed_modules = self.codemap_reader.get_allowed_modules("console")

        # Logger使用率
        logger_compliant = 0
        logger_allowed_modules = self.codemap_reader.get_allowed_modules("logger")

        # PathService使用率
        path_service_compliant = 0
        path_service_allowed_modules = self.codemap_reader.get_allowed_modules("path_service")

        # ErrorHandler使用率
        error_handler_compliant = 0
        error_handler_allowed_modules = self.codemap_reader.get_allowed_modules("error_handler")

        for file_path in target_files:
            if not file_path.suffix == '.py':
                continue

            try:
                content = file_path.read_text(encoding='utf-8')

                # Console使用率チェック
                if any(module in content for module in console_allowed_modules):
                    console_compliant += 1

                # Logger使用率チェック
                if any(module in content for module in logger_allowed_modules):
                    logger_compliant += 1

                # PathService使用率チェック
                if any(module in content for module in path_service_allowed_modules):
                    path_service_compliant += 1

                # ErrorHandler使用率チェック
                if any(module in content for module in error_handler_allowed_modules):
                    error_handler_compliant += 1

            except Exception as e:
                self.logger.warning(f"Error calculating compliance scores for {file_path}: {e}")

        scores['console_shared_usage_rate'] = console_compliant / total_files
        scores['logger_unified_usage_rate'] = logger_compliant / total_files
        scores['path_service_usage_rate'] = path_service_compliant / total_files
        scores['error_handling_unified_rate'] = error_handler_compliant / total_files

        return scores

    def validate_mcp_server_exceptions(self, file_path: Path) -> bool:
        """MCPサーバー例外の検証"""
        return self.codemap_reader.is_file_in_mcp_server_path(str(file_path))


class TestCODEMAPDynamicCompliance:
    """CODEMAP連携動的コンプライアンステストクラス"""

    @pytest.fixture
    def project_root(self):
        """プロジェクトルートパスのフィクスチャ"""
        return Path(__file__).parent.parent.parent.parent

    @pytest.fixture
    def compliance_checker(self, project_root):
        """動的コンプライアンスチェッカーのフィクスチャ"""
        return CODEMAPDynamicComplianceChecker(project_root)

    @pytest.fixture
    def sample_files(self, project_root):
        """テスト対象ファイルのフィクスチャ"""
        src_dir = project_root / "src" / "noveler"
        return list(src_dir.rglob("*.py"))[:10]  # 最初の10ファイルでテスト

    def test_codemap_reader_initialization(self, compliance_checker):
        """CODEMAPReader初期化テスト"""
        assert compliance_checker.codemap_reader is not None
        assert compliance_checker.codemap_reader.codemap_path.exists()

    def test_dynamic_compliance_thresholds_loading(self, compliance_checker):
        """CODEMAP基準値の動的読み込みテスト"""
        thresholds = compliance_checker.codemap_reader.get_compliance_thresholds()

        assert thresholds.console_shared_usage_rate >= 0.0
        assert thresholds.logger_unified_usage_rate >= 0.0
        assert thresholds.path_service_usage_rate >= 0.0
        assert thresholds.console_duplication_max >= 0
        assert thresholds.legacy_logging_max >= 0
        assert thresholds.path_hardcoding_max >= 0

    def test_component_definitions_loading(self, compliance_checker):
        """共通基盤コンポーネント定義の動的読み込みテスト"""
        console_def = compliance_checker.codemap_reader.get_component_definition("console")
        logger_def = compliance_checker.codemap_reader.get_component_definition("logger")
        path_service_def = compliance_checker.codemap_reader.get_component_definition("path_service")

        assert console_def is not None
        assert console_def.primary_module
        assert console_def.primary_function

        assert logger_def is not None
        assert logger_def.primary_module
        assert logger_def.primary_function

        assert path_service_def is not None
        assert path_service_def.primary_module
        assert path_service_def.primary_function

    def test_forbidden_patterns_loading(self, compliance_checker):
        """禁止パターンの動的読み込みテスト"""
        console_patterns = compliance_checker.codemap_reader.get_forbidden_patterns("console")
        logger_patterns = compliance_checker.codemap_reader.get_forbidden_patterns("logger")

        assert len(console_patterns) > 0
        assert len(logger_patterns) > 0

        for pattern in console_patterns:
            assert pattern.pattern
            assert pattern.severity in ['critical', 'warning', 'info']
            assert pattern.message

    def test_dynamic_compliance_check(self, compliance_checker, sample_files):
        """動的コンプライアンスチェックテスト"""
        results = compliance_checker.check_dynamic_compliance(sample_files)

        # 結果構造の検証
        assert 'console_violations' in results
        assert 'logger_violations' in results
        assert 'path_violations' in results
        assert 'error_handler_violations' in results
        assert 'compliance_scores' in results
        assert 'thresholds' in results

        # スコアの妥当性チェック
        scores = results['compliance_scores']
        for score_name, score_value in scores.items():
            assert 0.0 <= score_value <= 1.0, f"Score {score_name} is out of range: {score_value}"

    def test_mcp_server_exceptions(self, compliance_checker):
        """MCPサーバー例外処理テスト"""
        # MCPサーバーパスのファイル
        mcp_file = Path("src/mcp_servers/test_file.py")
        assert compliance_checker.validate_mcp_server_exceptions(mcp_file) == True

        # 通常のファイル
        normal_file = Path("src/noveler/domain/test_file.py")
        assert compliance_checker.validate_mcp_server_exceptions(normal_file) == False

    def test_allowed_modules_detection(self, compliance_checker):
        """許可モジュール検出テスト"""
        console_modules = compliance_checker.codemap_reader.get_allowed_modules("console")
        logger_modules = compliance_checker.codemap_reader.get_allowed_modules("logger")
        path_service_modules = compliance_checker.codemap_reader.get_allowed_modules("path_service")

        assert len(console_modules) > 0
        assert len(logger_modules) > 0
        assert len(path_service_modules) > 0

    def test_import_compliance_validation(self, compliance_checker):
        """インポート文コンプライアンス検証テスト"""
        # 違反インポート文
        violation_import = "from rich.console import Console"
        result = compliance_checker.codemap_reader.validate_import_compliance(
            violation_import, "test_file.py"
        )
        assert not result['is_compliant']
        assert len(result['violations']) > 0

        # 適合インポート文
        compliant_import = "from noveler.presentation.shared.shared_utilities import _get_console"
        result = compliance_checker.codemap_reader.validate_import_compliance(
            compliant_import, "test_file.py"
        )
        assert result['is_compliant']
        assert len(result['violations']) == 0

    @pytest.mark.integration
    def test_end_to_end_compliance_check(self, compliance_checker, project_root):
        """エンドツーエンド動的コンプライアンスチェックテスト"""
        # 実際のプロジェクトファイルに対する包括的チェック
        target_files = list((project_root / "src" / "noveler").rglob("*.py"))

        if len(target_files) == 0:
            pytest.skip("No target files found for integration test")

        results = compliance_checker.check_dynamic_compliance(target_files)

        # 基本的な結果検証
        assert isinstance(results, dict)
        assert 'compliance_scores' in results
        assert 'thresholds' in results

        # 基準値との比較（警告レベル）
        thresholds = results['thresholds']
        scores = results['compliance_scores']

        console_threshold = thresholds['console_shared_usage_rate']
        console_score = scores['console_shared_usage_rate']

        if console_score < console_threshold:
            compliance_checker.logger.warning(
                f"Console usage score ({console_score:.2%}) below threshold ({console_threshold:.2%})"
            )

        logger_threshold = thresholds['logger_unified_usage_rate']
        logger_score = scores['logger_unified_usage_rate']

        if logger_score < logger_threshold:
            compliance_checker.logger.warning(
                f"Logger usage score ({logger_score:.2%}) below threshold ({logger_threshold:.2%})"
            )


if __name__ == "__main__":
    # 動的テスト実行例
    project_root = Path(__file__).parent.parent.parent.parent
    checker = CODEMAPDynamicComplianceChecker(project_root)

    sample_files = list((project_root / "src" / "noveler").rglob("*.py"))[:5]
    results = checker.check_dynamic_compliance(sample_files)

    print("=== CODEMAP Dynamic Compliance Results ===")
    print(f"Console violations: {len(results['console_violations'])}")
    print(f"Logger violations: {len(results['logger_violations'])}")
    print(f"Path violations: {len(results['path_violations'])}")
    print(f"Compliance scores:")
    for component, score in results['compliance_scores'].items():
        threshold = results['thresholds'].get(f"{component.split('_')[0]}_shared_usage_rate", 0.8)
        status = "✓" if score >= threshold else "✗"
        print(f"  {component}: {score:.2%} {status}")
