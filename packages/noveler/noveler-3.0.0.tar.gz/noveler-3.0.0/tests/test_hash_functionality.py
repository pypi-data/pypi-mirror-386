#!/usr/bin/env python3
"""SPEC-MCP-HASH-001 機能テスト（統合テスト）

B20準拠の品質ゲート確認として、実装した機能が正常に動作することを確認する。
"""

import sys
import os
from pathlib import Path

# プロジェクトルートを設定
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_file_reference_manager_hash_functionality():
    """FileReferenceManagerのハッシュ機能をテスト"""
    print("🔍 FileReferenceManager ハッシュ機能テスト開始...")

    try:
        from noveler.infrastructure.json.file_managers.file_reference_manager import FileReferenceManager

        # テストディレクトリ作成
        test_dir = project_root / "temp_test_output"
        test_dir.mkdir(exist_ok=True)

        # FileReferenceManager初期化
        manager = FileReferenceManager(test_dir)

        # テストコンテンツ保存
        test_content = "これはテスト用のファイル内容です。SPEC-MCP-HASH-001準拠テスト"
        file_ref = manager.save_content(
            content=test_content,
            content_type="text/plain",
            filename_prefix="test"
        )

        print(f"✅ ファイル保存成功: {file_ref.path}")
        print(f"📁 SHA256: {file_ref.sha256[:16]}...")
        print(f"📊 サイズ: {file_ref.size_bytes} bytes")

        # ハッシュによる検索テスト
        found_file = manager.find_file_by_hash(file_ref.sha256)
        assert found_file is not None, "ハッシュによるファイル検索に失敗"
        print("✅ ハッシュによるファイル検索成功")

        # ハッシュによる内容取得テスト
        result = manager.get_file_by_hash(file_ref.sha256)
        assert result is not None, "ハッシュによるファイル内容取得に失敗"

        found_ref, content = result
        assert content == test_content, "取得したファイル内容が一致しない"
        print("✅ ハッシュによるファイル内容取得成功")

        # ファイル変更検知テスト（未変更）
        file_path = test_dir / file_ref.path
        changed = manager.has_file_changed(file_path, file_ref.sha256)
        assert not changed, "未変更ファイルが変更ありと検知された"
        print("✅ ファイル未変更検知成功")

        # ファイル変更検知テスト（変更後）
        modified_content = test_content + "\n追加された内容"
        file_path.write_text(modified_content, encoding="utf-8")
        changed = manager.has_file_changed(file_path, file_ref.sha256)
        assert changed, "変更されたファイルが未変更として検知された"
        print("✅ ファイル変更検知成功")

        # ファイル一覧取得テスト
        files_with_hashes = manager.list_files_with_hashes()
        assert len(files_with_hashes) > 0, "ファイル一覧が空"
        print(f"✅ ファイル一覧取得成功: {len(files_with_hashes)}個のハッシュ")

        print("🎉 FileReferenceManager ハッシュ機能テスト全て成功！")
        return True

    except Exception as e:
        print(f"❌ FileReferenceManager テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # テストディレクトリクリーンアップ
        try:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)
                print("🗑️ テストディレクトリクリーンアップ完了")
        except Exception as e:
            print(f"⚠️ クリーンアップエラー（無視可）: {e}")


def test_mcp_tools_functionality():
    """MCPツール関数をテスト"""
    print("\n🔍 MCPツール機能テスト開始...")

    try:
        # テスト用の設定をするためのパス追加
        sys.path.insert(0, str(project_root / "src" / "mcp_servers" / "noveler"))

        from json_conversion_adapter import (
            get_file_by_hash,
            check_file_changes,
            list_files_with_hashes
        )

        # テストディレクトリ作成
        test_dir = project_root / "temp_mcp_test"
        test_dir.mkdir(exist_ok=True)

        # テストファイル作成
        test_file = test_dir / "test_file.txt"
        test_content = "MCPツールテスト用ファイル"
        test_file.write_text(test_content, encoding="utf-8")

        # ファイル参照情報作成（ダミー）
        from noveler.infrastructure.json.utils.hash_utils import calculate_sha256
        test_hash = calculate_sha256(test_file)

        print(f"📁 テストファイル作成: {test_file}")
        print(f"📊 SHA256: {test_hash[:16]}...")

        # get_file_by_hashテスト（該当なしの場合）
        result = get_file_by_hash("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
        assert result["found"] == False, "存在しないハッシュでファイルが見つかった"
        print("✅ get_file_by_hash (該当なし) 成功")

        # check_file_changesテスト
        result = check_file_changes([str(test_file)])
        assert "results" in result, "check_file_changes レスポンス形式エラー"
        print("✅ check_file_changes 成功")

        # list_files_with_hashesテスト
        result = list_files_with_hashes()
        assert "files" in result, "list_files_with_hashes レスポンス形式エラー"
        print("✅ list_files_with_hashes 成功")

        print("🎉 MCPツール機能テスト全て成功！")
        return True

    except Exception as e:
        print(f"❌ MCPツール テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # テストディレクトリクリーンアップ
        try:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)
                print("🗑️ MCPテストディレクトリクリーンアップ完了")
        except Exception as e:
            print(f"⚠️ クリーンアップエラー（無視可）: {e}")


def main():
    """統合テスト実行"""
    print("🚀 SPEC-MCP-HASH-001 統合テスト開始")
    print("=" * 60)

    results = []

    # FileReferenceManagerテスト
    results.append(test_file_reference_manager_hash_functionality())

    # MCPツールテスト
    results.append(test_mcp_tools_functionality())

    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")

    passed = sum(results)
    total = len(results)

    print(f"✅ 成功: {passed}/{total}")
    print(f"❌ 失敗: {total - passed}/{total}")

    if all(results):
        print("\n🎉 SPEC-MCP-HASH-001 機能実装成功！")
        print("✅ B20準拠品質ゲート: 通過")
        return 0
    else:
        print("\n❌ 一部テストに失敗")
        print("⚠️ B20準拠品質ゲート: 要修正")
        return 1


if __name__ == "__main__":
    sys.exit(main())
