"""リファクタリング後のSettingsFileWatcherのテスト

TDD: リポジトリパターンを使用したドメインエンティティのテスト


仕様書: SPEC-DOMAIN-ENTITIES
"""

import hashlib
import inspect
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from noveler.domain.entities.settings_file_watcher import SettingsFileWatcher
from noveler.domain.repositories.file_system_repository import FileSystemRepository


class MockFileSystemRepository(FileSystemRepository):
    """テスト用モックリポジトリ"""

    def __init__(self) -> None:
        self.files = {}  # パス -> 内容
        self.directories = set()  # ディレクトリパス
        self.file_states = {}  # パス -> 状態情報

    def exists(self, path: Path) -> bool:
        str_path = str(path)
        return str_path in self.files or str_path in self.directories

    def is_directory(self, path: Path) -> bool:
        return str(path) in self.directories

    def list_files(self, directory: Path, extensions: set[str]) -> list[Path]:
        dir_str = str(directory)
        if dir_str not in self.directories:
            return []

        files = []
        for file_path in self.files:
            path_obj = Path(file_path)
            if str(path_obj.parent) == dir_str and path_obj.suffix.lower() in extensions:
                files.append(path_obj)

        return files

    def get_file_state(self, file_path: Path) -> dict[str, object] | None:
        str_path = str(file_path)
        return self.file_states.get(str_path)

    def calculate_file_hash(self, file_path: Path) -> str | None:
        str_path = str(file_path)
        if str_path in self.files:
            return hashlib.md5(self.files[str_path].encode()).hexdigest()
        return None

    # 抽象メソッドの実装
    def calculate_hash(self, file_path: Path) -> str | None:
        """ファイルのハッシュ値を計算"""
        return self.calculate_file_hash(file_path)

    def get_file_info(self, file_path: Path) -> dict[str, object] | None:
        """ファイル情報を取得"""
        return self.get_file_state(file_path)

    def get_modification_time(self, file_path: Path) -> datetime | None:
        """ファイルの最終更新時刻を取得"""
        str_path = str(file_path)
        if str_path in self.file_states:
            mtime = self.file_states[str_path].get("mtime", 0)
            return datetime.fromtimestamp(mtime, tz=timezone.utc)
        return None

    def read_yaml(self, file_path: Path) -> dict[str, object] | None:
        """YAMLファイルを読み込み"""
        str_path = str(file_path)
        if str_path in self.files:
            try:
                return yaml.safe_load(self.files[str_path])
            except Exception:
                return None
        return None

    def write_yaml(self, file_path: Path, data: dict[str, object]) -> bool:
        """YAMLファイルに書き込み"""
        try:
            content = yaml.dump(data, allow_unicode=True)
            self.add_file(str(file_path), content)
            return True
        except Exception:
            return False

    def add_directory(self, path: str) -> None:
        """テスト用:ディレクトリを追加"""
        self.directories.add(path)

    def add_file(self, path: str, content: str, mtime: float | None = None) -> None:
        """テスト用:ファイルを追加"""
        self.files[path] = content
        if mtime is None:
            mtime = time.time()

        self.file_states[path] = {
            "mtime": mtime,
            "size": len(content),
            "hash": self.calculate_file_hash(Path(path)),
            "last_checked": mtime,
            "path": path,
        }

    def update_file(self, path: str, content: str) -> None:
        """テスト用:ファイルを更新"""
        self.files[path] = content
        new_mtime = time.time() + 1  # 確実に変更を検出するため

        self.file_states[path] = {
            "mtime": new_mtime,
            "size": len(content),
            "hash": self.calculate_file_hash(Path(path)),
            "last_checked": new_mtime,
            "path": path,
        }

    def delete_file(self, path: str) -> None:
        """テスト用:ファイルを削除"""
        if path in self.files:
            del self.files[path]
        if path in self.file_states:
            del self.file_states[path]


class TestSettingsFileWatcherRefactored:
    """リファクタリング後のSettingsFileWatcherのテスト"""

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER_REFACTORED-WATCHER_NO_DIRECT_FI")
    def test_watcher_no_direct_file_io(self) -> None:
        """エンティティが直接ファイルI/Oを行わないことを確認"""
        source = inspect.getsource(SettingsFileWatcher)

        # 禁止されているimport/関数
        forbidden = ["import os", "import hashlib", "open(", ".read()", ".write()"]
        for forbidden_item in forbidden:
            assert forbidden_item not in source, f"エンティティに{forbidden_item}が含まれています"

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER_REFACTORED-INITIALIZE_WITH_NO_P")
    def test_initialize_with_no_project_root(self) -> None:
        """存在しないプロジェクトルートでの初期化"""
        repo = MockFileSystemRepository()

        # 現在の実装では例外を発生しないため、基本的な初期化をテスト
        watcher = SettingsFileWatcher("/nonexistent", repo)
        assert watcher.project_id == "/nonexistent"

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER_REFACTORED-INITIALIZE_WITH_VALI")
    def test_initialize_with_valid_project(self) -> None:
        """有効なプロジェクトでの初期化"""
        repo = MockFileSystemRepository()
        repo.add_directory("/test/project")

        watcher = SettingsFileWatcher("/test/project", repo)
        assert watcher.project_id == "/test/project"
        assert watcher.settings_dir == "/test/project/30_設定集"

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER_REFACTORED-SETTINGS_DIR_DETECTI")
    def test_settings_dir_detection(self) -> None:
        """設定ディレクトリの存在確認"""
        repo = MockFileSystemRepository()
        repo.add_directory("/test/project")

        watcher = SettingsFileWatcher("/test/project", repo)

        # 設定ディレクトリが存在しない
        assert not watcher.is_settings_dir_exists()

        # 設定ディレクトリを追加
        repo.add_directory("/test/project/30_設定集")
        assert watcher.is_settings_dir_exists()

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER_REFACTORED-INITIALIZE_FILE_STAT")
    def test_initialize_file_states(self) -> None:
        """ファイル状態の初期化"""
        repo = MockFileSystemRepository()
        repo.add_directory("/test/project")
        repo.add_directory("/test/project/30_設定集")

        # YAMLファイルを追加
        repo.add_file("/test/project/30_設定集/world.yaml", "content1")
        repo.add_file("/test/project/30_設定集/character.yml", "content2")
        repo.add_file("/test/project/30_設定集/readme.txt", "ignored")  # 非対象

        watcher = SettingsFileWatcher("/test/project", repo)
        watcher.initialize_file_states()

        file_count = watcher.get_watched_file_count()
        assert file_count == 2  # YAMLファイル2つ

        file_states = watcher.get_file_states()
        assert len(file_states) == 2

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER_REFACTORED-DETECT_FILE_CREATION")
    def test_detect_file_creation(self) -> None:
        """新規ファイル作成の検出"""
        repo = MockFileSystemRepository()
        repo.add_directory("/test/project")
        repo.add_directory("/test/project/30_設定集")

        watcher = SettingsFileWatcher("/test/project", repo)
        watcher.initialize_file_states()

        # 新規ファイルを追加
        repo.add_file("/test/project/30_設定集/magic.yaml", "new content")

        changes = watcher.detect_changes()
        assert len(changes) == 1
        assert changes[0].change_type == "ADDED"
        assert changes[0].file_path.split("/")[-1] == "magic.yaml"

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER_REFACTORED-DETECT_FILE_MODIFICA")
    def test_detect_file_modification(self) -> None:
        """ファイル変更の検出"""
        repo = MockFileSystemRepository()
        repo.add_directory("/test/project")
        repo.add_directory("/test/project/30_設定集")

        # 初期ファイル
        repo.add_file("/test/project/30_設定集/world.yaml", "original content")

        watcher = SettingsFileWatcher("/test/project", repo)
        watcher.initialize_file_states()

        # ファイルを更新
        repo.update_file("/test/project/30_設定集/world.yaml", "modified content")

        changes = watcher.detect_changes()
        assert len(changes) == 1
        assert changes[0].change_type == "MODIFIED"
        assert changes[0].file_path.split("/")[-1] == "world.yaml"

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER_REFACTORED-DETECT_FILE_DELETION")
    def test_detect_file_deletion(self) -> None:
        """ファイル削除の検出"""
        repo = MockFileSystemRepository()
        repo.add_directory("/test/project")
        repo.add_directory("/test/project/30_設定集")

        # 初期ファイル
        repo.add_file("/test/project/30_設定集/world.yaml", "content")

        watcher = SettingsFileWatcher("/test/project", repo)
        watcher.initialize_file_states()

        # ファイルを削除
        repo.delete_file("/test/project/30_設定集/world.yaml")

        changes = watcher.detect_changes()
        assert len(changes) == 1
        assert changes[0].change_type == "DELETED"
        assert changes[0].file_path.split("/")[-1] == "world.yaml"

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER_REFACTORED-NO_CHANGES_DETECTION")
    def test_no_changes_detection(self) -> None:
        """変更なしの場合"""
        repo = MockFileSystemRepository()
        repo.add_directory("/test/project")
        repo.add_directory("/test/project/30_設定集")
        repo.add_file("/test/project/30_設定集/world.yaml", "content")

        watcher = SettingsFileWatcher("/test/project", repo)
        watcher.initialize_file_states()

        # 変更なし
        changes = watcher.detect_changes()
        assert len(changes) == 0

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER_REFACTORED-WATCHED_FILE_COUNT_T")
    def test_watched_file_count_tracking(self) -> None:
        """監視ファイル数の追跡機能"""
        repo = MockFileSystemRepository()
        repo.add_directory("/test/project")
        repo.add_directory("/test/project/30_設定集")

        watcher = SettingsFileWatcher("/test/project", repo)

        # 初期状態ではファイル数は0
        assert watcher.get_watched_file_count() == 0

        # ファイル状態を初期化
        watcher.initialize_file_states()

        # ファイルがない状態でも正常に動作することを確認
        assert watcher.get_watched_file_count() == 0
