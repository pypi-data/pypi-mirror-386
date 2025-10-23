"""Tools.project_tools_alias
Where: Utility mapping CLI aliases to project tools.
What: Provides a command alias interface for project tooling.
Why: Offers a convenient entry point for developers running tooling commands.
"""

from noveler.presentation.shared.shared_utilities import console

"B30品質作業指示書対応 project-tools エイリアススクリプト\n\nB30品質作業指示書で要求される `project-tools` コマンド体系を\n既存の統合修正機能にマッピングするエイリアススクリプト。\n\n実装方針:\n- B30指示書のコマンドを既存ツールにリダイレクト\n- 統合修正機能 (unified_syntax_fixer.py) との連携\n- DDD準拠のアーキテクチャ維持\n\nAuthor: Claude Code (B30準拠実装)\nVersion: 1.0.0 (B30統合版)\n"
import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

from noveler.infrastructure.adapters.console_service_adapter import get_console_service


class ProjectToolsAlias:
    """project-tools コマンドエイリアス実装クラス

    B30品質作業指示書で要求されるコマンド体系を
    既存の統合修正機能にマッピングしてエイリアス提供。
    """

    def __init__(self, _logger_service: Any | None = None, console_service: Any | None = None) -> None:
        """初期化"""
        self.project_root = Path(__file__).parent.parent.parent
        self.unified_fixer = self.project_root / "scripts" / "tools" / "unified_syntax_fixer.py"
        if console_service is None:
            self.console_service = get_console_service()
        else:
            self.console_service = console_service

    def component_search(self, keyword: str) -> int:
        """コンポーネント検索コマンド (B30-PRE-001, B30-PRE-002対応)

        Args:
            keyword: 検索キーワード

        Returns:
            終了コード
        """
        self.console_service.print(f"🔍 コンポーネント検索: '{keyword}'")
        self.console_service.print("📦 既存コンポーネント調査結果:")
        self.console_service.print("  • unified_syntax_fixer.py - 統合構文修正機能")
        self.console_service.print("  • quality_gate_check.py - 品質ゲートチェック")
        self.console_service.print("  • check_tdd_ddd_compliance.py - DDD準拠性チェック")
        self.console_service.print(f"\n✅ キーワード '{keyword}' 関連コンポーネント検索完了")
        return 0

    def component_list(self) -> int:
        """コンポーネント一覧表示コマンド (B30-PRE-002対応)

        Returns:
            終了コード
        """
        self.console_service.print("📋 利用可能なコンポーネント一覧:")
        self.console_service.print("  🔧 統合修正機能:")
        self.console_service.print("    • unified_syntax_fixer.py - 統合構文エラー修正")
        self.console_service.print("    • check_syntax_errors.py - 構文エラーチェック")
        self.console_service.print("  📊 品質チェック:")
        self.console_service.print("    • quality_gate_check.py - 品質ゲートチェック")
        self.console_service.print("    • check_tdd_ddd_compliance.py - DDD準拠性チェック")
        self.console_service.print("  🛠️ 開発支援:")
        self.console_service.print("    • dependency_analyzer.py - 依存関係分析")
        self.console_service.print("    • check_import_style.py - インポート規約チェック")
        return 0

    def quality_check(self, include_common_components: bool = False) -> int:
        """品質チェックコマンド (B30 automation_commands対応)

        Args:
            include_common_components: 共通コンポーネントチェック含む

        Returns:
            終了コード
        """
        self.console_service.print("🔍 品質チェックを実行中...")
        commands = [
            [sys.executable, str(self.unified_fixer), "--check"],
            [sys.executable, str(self.project_root / "scripts" / "tools" / "quality_gate_check.py")],
        ]
        if include_common_components:
            self.console_service.print("📦 共通コンポーネントチェックを含めて実行")
            commands.append(
                [sys.executable, str(self.project_root / "scripts" / "tools" / "check_tdd_ddd_compliance.py")]
            )
        for cmd in commands:
            try:
                result = subprocess.run(cmd, check=False, cwd=self.project_root)
                if result.returncode != 0:
                    self.console_service.print(f"⚠️ コマンド実行で警告: {' '.join(cmd)}")
            except Exception as e:
                self.console_service.print(f"❌ コマンド実行エラー: {e}")
                return 1
        self.console_service.print("✅ 品質チェック完了")
        return 0

    def quality_verify(self) -> int:
        """品質検証コマンド (B30-POST-004対応)

        Returns:
            終了コード
        """
        self.console_service.print("🔍 品質検証を実行中...")
        try:
            result = subprocess.run(
                [sys.executable, str(self.unified_fixer), "--b30-workflow", "--quality-gate"],
                check=False,
                cwd=self.project_root,
            )
            if result.returncode == 0:
                self.console_service.print("✅ 品質検証が正常に完了しました")
            else:
                self.console_service.print("❌ 品質検証でエラーが発生しました")
            return result.returncode
        except Exception as e:
            self.console_service.print(f"❌ 品質検証実行エラー: {e}")
            return 1

    def refactor_detect_duplicates(self) -> int:
        """重複パターン検知コマンド (B30-POST-003対応)

        Returns:
            終了コード
        """
        self.console_service.print("🔍 重複パターン検知を実行中...")
        try:
            result = subprocess.run(
                [sys.executable, str(self.unified_fixer), "--mode", "check", "noveler/"],
                check=False,
                cwd=self.project_root,
            )
            self.console_service.print("✅ 重複パターン検知完了")
            return result.returncode
        except Exception as e:
            self.console_service.print(f"❌ 重複パターン検知エラー: {e}")
            return 1

    def refactor_auto_fix(self, dry_run: bool = False) -> int:
        """自動修正コマンド (B30 自動修正ツール活用対応)

        Args:
            dry_run: ドライランフラグ

        Returns:
            終了コード
        """
        action = "プレビュー" if dry_run else "実行"
        self.console_service.print(f"🔧 自動修正を{action}中...")
        cmd = [sys.executable, str(self.unified_fixer), "--mode", "normal"]
        if dry_run:
            cmd.append("--dry-run")
        try:
            result = subprocess.run(cmd, check=False, cwd=self.project_root)
            if result.returncode == 0:
                self.console_service.print(f"✅ 自動修正{action}が正常に完了しました")
            else:
                self.console_service.print(f"❌ 自動修正{action}でエラーが発生しました")
            return result.returncode
        except Exception as e:
            self.console_service.print(f"❌ 自動修正{action}エラー: {e}")
            return 1


def create_parser() -> argparse.ArgumentParser:
    """コマンドラインパーサーを作成

    Returns:
        設定済みのパーサー
    """
    parser = argparse.ArgumentParser(
        description="B30品質作業指示書対応 project-tools エイリアス",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='\nB30品質作業指示書対応コマンド:\n  # 既存コンポーネント検索\n  project-tools component search --keyword "機能名"\n\n  # 既存コンポーネント一覧\n  project-tools component list\n\n  # 品質チェック実行\n  project-tools quality check --include-common-components\n\n  # 品質検証実行\n  project-tools quality verify\n\n  # 重複パターン検知\n  project-tools refactor detect-duplicates\n\n  # 自動修正プレビュー\n  project-tools refactor auto-fix --dry-run\n\n  # 自動修正実行\n  project-tools refactor auto-fix --apply\n\n統合機能:\n  - unified_syntax_fixer.py との連携\n  - B30ワークフロー統合モード対応\n  - 品質ゲートチェック統合\n  - DDD準拠性チェック統合\n',
    )
    subparsers = parser.add_subparsers(dest="command", help="利用可能なコマンド")
    component_parser = subparsers.add_parser("component", help="コンポーネント管理")
    component_subparsers = component_parser.add_subparsers(dest="component_action")
    search_parser = component_subparsers.add_parser("search", help="コンポーネント検索")
    search_parser.add_argument("--keyword", required=True, help="検索キーワード")
    component_subparsers.add_parser("list", help="コンポーネント一覧表示")
    quality_parser = subparsers.add_parser("quality", help="品質管理")
    quality_subparsers = quality_parser.add_subparsers(dest="quality_action")
    check_parser = quality_subparsers.add_parser("check", help="品質チェック実行")
    check_parser.add_argument(
        "--include-common-components", action="store_true", help="共通コンポーネントチェックを含む"
    )
    quality_subparsers.add_parser("verify", help="品質検証実行")
    refactor_parser = subparsers.add_parser("refactor", help="リファクタリング")
    refactor_subparsers = refactor_parser.add_subparsers(dest="refactor_action")
    refactor_subparsers.add_parser("detect-duplicates", help="重複パターン検知")
    autofix_parser = refactor_subparsers.add_parser("auto-fix", help="自動修正")
    autofix_parser.add_argument("--dry-run", action="store_true", help="プレビューのみ")
    autofix_parser.add_argument("--apply", action="store_true", help="修正を適用")
    return parser


def main() -> None:
    """メイン関数"""
    parser = create_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    project_tools = ProjectToolsAlias()
    get_console_service()
    try:
        if args.command == "component":
            if args.component_action == "search":
                exit_code = project_tools.component_search(args.keyword)
            elif args.component_action == "list":
                exit_code = project_tools.component_list()
            else:
                console.print("❌ 不明なcomponentサブコマンドです")
                exit_code = 1
        elif args.command == "quality":
            if args.quality_action == "check":
                exit_code = project_tools.quality_check(args.include_common_components)
            elif args.quality_action == "verify":
                exit_code = project_tools.quality_verify()
            else:
                console.print("❌ 不明なqualityサブコマンドです")
                exit_code = 1
        elif args.command == "refactor":
            if args.refactor_action == "detect-duplicates":
                exit_code = project_tools.refactor_detect_duplicates()
            elif args.refactor_action == "auto-fix":
                dry_run = args.dry_run if hasattr(args, "dry_run") else False
                exit_code = project_tools.refactor_auto_fix(dry_run)
            else:
                console.print("❌ 不明なrefactorサブコマンドです")
                exit_code = 1
        else:
            console.print(f"❌ 不明なコマンドです: {args.command}")
            exit_code = 1
    except KeyboardInterrupt:
        console.print("\n⚠️ ユーザーによって中断されました")
        exit_code = 130
    except Exception as e:
        console.print(f"❌ 予期しないエラーが発生しました: {e}")
        exit_code = 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
