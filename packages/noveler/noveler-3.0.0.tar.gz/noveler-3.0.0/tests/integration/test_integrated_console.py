#!/usr/bin/env python3
"""統合コンソールシステムテスト"""

def test_basic_console():
    """基本console.print()テスト"""
    print("=== Test 1: 基本console.print()テスト ===")

    from noveler.presentation.cli.shared_utilities import console

    console.print("✅ 基本console.print()動作OK")
    console.print("[bold green]Rich形式テスト[/bold green]")
    console.print("[blue]🔵[/blue] [yellow]🟡[/yellow] [red]🔴[/red]")


def test_integrated_console():
    """統合コンソールテスト"""
    print("\n=== Test 2: 統合コンソールテスト ===")

    try:
        from noveler.infrastructure.logging.integrated_console import get_integrated_console
        ic = get_integrated_console(__name__)

        print("✅ IntegratedConsole インポート成功")

        # レベル付き出力テスト
        ic.info("情報メッセージテスト")
        ic.success("成功メッセージテスト")
        ic.warning("警告メッセージテスト")
        ic.error("エラーメッセージテスト")
        ic.debug("デバッグメッセージテスト")

        # 構造化出力テスト
        ic.header("構造化出力テスト", style="bold cyan")
        ic.section("セクションテスト")
        ic.progress_start("進行状況テスト開始")
        ic.progress_complete("進行状況テスト完了")

        print("✅ 統合コンソール機能動作OK")

    except Exception as e:
        print(f"❌ 統合コンソールエラー: {e}")


def test_console_log_bridge():
    """ConsoleLogBridgeテスト"""
    print("\n=== Test 3: ConsoleLogBridgeテスト ===")

    try:
        from noveler.infrastructure.logging.console_log_bridge import get_console_log_bridge
        bridge = get_console_log_bridge(__name__)

        print("✅ ConsoleLogBridge インポート成功")

        bridge.print_info("ブリッジ情報テスト")
        bridge.print_success("ブリッジ成功テスト")
        bridge.print_warning("ブリッジ警告テスト")

        print("✅ ConsoleLogBridge機能動作OK")

    except Exception as e:
        print(f"❌ ConsoleLogBridgeエラー: {e}")


def test_fallback():
    """フォールバック機能テスト"""
    print("\n=== Test 4: フォールバック機能テスト ===")

    # 基本consoleFallback
    try:
        from noveler.presentation.cli.shared_utilities import console
        console.print("✅ フォールバック: 基本console利用可能")
    except Exception as e:
        print(f"❌ 基本consoleフォールバックエラー: {e}")


def main():
    """テスト実行"""
    print("🧪 統合コンソールシステム機能テスト開始")

    test_basic_console()
    test_integrated_console()
    test_console_log_bridge()
    test_fallback()

    print("\n🎯 テスト完了!")


if __name__ == "__main__":
    main()
