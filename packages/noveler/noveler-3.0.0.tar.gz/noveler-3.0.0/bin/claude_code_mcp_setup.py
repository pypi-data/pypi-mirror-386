#!/usr/bin/env python3
"""Claude Code MCP統合セットアップスクリプト"""

import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path


class ClaudeCodeMCPSetup:
    """Claude Code MCP統合セットアップ"""

    def __init__(self) -> None:
        self.project_root = self._detect_project_root()
        self.config_template = self._get_config_template()

    def _detect_project_root(self) -> Path:
        """プロジェクトルート自動検出"""
        current_file = Path(__file__).resolve()

        for parent in current_file.parents:
            if (parent / "scripts").exists() and (parent / "pyproject.toml").exists():
                return parent

        msg = "プロジェクトルートが見つかりません"
        raise ValueError(msg)

    def _get_config_template(self) -> dict:
        """MCP設定テンプレート生成"""
        return {
            "mcpServers": {
                "novel-json-converter": {
                    "command": "python",
                    "args": [
                        str(self.project_root / "src/noveler/infrastructure/json/cli/json_conversion_cli.py"),
                        "mcp-server",
                        "--stdio"
                    ],
                    "env": {
                        "PYTHONPATH": str(self.project_root),
                        "PYTHONUNBUFFERED": "1"
                    },
                    "cwd": str(self.project_root),
                    "description": "小説執筆支援システム JSON変換・MCP統合サーバー - CLI結果を95%トークン削減でJSON化し、ファイル参照アーキテクチャとSHA256完全性保証を提供"
                }
            }
        }

    def get_claude_code_config_paths(self) -> list[Path]:
        """Claude Code設定ファイルパス候補取得"""
        system = platform.system()
        home = Path.home()

        paths = []

        if system == "Windows":
            # Windows パス
            paths.extend([
                home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json",
                home / ".config" / "claude" / "claude_desktop_config.json",
                Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
            ])
        elif system == "Darwin":
            # macOS パス
            paths.extend([
                home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
                home / ".config" / "claude" / "claude_desktop_config.json"
            ])
        else:
            # Linux パス
            paths.extend([
                home / ".config" / "claude" / "claude_desktop_config.json",
                home / ".claude" / "claude_desktop_config.json"
            ])

        return paths

    def find_existing_config(self) -> Path | None:
        """既存設定ファイル検索"""
        for path in self.get_claude_code_config_paths():
            if path.exists():
                return path
        return None

    def create_config_file(self, output_path: Path | None = None) -> Path:
        """MCP設定ファイル作成"""
        if output_path is None:
            output_path = self.project_root / "claude_code_mcp_config.json"

        # 既存設定があれば統合
        existing_config = self.find_existing_config()
        if existing_config:
            try:
                with open(existing_config, encoding="utf-8") as f:
                    existing_data = json.load(f)

                # MCPサーバー設定を統合
                if "mcpServers" not in existing_data:
                    existing_data["mcpServers"] = {}

                existing_data["mcpServers"].update(self.config_template["mcpServers"])
                config_data = existing_data

            except (json.JSONDecodeError, FileNotFoundError):
                config_data = self.config_template
        else:
            config_data = self.config_template

        # 設定ファイル書き込み
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)

        return output_path

    def install_mcp_dependencies(self) -> bool:
        """MCP依存関係インストール"""
        try:

            # MCP関連パッケージインストール
            packages = ["mcp", "pydantic>=2.0.0"]

            for package in packages:
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", package
                ], check=False, capture_output=True, text=True)

                if result.returncode != 0:
                    print(f"パッケージ {package} のインストールに失敗: {result.stderr}")
                    return False

                print(f"✅ {package} インストール完了")

            return True

        except Exception as e:
            print(f"依存関係インストールエラー: {e}")
            return False

    def verify_installation(self) -> bool:
        """インストール検証"""
        try:
            # MCPサーバー起動テスト

            with tempfile.TemporaryDirectory() as temp_dir:
                test_args = [
                    sys.executable,
                    str(self.project_root / "src/noveler/infrastructure/json/cli/json_conversion_cli.py"),
                    "-o", temp_dir,
                    "health",
                    "--format", "json"
                ]

                result = subprocess.run(test_args, check=False, capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    print("✅ MCPサーバー動作検証成功")
                    return True
                print(f"❌ MCPサーバー動作検証失敗: {result.stderr}")
                return False

        except Exception as e:
            print(f"検証エラー: {e}")
            return False

    def run_setup(self) -> int:
        """セットアップ実行"""
        print("🚀 Claude Code MCP統合セットアップ開始")
        print(f"プロジェクトルート: {self.project_root}")

        # Step 1: 依存関係インストール
        print("\n📦 依存関係インストール中...")
        if not self.install_mcp_dependencies():
            print("❌ 依存関係インストール失敗")
            return 1

        # Step 2: 設定ファイル作成
        print("\n⚙️  MCP設定ファイル作成中...")
        config_path = self.create_config_file()
        print(f"✅ 設定ファイル作成完了: {config_path}")

        # Step 3: インストール検証
        print("\n🔍 インストール検証中...")
        if not self.verify_installation():
            print("❌ インストール検証失敗")
            return 1

        print("\n🎉 Claude Code MCP統合セットアップ完了!")
        print("\n📋 次の手順:")
        print(f"1. 生成された設定ファイルを確認: {config_path}")
        print("2. Claude Code設定ファイルに設定を統合:")

        for path in self.get_claude_code_config_paths():
            if path.parent.exists():
                print(f"   - {path}")
                break

        print("3. Claude Codeを再起動してMCPサーバーを有効化")
        print("\n🛠️  使用方法:")
        print("   Claude CodeでJSON変換MCPツールが利用可能になります")
        print("   - convert_cli_to_json: CLI結果→JSON変換")
        print("   - validate_json_response: JSON検証")
        print("   - get_file_content_by_reference: ファイル内容取得")
        print("   - list_output_files: ファイル一覧")
        print("   - cleanup_old_files: ファイルクリーンアップ")

        return 0

def main():
    """メイン実行"""
    setup = ClaudeCodeMCPSetup()
    return setup.run_setup()

if __name__ == "__main__":
    sys.exit(main())
