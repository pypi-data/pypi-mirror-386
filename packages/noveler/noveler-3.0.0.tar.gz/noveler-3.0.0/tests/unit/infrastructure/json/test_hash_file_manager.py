"""
ハッシュベースファイル管理機能のテストケース（SPEC-MCP-HASH-001準拠）

@pytest.mark.spec('SPEC-MCP-HASH-001')
"""

import pytest
import tempfile
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

# B20準拠: 共有コンポーネント利用
from scripts.presentation.cli.shared_utilities import (
    console,
    get_logger,
    get_common_path_service
)

# テスト対象モジュール
from noveler.infrastructure.json.file_managers.file_reference_manager import FileReferenceManager
from noveler.infrastructure.json.models.file_reference_models import FileReferenceModel
from noveler.infrastructure.json.utils.hash_utils import calculate_sha256

@pytest.mark.spec('SPEC-MCP-HASH-001')
class TestHashFileManagerCore:
    """
    SPEC-MCP-HASH-001 FR-001, FR-002のテスト
    ハッシュベースファイル管理コア機能
    """

    def setup_method(self):
        """各テスト前の初期化"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = FileReferenceManager(self.test_dir)
        self.logger = get_logger(__name__)

    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_find_file_by_hash_success(self):
        """
        FR-001: SHA256ハッシュによるファイル検索（成功パターン）
        """
        # テストデータ準備
        content = "ハッシュ検索テスト内容"
        file_ref = self.manager.save_content(content, "text/plain", "hash_test")

        # ハッシュで検索
        found_ref = self.manager.find_file_by_hash(file_ref.sha256)

        # 検証
        assert found_ref is not None
        assert found_ref.sha256 == file_ref.sha256
        assert found_ref.path == file_ref.path
        assert found_ref.size_bytes == file_ref.size_bytes

    def test_find_file_by_hash_not_found(self):
        """
        FR-001: SHA256ハッシュによるファイル検索（見つからない）
        """
        # 存在しないハッシュで検索
        fake_hash = "a" * 64  # 64文字の偽ハッシュ
        found_ref = self.manager.find_file_by_hash(fake_hash)

        # 検証
        assert found_ref is None

    def test_find_file_by_hash_invalid_format(self):
        """
        FR-001: 無効なハッシュ形式での検索エラー
        """
        invalid_hashes = [
            "short",  # 短すぎる
            "g" * 64,  # 無効文字
            "",  # 空文字
            "A" * 63,  # 1文字不足
            "A" * 65,  # 1文字過多
        ]

        for invalid_hash in invalid_hashes:
            with pytest.raises(ValueError, match="Invalid hash format"):
                self.manager.find_file_by_hash(invalid_hash)

    def test_get_file_by_hash_with_content(self):
        """
        FR-002: ハッシュ指定でのファイル内容取得
        """
        # テストデータ準備
        content = "内容取得テスト\nマルチライン対応"
        file_ref = self.manager.save_content(content, "text/plain", "content_test")

        # ハッシュで内容取得
        result = self.manager.get_file_by_hash(file_ref.sha256)

        # 検証
        assert result is not None
        found_ref, loaded_content = result
        assert found_ref.sha256 == file_ref.sha256
        assert loaded_content == content

    def test_get_file_by_hash_not_found(self):
        """
        FR-002: 存在しないハッシュでの内容取得
        """
        fake_hash = "b" * 64
        result = self.manager.get_file_by_hash(fake_hash)

        assert result is None

    def test_multiple_files_same_hash(self):
        """
        同じ内容の複数ファイルでハッシュ検索
        """
        content = "同じ内容のファイル"

        # 同じ内容で複数ファイル作成
        file_ref1 = self.manager.save_content(content, "text/plain", "same1")
        file_ref2 = self.manager.save_content(content, "text/plain", "same2")

        # ハッシュは同じはず
        assert file_ref1.sha256 == file_ref2.sha256

        # ハッシュで検索（どちらかが返される）
        found_ref = self.manager.find_file_by_hash(file_ref1.sha256)
        assert found_ref is not None
        assert found_ref.sha256 == file_ref1.sha256


@pytest.mark.spec('SPEC-MCP-HASH-001')
class TestFileChangeDetection:
    """
    SPEC-MCP-HASH-001 FR-003のテスト
    ファイル変更検知機能
    """

    def setup_method(self):
        """各テスト前の初期化"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = FileReferenceManager(self.test_dir)

    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_has_file_changed_no_change(self):
        """
        FR-003: ファイル変更なしの検知
        """
        # ファイル作成
        content = "変更検知テスト"
        file_ref = self.manager.save_content(content, "text/plain", "change_test")
        file_path = self.test_dir / file_ref.path

        # 変更チェック（変更なし）
        has_changed = self.manager.has_file_changed(file_path, file_ref.sha256)
        assert has_changed is False

    def test_has_file_changed_with_change(self):
        """
        FR-003: ファイル変更ありの検知
        """
        # ファイル作成
        content = "変更前の内容"
        file_ref = self.manager.save_content(content, "text/plain", "modify_test")
        file_path = self.test_dir / file_ref.path

        # ファイル内容変更
        modified_content = "変更後の内容"
        file_path.write_text(modified_content, encoding="utf-8")

        # 変更チェック（変更あり）
        has_changed = self.manager.has_file_changed(file_path, file_ref.sha256)
        assert has_changed is True

    def test_has_file_changed_one_byte_change(self):
        """
        FR-003: 1バイト変更でも検知（要件確認）
        """
        # ファイル作成
        content = "abc"
        file_ref = self.manager.save_content(content, "text/plain", "byte_test")
        file_path = self.test_dir / file_ref.path

        # 1バイト変更
        modified_content = "abd"  # c → d
        file_path.write_text(modified_content, encoding="utf-8")

        # 変更チェック（1バイトでも検知）
        has_changed = self.manager.has_file_changed(file_path, file_ref.sha256)
        assert has_changed is True

    def test_has_file_changed_file_not_exists(self):
        """
        FR-003: ファイル不在時のエラー処理
        """
        nonexistent_path = self.test_dir / "nonexistent.txt"
        fake_hash = "c" * 64

        with pytest.raises(FileNotFoundError, match="File not found"):
            self.manager.has_file_changed(nonexistent_path, fake_hash)

    def test_track_changes_multiple_files(self):
        """
        FR-003: 複数ファイルの変更追跡
        """
        # 複数ファイル作成
        files_data = [
            ("file1.txt", "内容1"),
            ("file2.txt", "内容2"),
            ("file3.txt", "内容3")
        ]

        file_refs = []
        for filename, content in files_data:
            file_ref = self.manager.save_content(content, "text/plain", filename)
            file_refs.append(file_ref)

        # 1つのファイルを変更
        modified_path = self.test_dir / file_refs[1].path
        modified_path.write_text("変更された内容2", encoding="utf-8")

        # 変更追跡実行
        changes = self.manager.track_changes()

        # 検証
        assert isinstance(changes, dict)
        # 変更されたファイルが検知される
        changed_files = [path for path, changed in changes.items() if changed]
        assert len(changed_files) == 1


@pytest.mark.spec('SPEC-MCP-HASH-001')
class TestHashIndexManagement:
    """
    ハッシュインデックス管理機能のテスト
    """

    def setup_method(self):
        """各テスト前の初期化"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = FileReferenceManager(self.test_dir)

    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_build_hash_index(self):
        """
        ハッシュインデックス構築のテスト
        """
        # 複数ファイル作成
        contents = ["内容A", "内容B", "内容C"]
        file_refs = []

        for i, content in enumerate(contents):
            file_ref = self.manager.save_content(content, "text/plain", f"index_test_{i}")
            file_refs.append(file_ref)

        # インデックス構築
        hash_index = self.manager._build_hash_index()

        # 検証
        assert isinstance(hash_index, dict)
        assert len(hash_index) == len(contents)

        # 各ハッシュがインデックスに含まれている
        for file_ref in file_refs:
            assert file_ref.sha256 in hash_index
            assert len(hash_index[file_ref.sha256]) >= 1

    def test_hash_index_persistence(self):
        """
        ハッシュインデックスの永続化テスト
        """
        # ファイル作成
        content = "永続化テスト"
        file_ref = self.manager.save_content(content, "text/plain", "persist_test")

        # インデックス保存
        self.manager._save_hash_index()

        # 新しいマネージャーインスタンスでインデックス読み込み
        new_manager = FileReferenceManager(self.test_dir)
        new_manager._load_hash_index()

        # インデックスが復元されることを確認
        found_ref = new_manager.find_file_by_hash(file_ref.sha256)
        assert found_ref is not None
        assert found_ref.sha256 == file_ref.sha256

    def test_list_files_with_hashes(self):
        """
        ファイル・ハッシュ一覧取得のテスト
        """
        # 複数ファイル作成
        test_data = [
            ("list1.txt", "リスト1"),
            ("list2.txt", "リスト2"),
        ]

        expected_hashes = []
        for filename, content in test_data:
            file_ref = self.manager.save_content(content, "text/plain", filename)
            expected_hashes.append(file_ref.sha256)

        # ファイル・ハッシュ一覧取得
        files_with_hashes = self.manager.list_files_with_hashes()

        # 検証
        assert isinstance(files_with_hashes, dict)

        # 作成したファイルのハッシュが全て含まれている
        all_hashes = set()
        for file_list in files_with_hashes.values():
            all_hashes.update(file_list)

        for expected_hash in expected_hashes:
            assert expected_hash in all_hashes


@pytest.mark.spec('SPEC-MCP-HASH-001')
class TestHashFileManagerPerformance:
    """
    NFR-001: 性能要件のテスト
    """

    def setup_method(self):
        """各テスト前の初期化"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = FileReferenceManager(self.test_dir)

    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_hash_search_performance(self):
        """
        NFR-001: O(1)ハッシュ検索性能テスト
        """
        import time

        # 100個のファイル作成
        file_refs = []
        for i in range(100):
            content = f"パフォーマンステスト内容 {i}"
            file_ref = self.manager.save_content(content, "text/plain", f"perf_{i:03d}")
            file_refs.append(file_ref)

        # ハッシュ検索時間測定
        target_hash = file_refs[50].sha256  # 中央のファイル

        start_time = time.time()
        found_ref = self.manager.find_file_by_hash(target_hash)
        search_time = time.time() - start_time

        # 検証
        assert found_ref is not None
        # 環境差分を許容しつつ1桁ms以内を保証
        assert search_time < 0.005, f"Search took {search_time:.4f}s, expected < 0.005s"

    def test_file_retrieval_response_time(self):
        """
        NFR-001: ファイル取得レスポンス時間テスト（100ms以内）
        """
        import time

        # テストファイル作成
        content = "レスポンス時間テスト" * 100  # やや大きなファイル
        file_ref = self.manager.save_content(content, "text/plain", "response_test")

        # ファイル取得時間測定
        start_time = time.time()
        result = self.manager.get_file_by_hash(file_ref.sha256)
        retrieval_time = time.time() - start_time

        # 検証
        assert result is not None
        # レスポンス時間が要件内（100ms以内）
        assert retrieval_time < 0.1, f"Retrieval took {retrieval_time:.4f}s, expected < 0.1s"


@pytest.mark.spec('SPEC-MCP-HASH-001')
class TestHashFileManagerErrorHandling:
    """
    エラーハンドリングとエッジケースのテスト
    """

    def setup_method(self):
        """各テスト前の初期化"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = FileReferenceManager(self.test_dir)

    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_corrupted_file_handling(self):
        """
        破損ファイルの処理テスト
        """
        # ファイル作成
        content = "破損テスト"
        file_ref = self.manager.save_content(content, "text/plain", "corrupt_test")
        file_path = self.test_dir / file_ref.path

        # ファイルを破損させる（バイナリ書き込み）
        file_path.write_bytes(b'\x00\x01\x02\x03')

        # ハッシュ検証で破損検知
        with pytest.raises(ValueError, match="ファイル完全性エラー"):
            self.manager.load_file_content(file_ref)

    def test_unicode_content_handling(self):
        """
        Unicode文字の処理テスト
        """
        # Unicode文字を含むコンテンツ
        content = "日本語テスト 🔍 émojis καὶ ἄλλα ñoël"
        file_ref = self.manager.save_content(content, "text/plain", "unicode_test")

        # ハッシュで取得
        result = self.manager.get_file_by_hash(file_ref.sha256)

        # 検証
        assert result is not None
        found_ref, loaded_content = result
        assert loaded_content == content

    def test_large_file_handling(self):
        """
        大容量ファイルの処理テスト
        """
        # 1MB程度のファイル
        large_content = "大容量テスト内容\n" * 50000
        file_ref = self.manager.save_content(large_content, "text/plain", "large_test")

        # ハッシュで取得
        result = self.manager.get_file_by_hash(file_ref.sha256)

        # 検証
        assert result is not None
        found_ref, loaded_content = result
        assert loaded_content == large_content
        assert found_ref.size_bytes > 500000  # 500KB以上

    def test_shared_components_usage(self):
        """
        B20準拠: 共有コンポーネント使用確認テスト
        """
        # 共有コンポーネントが正しくインポートされていることを確認
        assert console is not None
        assert get_logger is not None
        assert get_common_path_service is not None

        # ログが正しく取得できることを確認
        logger = get_logger(__name__)
        assert logger is not None
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')


# テスト用フィクスチャ
@pytest.fixture
def sample_file_data():
    """サンプルファイルデータ"""
    return [
        ("sample1.txt", "サンプル内容1", "text/plain"),
        ("sample2.md", "# サンプルMarkdown", "text/markdown"),
        ("sample3.json", '{"key": "value"}', "application/json"),
    ]


@pytest.fixture
def hash_test_environment():
    """ハッシュテスト環境"""
    test_dir = Path(tempfile.mkdtemp())
    yield test_dir
    if test_dir.exists():
        shutil.rmtree(test_dir)


# パフォーマンステスト用マーカー
pytestmark = [
    pytest.mark.spec('SPEC-MCP-HASH-001'),
    pytest.mark.performance,
    pytest.mark.hash_management
]
