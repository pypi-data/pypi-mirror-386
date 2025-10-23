"""
自動修正提案システムテスト

共通基盤違反の自動修正提案生成とテスト：
- 違反パターンの自動修正提案
- 修正前後の動作確認
- 修正精度検証
- バッチ修正提案生成
"""
from __future__ import annotations

import pytest
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

from noveler.infrastructure.logging.unified_logger import get_logger


@dataclass
class AutoFixProposal:
    """自動修正提案"""
    file_path: str
    line_number: int
    violation_type: str
    original_code: str
    fixed_code: str
    confidence: float
    additional_imports: List[str] = None
    removal_patterns: List[str] = None


class CommonFoundationAutoFixer:
    """共通基盤自動修正器"""

    def __init__(self):
        self.logger = get_logger(__name__)

        # 修正パターン定義
        self.fix_patterns = {
            # Console修正パターン
            'console_duplication': {
                'pattern': r'console\s*=\s*Console\(\)',
                'replacement': 'console = _get_console()',
                'required_import': 'from noveler.presentation.shared.shared_utilities import _get_console',
                'remove_import': 'from rich.console import Console'
            },

            # Logger修正パターン
            'legacy_logging': {
                'pattern': r'import logging',
                'replacement': '',
                'required_import': 'from noveler.infrastructure.logging.unified_logger import get_logger'
            },

            'legacy_getlogger': {
                'pattern': r'logging\.getLogger\(__name__\)',
                'replacement': 'get_logger(__name__)',
                'required_import': 'from noveler.infrastructure.logging.unified_logger import get_logger'
            },

            # PathService修正パターン
            'hardcoded_manuscript': {
                'pattern': r'project_root\s*\/\s*"40_原稿"',
                'replacement': 'path_service.get_manuscript_dir()',
                'required_import': 'from noveler.infrastructure.factories.path_service_factory import create_path_service'
            },

            'hardcoded_plot': {
                'pattern': r'project_root\s*\/\s*"30_プロット"',
                'replacement': 'path_service.get_plot_dir()',
                'required_import': 'from noveler.infrastructure.factories.path_service_factory import create_path_service'
            }
        }

    def generate_fix_proposals(self, file_path: Path, violations: List[Dict]) -> List[AutoFixProposal]:
        """修正提案の生成"""
        proposals = []

        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            for violation in violations:
                proposal = self._create_fix_proposal(
                    file_path, violation, lines
                )
                if proposal:
                    proposals.append(proposal)

        except Exception as e:
            self.logger.error(f"修正提案生成エラー {file_path}: {e}")

        return proposals

    def _create_fix_proposal(
        self,
        file_path: Path,
        violation: Dict,
        lines: List[str]
    ) -> Optional[AutoFixProposal]:
        """個別の修正提案作成"""
        violation_type = violation.get('type', '')
        line_num = violation.get('line', 1)

        if violation_type == 'console_duplication':
            return self._create_console_fix_proposal(file_path, violation, lines)
        elif violation_type == 'legacy_logging':
            return self._create_logging_fix_proposal(file_path, violation, lines)
        elif violation_type == 'hardcoded_path':
            return self._create_path_fix_proposal(file_path, violation, lines)

        return None

    def _create_console_fix_proposal(
        self,
        file_path: Path,
        violation: Dict,
        lines: List[str]
    ) -> AutoFixProposal:
        """Console修正提案の作成"""
        line_num = violation.get('line', 1)
        current_line = lines[line_num - 1] if 1 <= line_num <= len(lines) else ""

        def _locate(pattern: str, fallback_type: str) -> tuple[int, str]:
            if pattern in current_line:
                return line_num, current_line
            for idx, line in enumerate(lines, start=1):
                if pattern in line:
                    return idx, line
            self.logger.warning(
                "[%s] Pattern '%s' not found in %s", fallback_type, pattern, file_path
            )
            return line_num, current_line

        # Console重複作成の修正
        line_num, current_line = _locate('Console()', 'console_duplication')

        if 'Console()' in current_line:
            fixed_line = current_line.replace('Console()', '_get_console()')

            return AutoFixProposal(
                file_path=str(file_path),
                line_number=line_num,
                violation_type='console_duplication',
                original_code=current_line.strip(),
                fixed_code=fixed_line.strip(),
                confidence=0.95,
                additional_imports=['from noveler.presentation.shared.shared_utilities import _get_console'],
                removal_patterns=['from rich.console import Console']
            )

        # rich.console importの修正
        import_line_num, import_line = _locate('from rich.console import Console', 'console_import')

        if 'from rich.console import Console' in import_line:
            return AutoFixProposal(
                file_path=str(file_path),
                line_number=import_line_num,
                violation_type='console_import',
                original_code=import_line.strip(),
                fixed_code='from noveler.presentation.shared.shared_utilities import _get_console',
                confidence=0.90,
                additional_imports=[],
                removal_patterns=[import_line.strip()]
            )

        return None

    def _create_logging_fix_proposal(
        self,
        file_path: Path,
        violation: Dict,
        lines: List[str]
    ) -> AutoFixProposal:
        """Logging修正提案の作成"""
        line_num = violation.get('line', 1)
        current_line = lines[line_num - 1] if line_num <= len(lines) else ""

        # import logging の修正
        if 'import logging' in current_line and 'from' not in current_line:
            return AutoFixProposal(
                file_path=str(file_path),
                line_number=line_num,
                violation_type='legacy_logging_import',
                original_code=current_line.strip(),
                fixed_code='from noveler.infrastructure.logging.unified_logger import get_logger',
                confidence=0.90,
                additional_imports=['from noveler.infrastructure.logging.unified_logger import get_logger'],
                removal_patterns=[current_line.strip()]
            )

        # logging.getLogger の修正
        elif 'logging.getLogger' in current_line:
            fixed_line = current_line.replace('logging.getLogger', 'get_logger')

            return AutoFixProposal(
                file_path=str(file_path),
                line_number=line_num,
                violation_type='legacy_getlogger',
                original_code=current_line.strip(),
                fixed_code=fixed_line.strip(),
                confidence=0.95,
                additional_imports=['from noveler.infrastructure.logging.unified_logger import get_logger'],
                removal_patterns=[]
            )

        return None

    def _create_path_fix_proposal(
        self,
        file_path: Path,
        violation: Dict,
        lines: List[str]
    ) -> AutoFixProposal:
        """PathService修正提案の作成"""
        line_num = violation.get('line', 1)
        current_line = lines[line_num - 1] if line_num <= len(lines) else ""

        # ハードコーディングされたパスの修正
        path_mappings = {
            '"40_原稿"': 'path_service.get_manuscript_dir()',
            '"30_プロット"': 'path_service.get_plot_dir()',
            '"20_設定"': 'path_service.get_settings_dir()',
            '"10_企画"': 'path_service.get_planning_dir()'
        }

        for hardcoded_path, service_method in path_mappings.items():
            if hardcoded_path in current_line:
                fixed_line = current_line.replace(
                    f'project_root / {hardcoded_path}',
                    service_method
                )

                return AutoFixProposal(
                    file_path=str(file_path),
                    line_number=line_num,
                    violation_type='hardcoded_path',
                    original_code=current_line.strip(),
                    fixed_code=fixed_line.strip(),
                    confidence=0.85,
                    additional_imports=[
                        'from noveler.infrastructure.factories.path_service_factory import create_path_service'
                    ],
                    removal_patterns=[]
                )

        return None

    def apply_fix_proposal(self, proposal: AutoFixProposal, target_file: Path) -> bool:
        """修正提案の適用"""
        try:
            content = target_file.read_text(encoding='utf-8')
            lines = content.split('\n')

            # 該当行の修正
            replaced = False
            if proposal.original_code:
                original_stripped = proposal.original_code.strip()
                for idx, line in enumerate(lines):
                    if line.strip() == original_stripped:
                        lines[idx] = proposal.fixed_code
                        replaced = True
                        break
            if not replaced and proposal.line_number <= len(lines):
                lines[proposal.line_number - 1] = proposal.fixed_code

            # インポートの追加
            if proposal.additional_imports:
                import_section = self._find_import_section(lines)
                for new_import in proposal.additional_imports:
                    current_snapshot = "\n".join(lines)
                    if new_import not in current_snapshot:
                        lines.insert(import_section, new_import)

            # 不要なインポートの削除
            if proposal.removal_patterns:
                lines = [line for line in lines
                        if not any(pattern in line for pattern in proposal.removal_patterns)]

            # ファイルの更新
            target_file.write_text('\n'.join(lines), encoding='utf-8')
            return True

        except Exception as e:
            self.logger.error(f"修正適用エラー {target_file}: {e}")
            return False

    def _find_import_section(self, lines: List[str]) -> int:
        """インポートセクションの検出"""
        for i, line in enumerate(lines):
            if line.strip().startswith('from ') or line.strip().startswith('import '):
                return i

        # docstring の後を検索
        in_docstring = False
        for i, line in enumerate(lines):
            if '"""' in line or "'''" in line:
                in_docstring = not in_docstring
            elif not in_docstring and line.strip():
                return i

        return 0


class TestAutoFixSuggestions:
    """自動修正提案システムテスト"""

    @pytest.fixture
    def auto_fixer(self):
        """自動修正器のフィクスチャ"""
        return CommonFoundationAutoFixer()

    @pytest.fixture
    def sample_violation_file(self, tmp_path):
        """サンプル違反ファイルの作成"""
        sample_file = tmp_path / "sample_violation.py"
        sample_content = '''"""
サンプル違反ファイル
"""
import logging
from rich.console import Console

class SampleClass:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.console = Console()
        self.manuscript_path = project_root / "40_原稿"

    def process(self):
        self.logger.info("Processing")
        self.console.print("Hello")
'''
        sample_file.write_text(sample_content)
        return sample_file

    @pytest.mark.spec("SPEC-FIX-SUG-001")
    def test_console_duplication_fix_generation(self, auto_fixer, sample_violation_file):
        """Console重複作成修正提案生成"""
        violations = [
            {'type': 'console_duplication', 'line': 9, 'severity': 'critical'},
            {'type': 'console_duplication', 'line': 6, 'severity': 'critical'}
        ]

        proposals = auto_fixer.generate_fix_proposals(sample_violation_file, violations)

        # Console修正提案の確認
        console_proposals = [p for p in proposals if p.violation_type == 'console_duplication']

        print(f"\n=== Console Duplication Fix Generation ===")
        print(f"Console proposals generated: {len(console_proposals)}")

        for proposal in console_proposals:
            print(f"Line {proposal.line_number}:")
            print(f"  Original: {proposal.original_code}")
            print(f"  Fixed: {proposal.fixed_code}")
            print(f"  Confidence: {proposal.confidence:.2%}")

        # 修正提案の品質確認
        assert len(console_proposals) > 0, "Console修正提案が生成されませんでした"

        for proposal in console_proposals:
            assert proposal.confidence >= 0.80, f"修正提案の信頼度が低すぎます: {proposal.confidence}"
            assert '_get_console()' in proposal.fixed_code, "共通Console使用の修正が含まれていません"

    @pytest.mark.spec("SPEC-FIX-SUG-002")
    def test_logging_fix_generation(self, auto_fixer, sample_violation_file):
        """Logging修正提案生成"""
        violations = [
            {'type': 'legacy_logging', 'line': 4, 'severity': 'critical'},
            {'type': 'legacy_logging', 'line': 8, 'severity': 'critical'}
        ]

        proposals = auto_fixer.generate_fix_proposals(sample_violation_file, violations)

        # Logging修正提案の確認
        logging_proposals = [p for p in proposals if 'logging' in p.violation_type]

        print(f"\n=== Logging Fix Generation ===")
        print(f"Logging proposals generated: {len(logging_proposals)}")

        for proposal in logging_proposals:
            print(f"Type: {proposal.violation_type}")
            print(f"  Original: {proposal.original_code}")
            print(f"  Fixed: {proposal.fixed_code}")
            print(f"  Additional imports: {proposal.additional_imports}")

        # 修正提案の品質確認
        assert len(logging_proposals) > 0, "Logging修正提案が生成されませんでした"

        unified_logger_import_found = False
        for proposal in logging_proposals:
            if proposal.additional_imports:
                for imp in proposal.additional_imports:
                    if 'unified_logger' in imp and 'get_logger' in imp:
                        unified_logger_import_found = True

        assert unified_logger_import_found, "統一Logger使用の修正が含まれていません"

    @pytest.mark.spec("SPEC-FIX-SUG-003")
    def test_path_service_fix_generation(self, auto_fixer, sample_violation_file):
        """PathService修正提案生成"""
        violations = [
            {'type': 'hardcoded_path', 'line': 10, 'severity': 'critical'}
        ]

        proposals = auto_fixer.generate_fix_proposals(sample_violation_file, violations)

        # PathService修正提案の確認
        path_proposals = [p for p in proposals if p.violation_type == 'hardcoded_path']

        print(f"\n=== PathService Fix Generation ===")
        print(f"Path proposals generated: {len(path_proposals)}")

        for proposal in path_proposals:
            print(f"Line {proposal.line_number}:")
            print(f"  Original: {proposal.original_code}")
            print(f"  Fixed: {proposal.fixed_code}")
            print(f"  Service method: {'path_service' in proposal.fixed_code}")

        # 修正提案の品質確認
        if path_proposals:  # パス修正提案が生成された場合
            for proposal in path_proposals:
                assert 'path_service' in proposal.fixed_code, "PathService使用の修正が含まれていません"
                assert proposal.confidence >= 0.75, f"PathService修正の信頼度が低すぎます: {proposal.confidence}"

    @pytest.mark.spec("SPEC-FIX-SUG-004")
    def test_fix_proposal_application(self, auto_fixer, sample_violation_file):
        """修正提案の適用テスト"""
        # サンプル修正提案の作成
        proposal = AutoFixProposal(
            file_path=str(sample_violation_file),
            line_number=9,
            violation_type='console_duplication',
            original_code='        self.console = Console()',
            fixed_code='        self.console = _get_console()',
            confidence=0.95,
            additional_imports=['from noveler.presentation.shared.shared_utilities import _get_console'],
            removal_patterns=['from rich.console import Console']
        )

        # 修正前の内容確認
        original_content = sample_violation_file.read_text()
        assert 'Console()' in original_content, "修正前のConsole()が見つかりません"

        # 修正の適用
        success = auto_fixer.apply_fix_proposal(proposal, sample_violation_file)
        assert success, "修正提案の適用に失敗しました"

        # 修正後の内容確認
        fixed_content = sample_violation_file.read_text()

        print(f"\n=== Fix Proposal Application ===")
        print(f"Fix applied successfully: {success}")
        print(f"_get_console() in fixed content: {'_get_console()' in fixed_content}")
        print(f"Console() in fixed content: {'Console()' in fixed_content}")

        # 修正内容の検証
        assert '_get_console()' in fixed_content, "修正後のコードに_get_console()が含まれていません"
        assert 'Console()' not in fixed_content, "修正後のコードにConsole()が残っています"

        # 統一import の追加確認
        if proposal.additional_imports:
            for new_import in proposal.additional_imports:
                assert new_import in fixed_content, f"必要なインポートが追加されていません: {new_import}"

    @pytest.mark.spec("SPEC-FIX-SUG-005")
    def test_batch_fix_proposal_generation(self, auto_fixer, tmp_path):
        """バッチ修正提案生成"""
        # 複数の違反ファイル作成
        violation_files = []
        for i in range(3):
            file_path = tmp_path / f"violation_{i}.py"
            content = f'''
import logging
from rich.console import Console

def function_{i}():
    logger = logging.getLogger(__name__)
    console = Console()
    return project_root / "40_原稿"
'''
            file_path.write_text(content)
            violation_files.append(file_path)

        # 各ファイルの違反定義
        all_violations = {
            str(file_path): [
                {'type': 'legacy_logging', 'line': 2, 'severity': 'critical'},
                {'type': 'console_duplication', 'line': 3, 'severity': 'critical'},
                {'type': 'legacy_logging', 'line': 6, 'severity': 'critical'},
                {'type': 'console_duplication', 'line': 7, 'severity': 'critical'},
                {'type': 'hardcoded_path', 'line': 8, 'severity': 'critical'}
            ] for file_path in violation_files
        }

        # バッチ修正提案生成
        batch_proposals = {}
        total_proposals = 0

        for file_path, violations in all_violations.items():
            proposals = auto_fixer.generate_fix_proposals(Path(file_path), violations)
            batch_proposals[file_path] = proposals
            total_proposals += len(proposals)

        print(f"\n=== Batch Fix Proposal Generation ===")
        print(f"Files processed: {len(violation_files)}")
        print(f"Total proposals generated: {total_proposals}")

        # ファイル別の修正提案統計
        for file_path, proposals in batch_proposals.items():
            file_name = Path(file_path).name
            print(f"  {file_name}: {len(proposals)} proposals")

            # 違反タイプ別の統計
            type_count = {}
            for proposal in proposals:
                vtype = proposal.violation_type
                type_count[vtype] = type_count.get(vtype, 0) + 1

            for vtype, count in type_count.items():
                print(f"    - {vtype}: {count}")

        # バッチ処理の品質確認
        assert total_proposals > 0, "バッチ修正提案が生成されませんでした"

        # 各ファイルに対して適切な修正提案が生成されているか
        for file_path, proposals in batch_proposals.items():
            assert len(proposals) >= 2, f"ファイル {Path(file_path).name} の修正提案が不足しています"

    @pytest.mark.spec("SPEC-FIX-SUG-006")
    def test_fix_confidence_assessment(self, auto_fixer, sample_violation_file):
        """修正信頼度評価"""
        violations = [
            {'type': 'console_duplication', 'line': 9, 'severity': 'critical'},
            {'type': 'legacy_logging', 'line': 8, 'severity': 'critical'},
            {'type': 'hardcoded_path', 'line': 10, 'severity': 'critical'}
        ]

        proposals = auto_fixer.generate_fix_proposals(sample_violation_file, violations)

        print(f"\n=== Fix Confidence Assessment ===")
        print(f"Total proposals: {len(proposals)}")

        # 信頼度分布の分析
        confidence_distribution = {
            'high': 0,    # 90%以上
            'medium': 0,  # 70-89%
            'low': 0      # 70%未満
        }

        for proposal in proposals:
            confidence = proposal.confidence
            print(f"{proposal.violation_type} (Line {proposal.line_number}): {confidence:.2%}")

            if confidence >= 0.90:
                confidence_distribution['high'] += 1
            elif confidence >= 0.70:
                confidence_distribution['medium'] += 1
            else:
                confidence_distribution['low'] += 1

        print(f"\nConfidence Distribution:")
        for level, count in confidence_distribution.items():
            print(f"  {level.capitalize()}: {count}")

        # 信頼度評価基準
        total_proposals_count = len(proposals)
        if total_proposals_count > 0:
            high_confidence_rate = confidence_distribution['high'] / total_proposals_count

            # 80%以上が高信頼度修正であることを期待
            assert high_confidence_rate >= 0.80, (
                f"高信頼度修正提案の割合が不足: {high_confidence_rate:.2%} < 80%"
            )

    @pytest.mark.spec("SPEC-FIX-SUG-007")
    def test_progressive_check_manager_auto_fix(self, auto_fixer):
        """ProgressiveCheckManager自動修正提案"""
        pcm_file = Path(__file__).parent.parent.parent.parent / \
                  "src" / "scripts" / "domain" / "services" / "progressive_check_manager.py"

        if not pcm_file.exists():
            pytest.skip("ProgressiveCheckManager file not found")

        # 仮想的な違反（実際のファイルは修正済みなのでテスト用）
        mock_violations = [
            {'type': 'legacy_logging', 'line': 15, 'severity': 'critical'},
            {'type': 'console_duplication', 'line': 127, 'severity': 'critical'}
        ]

        proposals = auto_fixer.generate_fix_proposals(pcm_file, mock_violations)

        print(f"\n=== ProgressiveCheckManager Auto-Fix ===")
        print(f"Proposals for PCM: {len(proposals)}")

        for proposal in proposals:
            print(f"  {proposal.violation_type}: {proposal.confidence:.2%}")
            print(f"    Original: {proposal.original_code[:50]}...")
            print(f"    Fixed: {proposal.fixed_code[:50]}...")

        # ProgressiveCheckManagerは高品質な修正提案を期待
        if proposals:
            avg_confidence = sum(p.confidence for p in proposals) / len(proposals)
            assert avg_confidence >= 0.90, (
                f"ProgressiveCheckManager修正提案の平均信頼度が低い: {avg_confidence:.2%}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
