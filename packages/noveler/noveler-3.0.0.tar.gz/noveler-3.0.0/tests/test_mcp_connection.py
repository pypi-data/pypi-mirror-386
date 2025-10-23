#!/usr/bin/env python3
"""
MCP接続診断スクリプト
"""
import json
import asyncio
import subprocess
import sys
from pathlib import Path
import pytest


pytestmark = [pytest.mark.integration, pytest.mark.slow]

async def test_mcp_server():
    """MCPサーバーへの接続テスト"""
    print("🔍 MCP接続診断開始...")

    # MCPサーバーのパス
    mcp_server_path = Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/dist/mcp_servers/noveler/main.py")

    if not mcp_server_path.exists():
        print(f"❌ MCPサーバーファイルが見つかりません: {mcp_server_path}")
        return False

    print(f"✅ MCPサーバーファイル確認: {mcp_server_path}")

    # テスト用のリクエスト（初期化→ツールリスト）
    test_requests = [
        {"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "0.1.0", "capabilities": {}}, "id": 1},
        {"jsonrpc": "2.0", "method": "tools/list", "id": 2}
    ]

    # 環境変数設定
    env = {
        **subprocess.os.environ,
        "PYTHONPATH": "/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/dist",
        "PYTHONUNBUFFERED": "1",
        "NOVEL_PRODUCTION_MODE": "1"
    }

    try:
        # MCPサーバープロセスを起動
        print("🚀 MCPサーバー起動中...")
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(mcp_server_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )

        # リクエストを送信
        for i, request in enumerate(test_requests):
            print(f"\n📤 リクエスト {i+1}: {request['method']}")
            request_data = json.dumps(request) + "\n"
            process.stdin.write(request_data.encode())
            await process.stdin.drain()

            # レスポンスを読み取り（タイムアウト付き）
            try:
                response_line = await asyncio.wait_for(
                    process.stdout.readline(),
                    timeout=2.0
                )
                response = json.loads(response_line.decode())

                if "result" in response:
                    print(f"✅ レスポンス成功:")
                    if request["method"] == "initialize":
                        print(f"   サーバー名: {response['result'].get('serverInfo', {}).get('name', 'unknown')}")
                    elif request["method"] == "tools/list":
                        tools = response['result'].get('tools', [])
                        print(f"   利用可能ツール数: {len(tools)}")
                        if tools:
                            print("   ツール一覧:")
                            for tool in tools[:5]:  # 最初の5個のみ表示
                                print(f"     - {tool['name']}: {tool.get('description', '')[:50]}...")
                elif "error" in response:
                    print(f"⚠️  エラーレスポンス: {response['error']}")

            except asyncio.TimeoutError:
                print("⏱️  タイムアウト - レスポンスなし")
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析エラー: {e}")

        # プロセス終了
        process.terminate()
        await process.wait()

        print("\n✅ MCP接続診断完了")
        return True

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_mcp_server())
    sys.exit(0 if result else 1)
