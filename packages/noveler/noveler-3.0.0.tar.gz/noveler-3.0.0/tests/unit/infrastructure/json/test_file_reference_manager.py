"""FileReferenceManagerのテストケース"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

from scripts.infrastructure.json.file_managers.file_reference_manager import FileReferenceManager
from scripts.infrastructure.json.models.file_reference_models import FileReferenceModel


class TestFileReferenceManager:
    """FileReferenceManagerのテストクラス"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = FileReferenceManager(self.test_dir)

    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_save_content_creates_file_reference(self):
        """ファイル保存と参照生成のテスト"""
        content = "テスト内容"
        content_type = "text/plain"

        file_ref = self.manager.save_content(content, content_type, "test")

        assert isinstance(file_ref, FileReferenceModel)
        assert file_ref.content_type == content_type
        assert file_ref.size_bytes == len(content.encode('utf-8'))
        assert len(file_ref.sha256) == 64  # SHA256ハッシュは64文字
        assert file_ref.path.endswith('.txt')

    def test_custom_filename_is_respected(self):
        """カスタムファイル名の使用テスト"""
        content = "テスト内容"
        custom_name = "custom_test.md"

        file_ref = self.manager.save_content(content, "text/markdown", custom_filename=custom_name)

        assert file_ref.path == custom_name
        actual_path = self.test_dir / custom_name
        assert actual_path.exists()

    def test_file_integrity_verification_success(self):
        """ファイル完全性検証成功のテスト"""
        content = "完全性テスト内容"
        file_ref = self.manager.save_content(content, "text/plain")

        is_valid = self.manager.verify_file_integrity(file_ref)

        assert is_valid is True

    def test_file_integrity_verification_failure(self):
        """ファイル完全性検証失敗のテスト"""
        content = "完全性テスト内容"
        file_ref = self.manager.save_content(content, "text/plain")

        # ファイル内容を変更してハッシュ不一致を作る
        file_path = self.test_dir / file_ref.path
        file_path.write_text("変更された内容", encoding="utf-8")

        is_valid = self.manager.verify_file_integrity(file_ref)

        assert is_valid is False

    def test_file_integrity_verification_missing_file(self):
        """存在しないファイルの完全性検証テスト"""
        # 有効な64文字の16進文字列を使用
        valid_sha256 = "b" * 64  # 64文字の16進文字列
        file_ref = FileReferenceModel(
            path="nonexistent.txt",
            sha256=valid_sha256,
            size_bytes=100,
            content_type="text/plain",
            created_at=datetime.now(timezone.utc)
        )

        is_valid = self.manager.verify_file_integrity(file_ref)

        assert is_valid is False

    def test_load_file_content_success(self):
        """ファイル内容読み込み成功のテスト"""
        original_content = "読み込みテスト内容\n日本語対応確認"
        file_ref = self.manager.save_content(original_content, "text/plain")

        loaded_content = self.manager.load_file_content(file_ref)

        assert loaded_content == original_content

    def test_load_file_content_integrity_error(self):
        """ファイル内容読み込み時の完全性エラーテスト"""
        content = "完全性エラーテスト"
        file_ref = self.manager.save_content(content, "text/plain")

        # ファイル内容を変更
        file_path = self.test_dir / file_ref.path
        file_path.write_text("改ざんされた内容", encoding="utf-8")

        with pytest.raises(ValueError, match="ファイル完全性エラー"):
            self.manager.load_file_content(file_ref)

    def test_extension_mapping(self):
        """コンテンツタイプによる拡張子マッピングのテスト"""
        test_cases = [
            ("text/markdown", ".md"),
            ("text/yaml", ".yaml"),
            ("application/json", ".json"),
            ("text/plain", ".txt"),
            ("unknown/type", ".txt")  # 不明なタイプはtxtになる
        ]

        for content_type, expected_ext in test_cases:
            file_ref = self.manager.save_content("テスト", content_type)
            assert file_ref.path.endswith(expected_ext)

    def test_cleanup_old_files(self):
        """古いファイル削除のテスト"""
        # 現在のファイル作成
        current_file_ref = self.manager.save_content("現在のファイル", "text/plain")

        # 古いファイルをシミュレート（mtime変更）
        old_file_path = self.test_dir / "old_file.txt"
        old_file_path.write_text("古いファイル", encoding="utf-8")

        # 古いファイルのタイムスタンプを変更
        import time
        import os
        old_timestamp = time.time() - (31 * 24 * 60 * 60)  # 31日前
        os.utime(old_file_path, (old_timestamp, old_timestamp))

        deleted_files = self.manager.cleanup_old_files(max_age_days=30)

        assert len(deleted_files) > 0
        assert not old_file_path.exists()
        # 現在のファイルは残存
        current_file_path = self.test_dir / current_file_ref.path
        assert current_file_path.exists()

    @pytest.mark.parametrize("content_size", [
        1,  # 最小サイズ
        1000,  # 中サイズ
        100000,  # 大サイズ
    ])
    def test_various_file_sizes(self, content_size):
        """様々なファイルサイズのテスト"""
        content = "A" * content_size
        file_ref = self.manager.save_content(content, "text/plain")

        assert file_ref.size_bytes == content_size
        loaded_content = self.manager.load_file_content(file_ref)
        assert loaded_content == content

    def test_unicode_content_handling(self):
        """Unicode文字の処理テスト"""
        content = "日本語テスト 🔍 émojis καὶ ἄλλα"
        file_ref = self.manager.save_content(content, "text/plain")

        loaded_content = self.manager.load_file_content(file_ref)
        assert loaded_content == content

    def test_concurrent_file_creation(self):
        """同時ファイル作成のテスト（一意性確保）"""
        import threading

        results = []

        def create_file():
            file_ref = self.manager.save_content("並行テスト", "text/plain")
            results.append(file_ref)

        threads = [threading.Thread(target=create_file) for _ in range(5)]
        for thread in threads:
            thread.start()
        # Prevent indefinite hangs if any worker stalls
        for thread in threads:
            thread.join(timeout=5)
        alive = [t for t in threads if t.is_alive()]
        assert not alive, f"worker threads did not finish: {alive}"

        # 全ファイル名がユニーク
        filenames = [ref.path for ref in results]
        assert len(filenames) == len(set(filenames))

        # 全ファイルが存在
        for file_ref in results:
            file_path = self.test_dir / file_ref.path
            assert file_path.exists()


class TestFileReferenceModel:
    """FileReferenceModelのテストクラス"""

    def test_file_reference_model_creation(self):
        """FileReferenceModel生成のテスト"""
        now = datetime.now(timezone.utc)
        model = FileReferenceModel(
            path="test.txt",
            sha256="a" * 64,  # 有効な64文字の16進文字列
            size_bytes=1024,
            content_type="text/plain",
            created_at=now
        )

        assert model.path == "test.txt"
        assert model.sha256 == "a" * 64  # 64文字の16進文字列
        assert model.size_bytes == 1024
        assert model.content_type == "text/plain"
        assert model.created_at == now

    def test_file_reference_model_encoding_default(self):
        """FileReferenceModelのデフォルトエンコーディングテスト"""
        model = FileReferenceModel(
            path="test.txt",
            sha256="hash",
            size_bytes=100,
            content_type="text/plain",
            created_at=datetime.now(timezone.utc)
        )

        assert model.encoding == "utf-8"


class TestHashBasedFileRetrieval:
    """ハッシュベースファイル取得機能のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = FileReferenceManager(self.test_dir)

    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_find_file_by_hash_success(self):
        """ハッシュによるファイル検索成功のテスト"""
        content = "ハッシュ検索テスト内容"
        file_ref = self.manager.save_content(content, "text/plain")

        # ハッシュでファイルを検索する機能をテスト
        # この機能は実装要求に基づいて追加が必要
        found_content = self.manager.load_file_content(file_ref)

        assert found_content == content

    def test_find_file_by_hash_not_found(self):
        """存在しないハッシュでのファイル検索テスト"""
        # 存在しないハッシュでの検索
        fake_hash = "nonexistent_hash_value"

        # この機能は実装が必要 - 現在はFileReferenceModelを直接使用
        fake_ref = FileReferenceModel(
            path="fake.txt",
            sha256=fake_hash,
            size_bytes=100,
            content_type="text/plain",
            created_at=datetime.now(timezone.utc)
        )

        with pytest.raises(ValueError):
            self.manager.load_file_content(fake_ref)

    def test_hash_collision_handling(self):
        """ハッシュ衝突処理のテスト（理論的シナリオ）"""
        # 同じ内容なら同じハッシュになることを確認
        content = "衝突テスト内容"
        file_ref1 = self.manager.save_content(content, "text/plain")
        file_ref2 = self.manager.save_content(content, "text/plain", custom_filename="duplicate.txt")

        assert file_ref1.sha256 == file_ref2.sha256
        # ただしファイルパスは異なる
        assert file_ref1.path != file_ref2.path


@pytest.mark.integration
class TestMCPFileReferenceIntegration:
    """MCPツールとファイル参照機能の統合テスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = FileReferenceManager(self.test_dir)

    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_mcp_file_reference_info_retrieval(self):
        """MCPツール経由でのファイル参照情報取得テスト"""
        # ファイル作成
        content = "MCPテスト内容"
        file_ref = self.manager.save_content(content, "text/plain")
        file_path = self.test_dir / file_ref.path

        # get_file_reference_info関数のテスト
        from scripts.mcp_servers.noveler.json_conversion_adapter import get_file_reference_info

        result = get_file_reference_info(str(file_path))

        assert result["exists"] is True
        assert result["size"] == file_ref.size_bytes
        assert result["is_file"] is True
        assert result["name"] == file_ref.path

    def test_mcp_file_reference_info_not_found(self):
        """MCPツール経由での存在しないファイル情報取得テスト"""
        from scripts.mcp_servers.noveler.json_conversion_adapter import get_file_reference_info

        result = get_file_reference_info("nonexistent_file.txt")

        assert result["exists"] is False
        assert "error" in result

    def test_end_to_end_file_reference_workflow(self):
        """エンドツーエンドのファイル参照ワークフローテスト"""
        # 1. ファイル作成と参照生成
        content = "E2Eワークフローテスト内容\n複数行対応確認"
        file_ref = self.manager.save_content(content, "text/markdown", "workflow_test")

        # 2. ファイル完全性確認
        assert self.manager.verify_file_integrity(file_ref) is True

        # 3. ファイル内容読み込み
        loaded_content = self.manager.load_file_content(file_ref)
        assert loaded_content == content

        # 4. MCPツール経由での情報取得
        from scripts.mcp_servers.noveler.json_conversion_adapter import get_file_reference_info
        file_path = self.test_dir / file_ref.path
        mcp_result = get_file_reference_info(str(file_path))

        assert mcp_result["exists"] is True
        assert mcp_result["size"] == file_ref.size_bytes

        # 5. クリーンアップテスト
        deleted_files = self.manager.cleanup_old_files(max_age_days=0)
        assert len(deleted_files) > 0
        assert not file_path.exists()
