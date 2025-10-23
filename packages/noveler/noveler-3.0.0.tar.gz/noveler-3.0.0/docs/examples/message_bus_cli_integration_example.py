#!/usr/bin/env python3
"""Message Bus統合CLI実装例

SPEC-901-DDD-REFACTORING対応:
- 既存CLIからMessage Bus経由での処理実行例
- DI統合とBootstrap処理の実装例
- エラーハンドリングと統合テストの例

使用例:
    python examples/message_bus_cli_integration_example.py generate-plot --episode 1
    python examples/message_bus_cli_integration_example.py validate-plot plot.md
    python examples/message_bus_cli_integration_example.py test-integration
"""

import argparse
import asyncio
import sys
from pathlib import Path

# プロジェクトルートを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from noveler.application.unit_of_work import AbstractUnitOfWork
from noveler.presentation.cli_message_bus_facade import create_cli_message_bus_facade


# テスト用実装クラス
class ExampleUnitOfWork(AbstractUnitOfWork):
    """サンプル用UnitOfWork実装"""

    def __init__(self):
        super().__init__()
        self.committed = False
        self.rolled_back = False

    def _commit(self):
        self.committed = True
        print("  UoW: コミット実行完了")

    def rollback(self):
        self.rolled_back = True
        print("  UoW: ロールバック実行完了")


class MockLogger:
    """サンプル用ロガー実装"""

    def info(self, message: str) -> None:
        print(f"[INFO] {message}")

    def warning(self, message: str) -> None:
        print(f"[WARNING] {message}")

    def error(self, message: str) -> None:
        print(f"[ERROR] {message}")

    def debug(self, message: str) -> None:
        print(f"[DEBUG] {message}")


class MockConsole:
    """サンプル用コンソールサービス実装"""

    def info(self, message: str) -> None:
        print(f"💬 {message}")

    def success(self, message: str) -> None:
        print(f"✅ {message}")

    def warning(self, message: str) -> None:
        print(f"⚠️ {message}")

    def error(self, message: str) -> None:
        print(f"❌ {message}")


class MockConfig:
    """サンプル用設定サービス実装"""


class MockPath:
    """サンプル用パスサービス実装"""

    def get_project_root(self) -> Path:
        return Path.cwd()


def create_sample_services():
    """サンプル用サービス作成"""
    return {
        "logger_service": MockLogger(),
        "console_service": MockConsole(),
        "unit_of_work": ExampleUnitOfWork(),
        "config_service": MockConfig(),
        "path_service": MockPath()
    }


def demo_plot_generation(facade, args):
    """プロット生成デモ"""
    print("\n=== プロット生成デモ ===")

    result = facade.generate_plot(
        episode_number=args.episode,
        chapter_title=args.title,
        use_ai=args.use_ai,
        quality_check=True,
        auto_save=False
    )

    print(f"実行結果: {result}")

    if result["status"] == "success":
        plot_result = result["result"]
        print("\n生成されたプロット内容:")
        print("-" * 40)
        print(plot_result.content)
        print("-" * 40)


def demo_plot_validation(facade, args):
    """プロット品質チェックデモ"""
    print("\n=== プロット品質チェックデモ ===")

    plot_file = Path(args.plot_file)
    if not plot_file.exists():
        # テスト用プロットファイル作成
        test_content = """# テストプロット

## タイトル
サンプルストーリー

## 基本構成
- ジャンル: ファンタジー
- 目標文字数: 2000文字

## プロット内容
主人公は魔法学校に入学する。
そこで友達と出会い、冒険が始まる。
最終的に世界を救うことになる。
"""
        plot_file.write_text(test_content, encoding="utf-8")
        print(f"テスト用プロットファイルを作成しました: {plot_file}")

    result = facade.validate_plot(
        plot_file_path=str(plot_file),
        quality_criteria={
            "min_length": 100,
            "require_title": True,
            "require_structure": True
        }
    )

    print(f"品質チェック結果: {result}")


async def demo_async_plot_generation(facade, args):
    """非同期プロット生成デモ"""
    print("\n=== 非同期プロット生成デモ ===")

    result = await facade.generate_plot_async(
        episode_number=args.episode,
        chapter_title=f"非同期生成: {args.title or 'デフォルトタイトル'}",
        use_ai_enhancement=args.use_ai
    )

    print(f"非同期実行結果: {result}")


def demo_integration_test(facade, args):
    """統合テストデモ"""
    print("\n=== 統合テストデモ ===")

    # 統合状況表示
    facade.show_integration_status()

    # Message Bus接続テスト
    print("\nMessage Bus接続テスト実行中...")
    connection_ok = facade.test_message_bus_connection()

    if connection_ok:
        print("✅ Message Bus統合テスト成功")
    else:
        print("❌ Message Bus統合テスト失敗")

    # パフォーマンスメトリクス表示
    print("\nパフォーマンスメトリクス取得中...")
    metrics_result = facade.get_message_bus_metrics()

    if metrics_result["status"] == "success":
        print("メトリクス取得成功")
    else:
        print(f"メトリクス取得エラー: {metrics_result.get('error', '不明')}")


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="Message Bus統合CLI実装例",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="実行するコマンド")

    # プロット生成コマンド
    plot_gen_parser = subparsers.add_parser("generate-plot", help="プロット生成")
    plot_gen_parser.add_argument("--episode", type=int, default=1, help="エピソード番号")
    plot_gen_parser.add_argument("--title", type=str, help="チャプタータイトル")
    plot_gen_parser.add_argument("--use-ai", action="store_true", default=True, help="AI使用")

    # プロット品質チェックコマンド
    validate_parser = subparsers.add_parser("validate-plot", help="プロット品質チェック")
    validate_parser.add_argument("plot_file", help="プロットファイルパス")

    # 非同期プロット生成コマンド
    async_gen_parser = subparsers.add_parser("generate-plot-async", help="非同期プロット生成")
    async_gen_parser.add_argument("--episode", type=int, default=1, help="エピソード番号")
    async_gen_parser.add_argument("--title", type=str, help="チャプタータイトル")
    async_gen_parser.add_argument("--use-ai", action="store_true", default=True, help="AI使用")

    # 統合テストコマンド
    subparsers.add_parser("test-integration", help="統合テスト実行")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return None

    # サービス初期化
    print("🚀 Message Bus統合CLI実装例")
    print("=" * 50)

    try:
        services = create_sample_services()

        # CLIファサード作成
        facade = create_cli_message_bus_facade(**services)

        print("✅ CLIファサード初期化完了")

        # コマンド実行
        if args.command == "generate-plot":
            demo_plot_generation(facade, args)

        elif args.command == "validate-plot":
            demo_plot_validation(facade, args)

        elif args.command == "generate-plot-async":
            asyncio.run(demo_async_plot_generation(facade, args))

        elif args.command == "test-integration":
            demo_integration_test(facade, args)

        print("\n🎉 実行完了")

    except Exception as e:
        print(f"\n❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
