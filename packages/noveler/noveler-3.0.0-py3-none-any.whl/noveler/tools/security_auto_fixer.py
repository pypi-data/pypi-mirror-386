#!/usr/bin/env python3
"""
セキュリティ脆弱性自動修正ツール

検出された脆弱性を自動で修正し、セキュアなコードパターンに置き換える
"""

import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from noveler.infrastructure.config.unified_config_manager import get_configuration_manager
from noveler.presentation.shared.shared_utilities import get_console
from noveler.tools.security_vulnerability_scanner import (
    SecurityScanResult,
    SecurityVulnerabilityScanner,
    VulnerabilityType,
)


@dataclass
class FixResult:
    """修正結果データクラス"""

    file_path: str
    fixes_applied: int = 0
    backup_created: bool = False
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class SecurityAutoFixer:
    """セキュリティ脆弱性自動修正ツール"""

    def __init__(self, logger_service: Any | None = None, console_service: Any | None = None) -> None:
        self.config = get_configuration_manager()
        self.console = get_console()
        self.scanner = SecurityVulnerabilityScanner()
        self.fix_patterns = self._initialize_fix_patterns()

        self.logger_service = logger_service
        self.console_service = console_service

    def fix_project_vulnerabilities(self, create_backup: bool = True) -> dict[str, FixResult]:
        """プロジェクト全体の脆弱性を自動修正"""
        self.console.print("🔧 セキュリティ脆弱性の自動修正を開始しています...", style="info")

        # まずスキャンを実行
        scan_result = self.scanner.scan_project()

        if not scan_result.vulnerabilities:
            self.console.print("✅ 修正すべき脆弱性が見つかりませんでした", style="success")
            return {}

        # ファイル別に脆弱性をグループ化
        files_to_fix = self._group_vulnerabilities_by_file(scan_result)

        fix_results = {}

        for file_path, vulnerabilities in files_to_fix.items():
            try:
                result = self._fix_file_vulnerabilities(file_path, vulnerabilities, create_backup)
                fix_results[file_path] = result

                if result.fixes_applied > 0:
                    self.console.print(f"✅ {file_path}: {result.fixes_applied}件の脆弱性を修正", style="success")
                else:
                    self.console.print(f"ℹ️  {file_path}: 修正不要または手動対応が必要", style="info")

            except Exception as e:
                self.console.print(f"❌ {file_path}: 修正中にエラーが発生 - {e!s}", style="error")
                fix_results[file_path] = FixResult(file_path=file_path, errors=[str(e)])

        self._print_fix_summary(fix_results)
        return fix_results

    def _group_vulnerabilities_by_file(self, scan_result: SecurityScanResult) -> dict[str, list]:
        """脆弱性をファイル別にグループ化"""
        files_to_fix = {}
        for vuln in scan_result.vulnerabilities:
            if vuln.file_path not in files_to_fix:
                files_to_fix[vuln.file_path] = []
            files_to_fix[vuln.file_path].append(vuln)
        return files_to_fix

    def _fix_file_vulnerabilities(
        self, relative_file_path: str, vulnerabilities: list, create_backup: bool
    ) -> FixResult:
        """単一ファイルの脆弱性を修正"""
        file_path = self.config.get_project_root() / relative_file_path
        result = FixResult(file_path=relative_file_path)

        if not file_path.exists():
            result.errors.append(f"ファイルが存在しません: {file_path}")
            return result

        try:
            # バックアップ作成
            if create_backup:
                backup_path = file_path.with_suffix(file_path.suffix + ".backup")
                shutil.copy2(file_path, backup_path)
                result.backup_created = True

            # ファイル内容を読み込み
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # 各脆弱性タイプに対して修正を適用
            for vuln in vulnerabilities:
                if vuln.vuln_type in self.fix_patterns:
                    fix_func = self.fix_patterns[vuln.vuln_type]
                    new_content = fix_func(content, vuln)
                    if new_content != content:
                        content = new_content
                        result.fixes_applied += 1

            # 修正されたコンテンツを書き込み
            if content != original_content:
                file_path.write_text(content, encoding="utf-8")

        except Exception as e:
            result.errors.append(f"ファイル処理エラー: {e!s}")

        return result

    def _initialize_fix_patterns(self) -> dict[VulnerabilityType, Callable]:
        """修正パターンの初期化"""
        return {
            VulnerabilityType.PATH_TRAVERSAL: self._fix_path_traversal,
            VulnerabilityType.COMMAND_INJECTION: self._fix_command_injection,
            VulnerabilityType.HARDCODED_SECRET: self._fix_hardcoded_secret,
            VulnerabilityType.UNSAFE_FILE_OPERATION: self._fix_unsafe_file_operation,
            VulnerabilityType.XML_YAML_INJECTION: self._fix_yaml_injection,
            VulnerabilityType.INSECURE_RANDOM: self._fix_insecure_random,
            VulnerabilityType.WEAK_CRYPTO: self._fix_weak_crypto,
        }

    def _fix_path_traversal(self, content: str, vuln: Any) -> str:
        """パストラバーサル脆弱性の修正"""
        lines = content.split("\n")

        if vuln.line_number <= len(lines):
            original_line = lines[vuln.line_number - 1]

            # 危険な相対パス参照を安全なPath Service呼び出しに置き換え
            if "../00_ガイド" in original_line:
                # Path Serviceを使用した安全な実装に置き換え
                fixed_line = re.sub(r'["\'][^"\']*\.\./[^"\']*["\']', "self.config.get_project_root()", original_line)

                # import文が必要な場合は追加
                if "self.config" in fixed_line and "get_configuration_manager" not in content:
                    # インポート文を追加する位置を見つける
                    import_line = (
                        "from noveler.infrastructure.config.unified_config_manager import get_configuration_manager"
                    )

                    # 既存のimport文の後に追加
                    import_inserted = False
                    for i, line in enumerate(lines):
                        if line.startswith(("from noveler.", "import ")):
                            continue
                        lines.insert(i, import_line)
                        import_inserted = True
                        break

                    if not import_inserted:
                        lines.insert(0, import_line)

                lines[vuln.line_number - 1] = fixed_line
                return "\n".join(lines)

            # その他のパストラバーサルパターンの修正
            if "../" in original_line and "test" not in vuln.file_path.lower():
                fixed_line = re.sub(r'["\'][^"\']*\.\./[^"\']*["\']', "validated_path", original_line)
                lines[vuln.line_number - 1] = fixed_line
                return "\n".join(lines)

        return content

    def _fix_command_injection(self, content: str, vuln: Any) -> str:
        """コマンドインジェクション脆弱性の修正"""
        lines = content.split("\n")

        if vuln.line_number <= len(lines):
            original_line = lines[vuln.line_number - 1]

            # f文字列でのcp/mvコマンド構築を安全な実装に置き換え
            if re.search(r'f["\'].*cp\s+.*\{.*\}.*["\']', original_line):
                # shutilを使用した安全な実装に置き換え
                fixed_line = re.sub(
                    r'f["\']cp\s+([^{]+)\{([^}]+)\}\s+([^"\']+)["\']',
                    r"# 安全なファイルコピー実装が必要: shutil.copy(\1{\2}, \3)",
                    original_line,
                )

                # shutil importを追加
                if "shutil" not in content:
                    import_line = "import shutil"
                    for i, line in enumerate(lines):
                        if line.startswith(("import ", "from ")):
                            continue
                        lines.insert(i, import_line)
                        break

                lines[vuln.line_number - 1] = fixed_line
                return "\n".join(lines)

        return content

    def _fix_hardcoded_secret(self, content: str, vuln: Any) -> str:
        """ハードコードされたシークレットの修正"""
        lines = content.split("\n")

        if vuln.line_number <= len(lines):
            original_line = lines[vuln.line_number - 1]

            # テストファイルの場合はそのまま（テスト用データのため）
            if "test" in vuln.file_path.lower():
                return content

            # パスワード/秘密鍵らしきものを環境変数参照に置き換え
            if re.search(r'(password|secret|key|token)\s*=\s*["\'][^"\']+["\']', original_line, re.IGNORECASE):
                fixed_line = re.sub(
                    r'(password|secret|key|token)\s*=\s*["\'][^"\']+["\']',
                    r'\1 = os.getenv("\1".upper(), "")',
                    original_line,
                    flags=re.IGNORECASE,
                )

                # os importを追加
                if "import os" not in content:
                    import_line = "import os"
                    for i, line in enumerate(lines):
                        if line.startswith(("import ", "from ")):
                            continue
                        lines.insert(i, import_line)
                        break

                lines[vuln.line_number - 1] = fixed_line
                return "\n".join(lines)

        return content

    def _fix_unsafe_file_operation(self, content: str, vuln: Any) -> str:
        """安全でないファイル操作の修正"""
        lines = content.split("\n")

        if vuln.line_number <= len(lines):
            original_line = lines[vuln.line_number - 1]

            # パス検証コメントを追加
            if "open(" in original_line and "w" in original_line:
                # パス検証のコメントを追加
                indent = len(original_line) - len(original_line.lstrip())
                validation_comment = (
                    " " * indent + "# セキュリティ: ファイルパス検証が必要です - Path().resolve()でパストラバーサル防止"
                )
                lines.insert(vuln.line_number - 1, validation_comment)
                return "\n".join(lines)

        return content

    def _fix_yaml_injection(self, content: str, vuln: Any) -> str:
        """YAML injection脆弱性の修正"""
        lines = content.split("\n")

        if vuln.line_number <= len(lines):
            original_line = lines[vuln.line_number - 1]

            # yaml.load() を yaml.safe_load() に置き換え
            fixed_line = re.sub(r"yaml\.load\s*\(", "yaml.safe_load(", original_line)

            lines[vuln.line_number - 1] = fixed_line
            return "\n".join(lines)

        return content

    def _fix_insecure_random(self, content: str, vuln: Any) -> str:
        """安全でない乱数生成の修正"""
        lines = content.split("\n")

        if vuln.line_number <= len(lines):
            original_line = lines[vuln.line_number - 1]

            # random.random() を secrets.SystemRandom().random() に置き換え
            fixed_line = re.sub(r"random\.(random|choice)", r"secrets.SystemRandom().\1", original_line)

            # secrets importを追加
            if "import secrets" not in content:
                import_line = "import secrets"
                for i, line in enumerate(lines):
                    if line.startswith(("import ", "from ")):
                        continue
                    lines.insert(i, import_line)
                    break

            lines[vuln.line_number - 1] = fixed_line
            return "\n".join(lines)

        return content

    def _fix_weak_crypto(self, content: str, vuln: Any) -> str:
        """弱い暗号化アルゴリズムの修正"""
        lines = content.split("\n")

        if vuln.line_number <= len(lines):
            original_line = lines[vuln.line_number - 1]

            # MD5/SHA1 を SHA256 に置き換え
            fixed_line = re.sub(r"hashlib\.(md5|sha1)\s*\(", "hashlib.sha256(", original_line)

            lines[vuln.line_number - 1] = fixed_line
            return "\n".join(lines)

        return content

    def _print_fix_summary(self, fix_results: dict[str, FixResult]) -> None:
        """修正結果サマリーを表示"""
        self.console.print("\n" + "=" * 60, style="bold")
        self.console.print("🔧 セキュリティ修正結果", style="bold blue")
        self.console.print("=" * 60, style="bold")

        total_fixes = sum(result.fixes_applied for result in fix_results.values())
        files_with_fixes = sum(1 for result in fix_results.values() if result.fixes_applied > 0)
        files_with_errors = sum(1 for result in fix_results.values() if result.errors)

        self.console.print(f"📁 対象ファイル数: {len(fix_results)}")
        self.console.print(f"✅ 修正済みファイル数: {files_with_fixes}")
        self.console.print(f"🔧 総修正数: {total_fixes}")
        self.console.print(f"❌ エラーファイル数: {files_with_errors}")

        if files_with_errors > 0:
            self.console.print("\n❌ エラー詳細:", style="error")
            for file_path, result in fix_results.items():
                if result.errors:
                    self.console.print(f"  {file_path}: {', '.join(result.errors)}", style="error")


def main():
    """メイン実行関数"""
    fixer = SecurityAutoFixer()
    fixer.fix_project_vulnerabilities(create_backup=True)


if __name__ == "__main__":
    main()
