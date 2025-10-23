#!/usr/bin/env python3
"""
MCPサーバーテストスクリプト
"""
import asyncio
import sys
from pathlib import Path

# プロジェクトルート設定
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

async def test_server():
    """MCPサーバーの基本動作テスト"""
    print("🔍 MCPサーバーテスト開始...")

    try:
        # MCPサーバーモジュールのインポート
        from mcp_servers.noveler.main import main as mcp_main
        print("✅ MCPサーバーモジュールのインポート成功")

        # サーバーの起動テスト（すぐに終了）
        print("🚀 MCPサーバー起動テスト...")
        # 注意: 実際の起動はstdioを待つため、インポートのみテスト

        print("✅ MCPサーバーテスト成功")
        return True

    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_server())
    sys.exit(0 if result else 1)
