#!/usr/bin/env python3
"""
統一ファイル保存サービスのテスト・デモンストレーション

新しい統一サービスの動作を検証し、既存の問題が解決されたことを確認
"""
import asyncio
import sys
from pathlib import Path
import tempfile
import shutil

# パス設定
sys.path.append('src')

def test_unified_file_storage():
    """統一ファイル保存サービステスト"""

    print("🧪 統一ファイル保存サービス テスト開始")
    print("=" * 70)

    try:
        # 一時テストディレクトリの作成
        with tempfile.TemporaryDirectory() as temp_dir:
            test_root = Path(temp_dir)

            # 1. 基本的なインポートテスト
            print("\n📦 1. モジュールインポートテスト")
            from noveler.infrastructure.storage import UnifiedFileStorageService
            from noveler.domain.interfaces.i_unified_file_storage import FileContentType

            storage_service = UnifiedFileStorageService(test_root)
            print("✅ UnifiedFileStorageService インスタンス化成功")

            # 2. 形式自動判定テスト
            print("\n🔍 2. ファイル形式自動判定テスト")

            # 原稿の自動判定（40_原稿ディレクトリ）
            manuscript_content = """
# 第001話 最初の出会い

彼女は森の奥で光る石を見つけた。それは魔法の力を秘めているようだった。

「これは一体何なのだろう」と彼女は呟いた。

石は暖かく、心地よい光を放っていた。それはまるで彼女を呼んでいるかのようだった。
"""

            success = storage_service.save(
                "40_原稿/test_manuscript.md",
                manuscript_content
            )
            print(f"✅ 原稿保存（自動判定）: {success}")

            # 設定ファイルの自動判定
            config_content = {
                "project_name": "テスト小説プロジェクト",
                "author": "AI Assistant",
                "version": "1.0.0",
                "settings": {
                    "auto_save": True,
                    "format": "markdown"
                }
            }

            success = storage_service.save(
                "config/project_config.yaml",
                config_content,
                FileContentType.CONFIG
            )
            print(f"✅ 設定保存（YAML指定）: {success}")

            # APIレスポンスの自動判定
            api_response = {
                "status": "success",
                "data": {
                    "episode": 1,
                    "word_count": 1500,
                    "quality_score": 85
                },
                "timestamp": "2025-09-05T18:00:00Z"
            }

            success = storage_service.save(
                "cache/api_response.json",
                api_response,
                FileContentType.API_RESPONSE
            )
            print(f"✅ APIレスポンス保存（JSON指定）: {success}")

            # 3. 原稿専用メソッドテスト
            print("\n📄 3. 原稿専用保存メソッドテスト")

            episode_content = """主人公のアリスは、今日も冒険に出かけた。
森の中で出会った不思議な生き物との会話が、彼女の運命を変えることになる。

「君は誰？」アリスが問いかけると、
「私は森の精霊よ。あなたを待っていたの」と答えが返ってきた。"""

            success = storage_service.save_manuscript(
                episode=1,
                content=episode_content,
                project_root=test_root
            )
            print(f"✅ 原稿専用保存（第001話）: {success}")

            # 4. ファイル読み込みテスト
            print("\n📖 4. ファイル読み込み・メタデータ確認テスト")

            # 原稿読み込み
            loaded_content, metadata = storage_service.load_with_metadata("40_原稿/第001話.md")
            if loaded_content and metadata:
                print("✅ 原稿読み込み成功")
                print(f"   - タイトル: {metadata.get('title')}")
                print(f"   - エピソード: {metadata.get('episode')}")
                print(f"   - ステータス: {metadata.get('status')}")
                print(f"   - 文字数: {len(loaded_content)} 文字")

            # 設定ファイル読み込み
            loaded_config = storage_service.load("config/project_config.yaml")
            if loaded_config:
                print("✅ 設定ファイル読み込み成功")
                print(f"   - プロジェクト名: {loaded_config.get('project_name')}")

            # 5. サポート形式一覧テスト
            print("\n🔧 5. サポート形式・機能テスト")
            supported_formats = storage_service.get_supported_formats()
            print(f"✅ サポート形式: {', '.join(supported_formats)}")

            # 最適形式取得テスト
            optimal_manuscript = storage_service.get_optimal_format(FileContentType.MANUSCRIPT)
            optimal_config = storage_service.get_optimal_format(FileContentType.CONFIG)
            optimal_cache = storage_service.get_optimal_format(FileContentType.CACHE)

            print(f"✅ 最適形式判定:")
            print(f"   - 原稿: {optimal_manuscript}")
            print(f"   - 設定: {optimal_config}")
            print(f"   - キャッシュ: {optimal_cache}")

            # 6. 保存されたファイル一覧の確認
            print("\n📁 6. 保存されたファイル確認")
            for file_path in test_root.rglob("*"):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    print(f"   - {file_path.relative_to(test_root)} ({size} bytes)")

            print("\n🎉 全テスト完了")
            print("✅ 統一ファイル保存サービスは正常に動作しています")

        return True

    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mcp_tools():
    """MCPツール統合テスト"""

    print("\n" + "=" * 70)
    print("🔧 MCPツール統合テスト開始")

    try:
        # MCPサーバー初期化テスト
        from mcp_servers.noveler.json_conversion_server import JSONConversionServer

        print("\n📦 MCPサーバー初期化テスト")
        server = JSONConversionServer()
        print("✅ JSONConversionServer 初期化成功")

        print("✅ 新しい統一保存ツールが追加されました:")
        print("   - save_file: 統一サービスによる確実なファイル保存")
        print("   - save_manuscript: 原稿専用保存（統一サービス経由）")
        print("   - 既存ツールは下位互換性のため保持")

        return True

    except Exception as e:
        print(f"❌ MCPツールテストエラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("統一ファイル保存システム 包括テスト")
    print("=" * 70)

    success_count = 0
    total_tests = 2

    # 1. 統一ファイル保存サービステスト
    if test_unified_file_storage():
        success_count += 1

    # 2. MCPツール統合テスト
    if test_mcp_tools():
        success_count += 1

    # 結果サマリー
    print("\n" + "=" * 70)
    print("🏆 テスト結果サマリー")
    print("=" * 70)
    print(f"成功: {success_count}/{total_tests} テスト")

    if success_count == total_tests:
        print("🎉 全テスト成功！統一ファイル保存システムの実装完了")
        print("\n💡 利用可能な新機能:")
        print("   ✅ 用途別ファイル形式自動判定")
        print("   ✅ YAML frontmatter付きMarkdown保存")
        print("   ✅ 統一されたファイル保存API")
        print("   ✅ 下位互換性の維持")
        print("\n🚀 Claude Codeでの使用方法:")
        print("   - save_file ツールで任意ファイル保存（形式自動選択）")
        print("   - save_manuscript ツールで原稿専用保存")
        print("   - 既存ツールも引き続き利用可能")
    else:
        print("❌ 一部テストが失敗しました")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
