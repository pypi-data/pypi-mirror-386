"""Infrastructure.testing.fast_test
Where: Infrastructure module bundling fast test utilities.
What: Provides shortcuts to run targeted test suites and diagnostics quickly.
Why: Speeds up local testing workflows for developers.
"""

from noveler.presentation.shared.shared_utilities import console

"高速テスト実行ツール\n\n大規模テストスイートの効率的な実行を支援\n"
import argparse
import subprocess
import sys
import time
from typing import Any


def run_command(cmd: list[str], description: str) -> tuple[bool, float]:
    """コマンドを実行し、結果と実行時間を返す"""
    console.print(f"🚀 {description}")
    console.print(f"   コマンド: {' '.join(cmd)}")
    start_time = time.time()
    try:
        subprocess.run(cmd, check=True, capture_output=False)
        elapsed = time.time() - start_time
        console.print(f"✅ 成功 ({elapsed:.2f}秒)")
        return (True, elapsed)
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        console.print(f"❌ 失敗 ({elapsed:.2f}秒) - 終了コード: {e.returncode}")
        return (False, elapsed)


def main() -> Any:
    parser = argparse.ArgumentParser(description="高速テスト実行ツール")
    parser.add_argument("--unit", action="store_true", help="単体テストのみ実行")
    parser.add_argument("--integration", action="store_true", help="統合テストのみ実行")
    parser.add_argument("--e2e", action="store_true", help="E2Eテストのみ実行")
    parser.add_argument("--domain", action="store_true", help="ドメイン層のみ実行")
    parser.add_argument("--application", action="store_true", help="アプリケーション層のみ実行")
    parser.add_argument("--infrastructure", action="store_true", help="インフラ層のみ実行")
    parser.add_argument("--fast", action="store_true", help="最高速モード(slowテスト除外)")
    parser.add_argument("--parallel", type=int, help="並列実行数を指定")
    parser.add_argument("--coverage", action="store_true", help="カバレッジ測定を有効化")
    parser.add_argument("--maxfail", type=int, default=5, help="最大失敗数")
    parser.add_argument("--lf", action="store_true", help="前回失敗したテストのみ実行")
    parser.add_argument("--ff", action="store_true", help="前回失敗したテストを最初に実行")
    parser.add_argument("--collect-only", action="store_true", help="テスト収集のみ実行")
    args = parser.parse_args()
    cmd = [sys.executable, "-m", "pytest"]
    if args.unit:
        cmd.append("noveler/tests/unit")
    elif args.integration:
        cmd.append("noveler/tests/integration")
    elif args.e2e:
        cmd.append("noveler/tests/e2e")
    elif args.domain:
        cmd.append("noveler/tests/unit/domain")
    elif args.application:
        cmd.append("noveler/tests/unit/application")
    elif args.infrastructure:
        cmd.append("noveler/tests/unit/infrastructure")
    else:
        cmd.append("noveler/tests")
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    else:
        cmd.extend(["-n", "auto"])
    if args.fast:
        cmd.extend(["-m", "not slow"])
        cmd.append("--disable-warnings")
    if args.coverage:
        cmd.extend(["--cov=scripts", "--cov-branch", "--cov-report=term-missing"])
    else:
        cmd.append("--no-cov")
    cmd.extend(["--maxfail", str(args.maxfail)])
    cmd.append("--tb=short")
    if args.lf:
        cmd.append("--lf")
    if args.ff:
        cmd.append("--ff")
    if args.collect_only:
        cmd.append("--collect-only")
    console.print("=" * 60)
    console.print("🧪 高速テスト実行ツール")
    console.print("=" * 60)
    (success, elapsed) = run_command(cmd, "テスト実行")
    console.print("\n" + "=" * 60)
    if success:
        console.print(f"🎉 テスト完了! 総実行時間: {elapsed:.2f}秒")
    else:
        console.print(f"💥 テスト失敗! 総実行時間: {elapsed:.2f}秒")
    console.print("=" * 60)
    if not any([args.unit, args.integration, args.e2e, args.domain, args.application, args.infrastructure]):
        console.print("\n📖 使用例:")
        console.print("  python scripts/tools/fast_test.py --unit --fast      # 単体テスト(高速)")
        console.print("  python scripts/tools/fast_test.py --domain           # ドメイン層のみ")
        console.print("  python scripts/tools/fast_test.py --lf --parallel 4  # 前回失敗分を4並列で")
        console.print("  python scripts/tools/fast_test.py --collect-only     # テスト収集のみ")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
