"""B20準拠DIパターンバッチチェッカー

既存のユースケースファイルでB20準拠DI適用が必要なファイルを検出する。
"""
import ast
from pathlib import Path

from noveler.presentation.shared.shared_utilities import console


class B20DIChecker:
    """B20準拠DIパターンのチェックを行う"""

    def __init__(self, use_cases_dir: Path) -> None:
        self.use_cases_dir = use_cases_dir
        self.results: dict[str, dict] = {}

    def check_file(self, file_path: Path) -> dict:
        """ファイルのB20準拠状況をチェック"""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            use_case_classes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if any("UseCase" in base.id if hasattr(base, "id") else "UseCase" in getattr(base, "attr", "") if hasattr(base, "attr") else False for base in node.bases):
                        use_case_classes.append(node)
            if not use_case_classes:
                return {"status": "not_use_case", "needs_update": False, "reason": "No UseCase class found"}
            for class_node in use_case_classes:
                for method in class_node.body:
                    if isinstance(method, ast.FunctionDef) and method.name == "__init__":
                        return self._check_init_method(method)
            return {"status": "no_init", "needs_update": True, "reason": "No __init__ method found"}
        except Exception as e:
            return {"status": "error", "needs_update": False, "reason": f"Parse error: {e}"}

    def _check_init_method(self, init_method: ast.FunctionDef) -> dict:
        """__init__メソッドがB20準拠かチェック"""
        args = [arg.arg for arg in init_method.args.args[1:]]
        has_logger_service = "logger_service" in args
        has_unit_of_work = "unit_of_work" in args
        has_repository_args = any("repository" in arg for arg in args)
        has_old_pattern = any(arg in ["episode_repository", "project_repository", "quality_check_repository"] for arg in args)
        if has_logger_service and has_unit_of_work:
            return {"status": "b20_compliant", "needs_update": False, "reason": "Already B20 compliant"}
        if has_old_pattern or has_repository_args:
            return {"status": "old_pattern", "needs_update": True, "reason": f"Old pattern detected: {args}"}
        return {"status": "unknown_pattern", "needs_update": True, "reason": f"Unknown pattern: {args}"}

    def scan_all_files(self) -> tuple[list[Path], dict[str, dict]]:
        """全ユースケースファイルをスキャン"""
        use_case_files = list(self.use_cases_dir.glob("*use_case.py"))
        needs_update = []
        for file_path in use_case_files:
            result = self.check_file(file_path)
            self.results[str(file_path)] = result
            if result["needs_update"]:
                needs_update.append(file_path)
        return (needs_update, self.results)

    def generate_report(self) -> str:
        """チェック結果のレポート生成"""
        total = len(self.results)
        compliant = sum(1 for r in self.results.values() if r["status"] == "b20_compliant")
        needs_update = sum(1 for r in self.results.values() if r["needs_update"])
        report = f"B20準拠DIパターンチェック結果\n=====================================\n総ファイル数: {total}\nB20準拠: {compliant}\n更新必要: {needs_update}\n準拠率: {compliant / total * 100:.1f}%\n\n更新が必要なファイル:\n"
        for (file_path, result) in self.results.items():
            if result["needs_update"]:
                filename = Path(file_path).name
                report += f"- {filename}: {result['reason']}\n"
        return report

def main():
    """メイン処理"""
    use_cases_dir = Path(__file__).parent.parent / "application" / "use_cases"
    checker = B20DIChecker(use_cases_dir)
    (needs_update, all_results) = checker.scan_all_files()
    console.print(checker.generate_report())
    console.print(f"\n更新対象ファイル一覧 ({len(needs_update)}件):")
    for file_path in needs_update:
        console.print(f"  {file_path.name}")
if __name__ == "__main__":
    main()
