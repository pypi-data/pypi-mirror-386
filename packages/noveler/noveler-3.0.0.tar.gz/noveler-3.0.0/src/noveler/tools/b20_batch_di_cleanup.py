"""Tools.b20_batch_di_cleanup
Where: CLI tool cleaning up DI bindings for B20 compliance.
What: Scans and refactors dependency injection registrations to meet standards.
Why: Streamlines maintenance of DI configuration for large projects.
"""

from noveler.presentation.shared.shared_utilities import console

"B20準拠DI変換後のクリーンアップツール\n\n変換後のファイルの構文エラーやインポートエラーを修正する。\n"
import ast
import re
from pathlib import Path

from noveler.infrastructure.adapters.console_service_adapter import get_console_service


class B20PostConverter:
    """B20変換後のクリーンアップを行う"""

    def __init__(self, use_cases_dir: Path) -> None:
        self.use_cases_dir = use_cases_dir
        self.fixed_files = []
        self.error_files = []

    def fix_file(self, file_path: Path) -> bool:
        """単一ファイルの構文エラーを修正"""
        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content
            try:
                ast.parse(content)
            except SyntaxError as e:
                self.console_service.print(f"🔧 Fixing syntax errors in {file_path.name}: {e}")
                content = self._fix_syntax_errors(content)
            content = self._fix_code_quality(content)
            content = self._fix_unit_of_work_usage(content)
            if content != original_content:
                # バッチ書き込みを使用
                file_path.write_text(content, encoding="utf-8")
                self.console_service.print(f"✅ Fixed: {file_path.name}")
                self.fixed_files.append(file_path)
                return True
            self.console_service.print(f"✨ No issues found: {file_path.name}")
            return True
        except Exception as e:
            self.console_service.print(f"❌ Failed to fix {file_path.name}: {e}")
            self.error_files.append((file_path, str(e)))
            return False

    def _fix_syntax_errors(self, content: str) -> str:
        """構文エラーの修正"""
        lines = content.split("\n")
        fixed_lines = []
        for line in lines:
            line = re.sub("\\bself\\.logger_service\\b", "self._logger_service", line)
            line = re.sub("\\bself\\.episode_repository\\b", "self._unit_of_work.episode_repository", line)
            line = re.sub("\\bself\\.project_repository\\b", "self._unit_of_work.project_repository", line)
            line = re.sub("\\bself\\.quality_check_repository\\b", "self._unit_of_work.quality_check_repository", line)
            if "def create_with_di(" in line:
                line = line.replace(
                    "CreateEpisodeUseCase(episode_repository, project_repository)",
                    "use_case_factory.create_episode_use_case()",
                )
            fixed_lines.append(line)
        return "\n".join(fixed_lines)

    def _fix_code_quality(self, content: str) -> str:
        """コード品質の修正"""
        content = re.sub("\\s*# 依存関係をコンストラクタ注入\\s*\\n", "", content)
        content = re.sub("\\s*episode_repository: EpisodeRepository\\s*\\n", "", content)
        content = re.sub("\\s*project_repository: ProjectRepository\\s*\\n", "", content)
        content = re.sub("\\s*logger_service: ILoggerService\\s*\\n", "", content)
        content = re.sub("\\s*quality_repository: QualityRepository \\| None = None\\s*\\n", "", content)
        content = content.replace("Phase 5: 統一DIパターン適用版", "B20準拠DIパターン")
        content = content.replace("- 依存関係をコンストラクタ注入", "- logger_service, unit_of_work 注入")
        return content.replace("- create_with_di()メソッドによるDI解決", "- Unit of Work経由でリポジトリアクセス")

    def _fix_unit_of_work_usage(self, content: str) -> str:
        """Unit of Work使用法の修正"""
        lines = content.split("\n")
        fixed_lines = []
        in_execute_method = False
        has_uow_transaction = False
        for i, line in enumerate(lines):
            if "def execute(" in line or "async def execute(" in line:
                in_execute_method = True
                has_uow_transaction = False
            if in_execute_method and "with self._unit_of_work.transaction():" in line:
                has_uow_transaction = True
            if (
                in_execute_method
                and "try:" in line
                and (not has_uow_transaction)
                and (i + 1 < len(lines))
                and ("self._logger_service.info(" in lines[i + 1])
            ):
                indent = " " * (len(line) - len(line.lstrip()))
                fixed_lines.append(line.replace("try:", "with self._unit_of_work.transaction():"))
                fixed_lines.append(f"{indent}    try:")
                continue
            if in_execute_method and line.strip() and (not line.startswith(" ")):
                in_execute_method = False
            fixed_lines.append(line)
        return "\n".join(fixed_lines)

    def batch_cleanup(self) -> tuple[int, int]:
        """全変換済みファイルのクリーンアップ"""
        backup_files = list(self.use_cases_dir.glob("*.py.backup"))
        if not backup_files:
            use_case_files = list(self.use_cases_dir.glob("*use_case.py"))
            self.console_service.print(f"Checking {len(use_case_files)} use case files for post-conversion fixes")
        else:
            use_case_files = [f.with_suffix("") for f in backup_files]
            self.console_service.print(f"Found {len(backup_files)} backup files, checking converted files")
        success_count = 0
        for file_path in use_case_files[:15]:
            if self.fix_file(file_path):
                success_count += 1
        return (success_count, len(use_case_files[:15]))

    def generate_report(self) -> str:
        """クリーンアップ結果のレポート生成"""
        len(self.fixed_files) + len(self.error_files)
        success = len(self.fixed_files)
        failed = len(self.error_files)
        report = (
            f"B20準拠DI変換後クリーンアップ結果\n{'=' * 27}\n"
            f"修正ファイル数: {success}\n"
            f"修正失敗: {failed}\n"
            f"成功率: {(success / (success + failed) * 100 if success + failed > 0 else 100):.1f}%\n\n修正されたファイル:\n"
        )
        for file_path in self.fixed_files:
            report += f"- {file_path.name}\n"
        if self.error_files:
            report += "\n修正失敗ファイル:\n"
            for file_path, error in self.error_files:
                report += f"- {file_path.name}: {error}\n"
        return report


def main():
    """メイン処理"""
    use_cases_dir = Path(__file__).parent.parent / "application" / "use_cases"
    cleaner = B20PostConverter(use_cases_dir)
    get_console_service()
    console.print("B20準拠DI変換後クリーンアップツール")
    console.print("=" * 50)
    (success_count, total_count) = cleaner.batch_cleanup()
    console.print("\n" + "=" * 50)
    console.print(cleaner.generate_report())
    console.print(f"\nクリーンアップ完了: {success_count}/{total_count} ファイル")


if __name__ == "__main__":
    main()
