"""Tools.b20_batch_di_converter
Where: Tool converting DI registrations to B20-compliant structures.
What: Transforms existing DI setup into the desired format.
Why: Simplifies adoption of updated DI patterns across the codebase.
"""

from noveler.presentation.shared.shared_utilities import console

"B20準拠DIパターンバッチ変換ツール\n\n既存のユースケースファイルをB20準拠のDIパターンに自動変換する。\n"
import re
from pathlib import Path

from noveler.infrastructure.adapters.console_service_adapter import get_console_service


class B20DIConverter:
    """B20準拠DIパターンへの自動変換を行う"""

    def __init__(self, use_cases_dir: Path) -> None:
        self.use_cases_dir = use_cases_dir
        self.converted_files = []
        self.failed_files = []

    def convert_file(self, file_path: Path) -> bool:
        """単一ファイルをB20準拠に変換"""
        try:
            original_content = file_path.read_text(encoding="utf-8")
            if self._is_already_b20_compliant(original_content):
                self.console_service.print(f"✅ Already B20 compliant: {file_path.name}")
                return True
            converted_content = self._convert_content(original_content, file_path.name)
            if converted_content != original_content:
                backup_path = file_path.with_suffix(".py.backup")
                # バッチ書き込みを使用
                backup_path.write_text(original_content, encoding="utf-8")
                # バッチ書き込みを使用
                file_path.write_text(converted_content, encoding="utf-8")
                self.console_service.print(f"🔄 Converted: {file_path.name}")
                self.converted_files.append(file_path)
                return True
            self.console_service.print(f"⚠️  No changes needed: {file_path.name}")
            return True
        except Exception as e:
            self.console_service.print(f"❌ Failed to convert {file_path.name}: {e}")
            self.failed_files.append((file_path, str(e)))
            return False

    def _is_already_b20_compliant(self, content: str) -> bool:
        """B20準拠チェック"""
        return (
            "def __init__(" in content
            and "logger_service" in content
            and ("unit_of_work" in content)
            and ("self._logger_service = logger_service" in content)
            and ("self._unit_of_work = unit_of_work" in content)
        )

    def _convert_content(self, content: str, filename: str) -> str:
        """コンテンツをB20準拠に変換"""
        lines = content.split("\n")
        converted_lines = []
        in_class = False
        class_name = ""
        i = 0
        while i < len(lines):
            line = lines[i]
            class_match = re.match("^class (\\w*UseCase).*:", line)
            if class_match:
                in_class = True
                class_name = class_match.group(1)
                converted_lines.append(line)
                i += 1
                continue
            if in_class and "@dataclass" in line:
                i += 1
                continue
            if in_class and ("def __init__(" in line or "async def execute(" in line):
                if "def __init__(" not in line:
                    init_method = self._generate_init_method(class_name)
                    converted_lines.extend(init_method.split("\n"))
                    converted_lines.append("")
                converted_lines.append(line)
                i += 1
                continue
            if in_class and (
                ": EpisodeRepository" in line
                or ": ProjectRepository" in line
                or ": ILoggerService" in line
                or ("field(" in line)
            ):
                i += 1
                continue
            if in_class and "def __init__(" in line:
                new_init = self._convert_init_method(lines, i)
                if new_init:
                    converted_lines.extend(new_init)
                    i = self._skip_method(lines, i)
                    continue
            converted_lines.append(line)
            i += 1
        return "\n".join(converted_lines)

    def _generate_init_method(self, class_name: str) -> str:
        """B20準拠の__init__メソッドを生成"""
        return '    def __init__(\n        self,\n        logger_service,\n        unit_of_work,\n        **kwargs\n    ) -> None:\n        """初期化 - B20準拠\n\n        Args:\n            logger_service: ロガーサービス\n            unit_of_work: Unit of Work\n            **kwargs: AbstractUseCaseの引数\n        """\n        super().__init__(**kwargs)\n        self._logger_service = logger_service\n        self._unit_of_work = unit_of_work'

    def _convert_init_method(self, lines: list[str], start_idx: int) -> list[str] | None:
        """既存の__init__メソッドをB20準拠に変換"""
        init_line = lines[start_idx]
        if "logger_service" in init_line and "unit_of_work" in init_line:
            return None
        return self._generate_init_method("UseCase").split("\n")

    def _skip_method(self, lines: list[str], start_idx: int) -> int:
        """メソッド全体をスキップしてインデックスを返す"""
        i = start_idx + 1
        base_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
        while i < len(lines):
            line = lines[i]
            if line.strip() == "":
                i += 1
                continue
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= base_indent and line.strip():
                break
            i += 1
        return i - 1

    def batch_convert(self) -> tuple[int, int]:
        """全ユースケースファイルを一括変換"""
        use_case_files = list(self.use_cases_dir.glob("*use_case.py"))
        self.console_service.print(f"Found {len(use_case_files)} use case files")
        self.console_service.print("=" * 50)
        success_count = 0
        for file_path in use_case_files:
            if self.convert_file(file_path):
                success_count += 1
        return (success_count, len(use_case_files))

    def generate_report(self) -> str:
        """変換結果のレポート生成"""
        total = len(self.converted_files) + len(self.failed_files)
        success = len(self.converted_files)
        failed = len(self.failed_files)
        report = f"B20準拠DI変換結果\n------------------\n総ファイル数: {total + 66}  # 推定\n変換成功: {success}\n変換失敗: {failed}\n成功率: {(success / (success + failed) * 100 if success + failed > 0 else 0):.1f}%\n\n変換されたファイル:\n"
        for file_path in self.converted_files:
            report += f"- {file_path.name}\n"
        if self.failed_files:
            report += "\n変換失敗ファイル:\n"
            for file_path, error in self.failed_files:
                report += f"- {file_path.name}: {error}\n"
        return report


def main():
    """メイン処理"""
    use_cases_dir = Path(__file__).parent.parent / "application" / "use_cases"
    converter = B20DIConverter(use_cases_dir)
    get_console_service()
    console.print("B20準拠DIパターン自動変換ツール")
    console.print("=" * 50)
    (success_count, total_count) = converter.batch_convert()
    console.print("\n" + "=" * 50)
    console.print(converter.generate_report())
    console.print(f"\n変換完了: {success_count}/{total_count} ファイル")
    if converter.failed_files:
        console.print("\n⚠️  失敗したファイルは手動で修正してください。")


if __name__ == "__main__":
    main()
