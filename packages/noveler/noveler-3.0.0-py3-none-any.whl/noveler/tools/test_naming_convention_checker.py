"""Tools.test_naming_convention_checker
Where: Tool checking test naming conventions.
What: Ensures tests follow agreed naming patterns.
Why: Maintains readability and consistency in test suites.
"""

import argparse
import ast
import re
from pathlib import Path

from noveler.presentation.shared.shared_utilities import console

"テスト命名規則チェッカー\n\nテスト設計ガイドラインに準拠した命名規則をチェック・修正するツール\n"


class TestNamingConventionChecker:
    """テスト命名規則チェッカー"""

    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path or Path("noveler/tests")
        self.violations: list[tuple[str, int, str, str]] = []

    def check_all_test_files(self) -> dict[str, list[tuple[int, str, str]]]:
        """全テストファイルの命名規則をチェック"""
        violations_by_file = {}
        for test_file in self.base_path.rglob("test_*.py"):
            violations = self.check_file(test_file)
            if violations:
                violations_by_file[str(test_file)] = violations
        return violations_by_file

    def check_file(self, file_path: Path) -> list[tuple[int, str, str]]:
        """単一ファイルの命名規則をチェック"""
        violations = []
        try:
            with file_path.Path("r").open(encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    violation = self._check_method_name(node.name, node.lineno)
                    if violation:
                        violations.append(violation)
        except Exception as e:
            console.print(f"エラー: {file_path} の解析中にエラーが発生しました: {e}")
        return violations

    def _check_method_name(self, method_name: str, line_no: int) -> tuple[int, str, str] | None:
        """メソッド名の命名規則をチェック"""
        japanese_pattern = "[ひらがなカタカナ漢字]"
        if re.search(japanese_pattern, method_name):
            suggestion = self._suggest_english_name(method_name)
            return (line_no, method_name, suggestion)
        generic_names = ["test_unnamed", "test_done", "test_process"]
        if method_name in generic_names:
            suggestion = self._suggest_descriptive_name(method_name)
            return (line_no, method_name, suggestion)
        return None

    def _suggest_english_name(self, japanese_name: str) -> str:
        """日本語メソッド名の英語候補を提案"""
        conversion_map = {
            "作成": "create",
            "生成": "generate",
            "削除": "delete",
            "更新": "update",
            "取得": "get",
            "検索": "search",
            "チェック": "check",
            "確認": "verify",
            "検証": "validate",
            "実行": "execute",
            "処理": "process",
            "分析": "analyze",
            "計算": "calculate",
            "保存": "save",
            "読み込み": "load",
            "初期化": "initialize",
            "設定": "configure",
            "登録": "register",
            "一覧": "list",
            "複数": "multiple",
            "単一": "single",
            "基本": "basic",
            "詳細": "detailed",
            "簡単": "simple",
            "複雑": "complex",
            "正常": "success",
            "異常": "error",
            "失敗": "failure",
            "成功": "success",
            "エラー": "error",
            "警告": "warning",
            "情報": "info",
            "デバッグ": "debug",
        }
        result = japanese_name
        for jp, en in conversion_map.items():
            result = result.replace(jp, en)
        if re.search("[ひらがなカタカナ漢字]", result):
            base_name = result.replace("test_", "")
            return f"test_{base_name}_functionality"
        return result

    def _suggest_descriptive_name(self, generic_name: str) -> str:
        """一般的すぎる名前の改善案を提案"""
        suggestions = {
            "test_unnamed": "test_specific_functionality",
            "test_done": "test_completion_workflow",
            "test_process": "test_processing_logic",
        }
        return suggestions.get(generic_name, f"{generic_name}_with_specific_case")

    def generate_report(self, violations_by_file: dict[str, list[tuple[int, str, str]]]) -> str:
        """違反レポートを生成"""
        if not violations_by_file:
            return "✅ 全てのテストファイルが命名規則に準拠しています。"
        report = ["🚨 テスト命名規則違反レポート", "=" * 50, ""]
        total_violations = sum(len(violations) for violations in violations_by_file.values())
        report.append(f"📊 合計違反数: {total_violations}")
        report.append(f"📁 違反ファイル数: {len(violations_by_file)}")
        report.append("")
        for file_path, violations in violations_by_file.items():
            relative_path = Path(file_path).relative_to(Path.cwd())
            report.append(f"📄 {relative_path}")
            report.append("-" * len(str(relative_path)))
            for line_no, current_name, suggested_name in violations:
                report.append(f"  行 {line_no}: {current_name}")
                report.append(f"  提案: {suggested_name}")
                report.append("")
        report.append("🔧 修正方法:")
        report.append("1. 上記の提案に従ってメソッド名を変更")
        report.append("2. docstringで日本語の説明を追加")
        report.append("3. @pytest.mark.spec マーカーの追加")
        return "\n".join(report)

    def fix_file(self, file_path: Path, dry_run: bool = True) -> bool:
        """ファイルの命名規則違反を自動修正"""
        violations = self.check_file(file_path)
        if not violations:
            return False
        try:
            with file_path.Path("r").open(encoding="utf-8") as f:
                content = f.read()
            modified_content = content
            violations.sort(key=lambda x: x[0], reverse=True)
            for _line_no, current_name, suggested_name in violations:
                pattern = f"def {re.escape(current_name)}\\("
                replacement = f"def {suggested_name}("
                modified_content = re.sub(pattern, replacement, modified_content)
            if not dry_run:
                with file_path.Path("w").open(encoding="utf-8") as f:
                    f.write(modified_content)
                console.print(f"✅ 修正完了: {file_path}")
            else:
                console.print(f"🔍 修正プレビュー: {file_path}")
                console.print(f"   {len(violations)}個の違反を修正予定")
            return True
        except Exception as e:
            console.print(f"❌ 修正エラー: {file_path} - {e}")
            return False


def main():
    """メイン実行関数"""

    parser = argparse.ArgumentParser(description="テスト命名規則チェッカー")
    parser.add_argument("--fix", action="store_true", help="違反を自動修正")
    parser.add_argument("--dry-run", action="store_true", default=True, help="修正のプレビューのみ")
    parser.add_argument("--path", type=Path, help="チェック対象パス")
    parser.add_argument("--file", type=Path, help="単一ファイルをチェック")
    args = parser.parse_args()
    checker = TestNamingConventionChecker(args.path)
    if args.file:
        violations = checker.check_file(args.file)
        if violations:
            console.print(f"🚨 {args.file} で {len(violations)}個の違反を発見:")
            for line_no, current_name, suggested_name in violations:
                console.print(f"  行 {line_no}: {current_name} → {suggested_name}")
            if args.fix:
                checker.fix_file(args.file, dry_run=args.dry_run)
        else:
            console.print(f"✅ {args.file} は命名規則に準拠しています")
    else:
        violations_by_file = checker.check_all_test_files()
        report = checker.generate_report(violations_by_file)
        console.print(report)
        if args.fix and violations_by_file:
            console.print("\n🔧 自動修正を開始...")
            fixed_count = 0
            for file_path in violations_by_file:
                if checker.fix_file(Path(file_path), dry_run=args.dry_run):
                    fixed_count += 1
            console.print(f"\n✅ {fixed_count}個のファイルを修正しました")


if __name__ == "__main__":
    main()
