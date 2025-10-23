"""設定ファイル監視エンティティのテスト

TDD準拠テスト:
    - SettingsFileWatcher
- FileChangeEvent
- ChangeType (Enum)


仕様書: SPEC-DOMAIN-ENTITIES
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest
pytestmark = pytest.mark.project

from noveler.domain.entities.file_change_event import (
    ChangeType,
    FileChangeEvent,
    FileChangeType,
)
from noveler.domain.entities.settings_file_watcher import SettingsFileWatcher
from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestChangeType:
    """ChangeType(Enum)のテストクラス"""

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-CHANGE_TYPE_VALUES")
    def test_change_type_values(self) -> None:
        """変更タイプ値テスト"""
        assert ChangeType.ADDED.value == "ADDED"
        assert ChangeType.MODIFIED.value == "MODIFIED"
        assert ChangeType.DELETED.value == "DELETED"

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-CHANGE_TYPE_ENUM_COU")
    def test_change_type_enum_count(self) -> None:
        """変更タイプ数テスト"""
        assert len(ChangeType) == 3

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-FILE_CHANGE_TYPE_ALI")
    def test_file_change_type_alias(self) -> None:
        """FileChangeType エイリアステスト"""
        assert FileChangeType == ChangeType
        assert FileChangeType.ADDED == ChangeType.ADDED


class TestFileChangeEvent:
    """FileChangeEventエンティティのテストクラス"""

    @pytest.fixture
    def basic_event(self) -> FileChangeEvent:
        """基本ファイル変更イベント"""
        return FileChangeEvent(
            file_path="/test/project/30_設定集/キャラクター.yaml",
            change_type="MODIFIED",
            timestamp=project_now().datetime,
        )

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-FILE_CHANGE_EVENT_CR")
    def test_file_change_event_creation_valid(self, basic_event: FileChangeEvent) -> None:
        """有効な値でのファイル変更イベント作成テスト"""
        assert basic_event.file_path == "/test/project/30_設定集/キャラクター.yaml"
        assert basic_event.change_type == "MODIFIED"
        assert isinstance(basic_event.timestamp, datetime)

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-FILE_CHANGE_EVENT_CR")
    def test_file_change_event_creation_invalid_change_type(self) -> None:
        """無効な変更タイプでのファイル変更イベント作成エラーテスト"""
        with pytest.raises(ValueError, match="無効な変更タイプ: INVALID_TYPE"):
            FileChangeEvent(file_path="/test/file.yaml", change_type="INVALID_TYPE", timestamp=project_now().datetime)

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-IS_SETTINGS_FILE_TRU")
    def test_is_settings_file_true(self, basic_event: FileChangeEvent) -> None:
        """設定ファイル判定(True)テスト"""
        assert basic_event.is_settings_file() is True

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-IS_SETTINGS_FILE_FAL")
    def test_is_settings_file_false(self) -> None:
        """設定ファイル判定(False)テスト"""
        event = FileChangeEvent(
            file_path="/test/project/40_原稿/第001話.md", change_type="MODIFIED", timestamp=project_now().datetime
        )

        assert event.is_settings_file() is False

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-REQUIRES_EXTRACTION_")
    def test_requires_extraction_settings_yaml_true(self, basic_event: FileChangeEvent) -> None:
        """設定YAMLファイルでの抽出必要判定(True)テスト"""
        assert basic_event.requires_extraction() is True

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-REQUIRES_EXTRACTION_")
    def test_requires_extraction_non_settings_false(self) -> None:
        """非設定ファイルでの抽出必要判定(False)テスト"""
        event = FileChangeEvent(
            file_path="/test/project/40_原稿/第001話.md", change_type="MODIFIED", timestamp=project_now().datetime
        )

        assert event.requires_extraction() is False

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-REQUIRES_EXTRACTION_")
    def test_requires_extraction_non_yaml_false(self) -> None:
        """非YAMLファイルでの抽出必要判定(False)テスト"""
        event = FileChangeEvent(
            file_path="/test/project/30_設定集/readme.txt", change_type="MODIFIED", timestamp=project_now().datetime
        )

        assert event.requires_extraction() is False

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-REQUIRES_EXTRACTION_")
    def test_requires_extraction_all_change_types(self) -> None:
        """全変更タイプでの抽出必要判定テスト"""
        test_cases = [("ADDED", True), ("MODIFIED", True), ("DELETED", True)]

        for change_type, expected in test_cases:
            event = FileChangeEvent(
                file_path="/test/project/30_設定集/test.yaml", change_type=change_type, timestamp=project_now().datetime
            )

            assert event.requires_extraction() == expected

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_FILE_CATEGORY_CH")
    def test_get_file_category_character(self) -> None:
        """キャラクターファイルカテゴリ取得テスト"""
        event = FileChangeEvent(
            file_path="/test/30_設定集/キャラクター.yaml", change_type="MODIFIED", timestamp=project_now().datetime
        )

        assert event.get_file_category() == "character"

        # 英語版も確認
        event_en = FileChangeEvent(
            file_path="/test/30_設定集/character_settings.yaml",
            change_type="MODIFIED",
            timestamp=project_now().datetime,
        )

        assert event_en.get_file_category() == "character"

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_FILE_CATEGORY_WO")
    def test_get_file_category_world(self) -> None:
        """世界観ファイルカテゴリ取得テスト"""
        event = FileChangeEvent(
            file_path="/test/30_設定集/世界観.yaml", change_type="MODIFIED", timestamp=project_now().datetime
        )

        assert event.get_file_category() == "world"

        # 英語版も確認
        event_en = FileChangeEvent(
            file_path="/test/30_設定集/world_settings.yaml", change_type="MODIFIED", timestamp=project_now().datetime
        )

        assert event_en.get_file_category() == "world"

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_FILE_CATEGORY_TE")
    def test_get_file_category_terminology(self) -> None:
        """用語集ファイルカテゴリ取得テスト"""
        event = FileChangeEvent(
            file_path="/test/30_設定集/用語集.yaml", change_type="MODIFIED", timestamp=project_now().datetime
        )

        assert event.get_file_category() == "terminology"

        # 英語版も確認
        event_en = FileChangeEvent(
            file_path="/test/30_設定集/terminology.yaml", change_type="MODIFIED", timestamp=project_now().datetime
        )

        assert event_en.get_file_category() == "terminology"

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_FILE_CATEGORY_MA")
    def test_get_file_category_magic(self) -> None:
        """魔法システムファイルカテゴリ取得テスト"""
        event = FileChangeEvent(
            file_path="/test/30_設定集/魔法システム.yaml", change_type="MODIFIED", timestamp=project_now().datetime
        )

        assert event.get_file_category() == "magic"

        # 英語版も確認
        event_en = FileChangeEvent(
            file_path="/test/30_設定集/magic_system.yaml", change_type="MODIFIED", timestamp=project_now().datetime
        )

        assert event_en.get_file_category() == "magic"

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_FILE_CATEGORY_TE")
    def test_get_file_category_technology(self) -> None:
        """技術ファイルカテゴリ取得テスト"""
        event = FileChangeEvent(
            file_path="/test/30_設定集/技術仕様.yaml", change_type="MODIFIED", timestamp=project_now().datetime
        )

        assert event.get_file_category() == "technology"

        # 英語版も確認
        event_en = FileChangeEvent(
            file_path="/test/30_設定集/tech_specs.yaml", change_type="MODIFIED", timestamp=project_now().datetime
        )

        assert event_en.get_file_category() == "technology"

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_FILE_CATEGORY_OT")
    def test_get_file_category_other(self) -> None:
        """その他ファイルカテゴリ取得テスト"""
        event = FileChangeEvent(
            file_path="/test/30_設定集/その他設定.yaml", change_type="MODIFIED", timestamp=project_now().datetime
        )

        assert event.get_file_category() == "other"

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-IS_DELETION_TRUE")
    def test_is_deletion_true(self) -> None:
        """削除イベント判定(True)テスト"""
        event = FileChangeEvent(file_path="/test/file.yaml", change_type="DELETED", timestamp=project_now().datetime)
        assert event.is_deletion() is True

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-IS_DELETION_FALSE")
    def test_is_deletion_false(self, basic_event: FileChangeEvent) -> None:
        """削除イベント判定(False)テスト"""
        assert basic_event.is_deletion() is False

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-IS_ADDITION_TRUE")
    def test_is_addition_true(self) -> None:
        """追加イベント判定(True)テスト"""
        event = FileChangeEvent(file_path="/test/file.yaml", change_type="ADDED", timestamp=project_now().datetime)
        assert event.is_addition() is True

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-IS_ADDITION_FALSE")
    def test_is_addition_false(self, basic_event: FileChangeEvent) -> None:
        """追加イベント判定(False)テスト"""
        assert basic_event.is_addition() is False

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-IS_MODIFICATION_TRUE")
    def test_is_modification_true(self, basic_event: FileChangeEvent) -> None:
        """変更イベント判定(True)テスト"""
        assert basic_event.is_modification() is True

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-IS_MODIFICATION_FALS")
    def test_is_modification_false(self) -> None:
        """変更イベント判定(False)テスト"""
        event = FileChangeEvent(file_path="/test/file.yaml", change_type="ADDED", timestamp=project_now().datetime)
        assert event.is_modification() is False

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_PRIORITY_DELETIO")
    def test_get_priority_deletion_highest(self) -> None:
        """削除イベント最高優先度テスト"""
        event = FileChangeEvent(file_path="/test/file.yaml", change_type="DELETED", timestamp=project_now().datetime)
        assert event.get_priority() == 1

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_PRIORITY_MODIFIC")
    def test_get_priority_modification_medium(self, basic_event: FileChangeEvent) -> None:
        """変更イベント中優先度テスト"""
        assert basic_event.get_priority() == 2

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_PRIORITY_ADDITIO")
    def test_get_priority_addition_lowest(self) -> None:
        """追加イベント最低優先度テスト"""
        event = FileChangeEvent(file_path="/test/file.yaml", change_type="ADDED", timestamp=project_now().datetime)
        assert event.get_priority() == 3

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-EQUALITY_SAME_EVENTS")
    def test_equality_same_events(self, basic_event: FileChangeEvent) -> None:
        """同じイベントでの等価比較テスト"""
        other_event = FileChangeEvent(
            file_path=basic_event.file_path,
            change_type=basic_event.change_type,
            timestamp=project_now().datetime,  # 時刻は異なる
        )
        assert basic_event == other_event

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-EQUALITY_DIFFERENT_E")
    def test_equality_different_events(self, basic_event: FileChangeEvent) -> None:
        """異なるイベントでの等価比較テスト"""
        other_event = FileChangeEvent(
            file_path="/different/path.yaml", change_type="ADDED", timestamp=project_now().datetime
        )

        assert basic_event != other_event

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-EQUALITY_NON_EVENT_O")
    def test_equality_non_event_object(self, basic_event: FileChangeEvent) -> None:
        """非イベントオブジェクトとの等価比較テスト"""
        assert basic_event != "not an event"
        assert basic_event != 123

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-HASH_CONSISTENCY")
    def test_hash_consistency(self, basic_event: FileChangeEvent) -> None:
        """ハッシュ一貫性テスト"""
        other_event = FileChangeEvent(
            file_path=basic_event.file_path, change_type=basic_event.change_type, timestamp=project_now().datetime
        )

        assert hash(basic_event) == hash(other_event)

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-STR_REPRESENTATION")
    def test_str_representation(self, basic_event: FileChangeEvent) -> None:
        """文字列表現テスト"""
        str_repr = str(basic_event)
        assert "FileChangeEvent" in str_repr
        assert "MODIFIED" in str_repr
        assert "キャラクター.yaml" in str_repr

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-REPR_REPRESENTATION")
    def test_repr_representation(self, basic_event: FileChangeEvent) -> None:
        """デバッグ用文字列表現テスト"""
        repr_str = repr(basic_event)
        assert "FileChangeEvent(" in repr_str
        assert basic_event.file_path in repr_str
        assert basic_event.change_type in repr_str
        assert "timestamp=" in repr_str


class TestSettingsFileWatcher:
    """SettingsFileWatcherエンティティのテストクラス"""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """モックファイルシステムリポジトリ"""
        return Mock()

    @pytest.fixture
    def watcher(self, mock_repository: Mock) -> SettingsFileWatcher:
        """基本設定ファイル監視器"""
        return SettingsFileWatcher("test_project", mock_repository)

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-SETTINGS_FILE_WATCHE")
    def test_settings_file_watcher_creation(self, watcher: SettingsFileWatcher) -> None:
        """設定ファイル監視器作成テスト"""
        assert watcher.project_id == "test_project"
        assert watcher.settings_dir == "test_project/30_設定集"
        assert watcher._file_states == {}
        assert watcher._watch_extensions == {".yaml", ".yml"}
        assert watcher._last_check_time is None

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-IS_SETTINGS_DIR_EXIS")
    def test_is_settings_dir_exists_true(self, watcher: SettingsFileWatcher, mock_repository: Mock) -> None:
        """設定ディレクトリ存在判定(True)テスト"""
        mock_repository.exists.return_value = True
        mock_repository.is_directory.return_value = True

        result = watcher.is_settings_dir_exists()

        assert result is True
        mock_repository.exists.assert_called_once_with("test_project/30_設定集")
        mock_repository.is_directory.assert_called_once_with("test_project/30_設定集")

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-IS_SETTINGS_DIR_EXIS")
    def test_is_settings_dir_exists_false_not_exists(self, watcher: SettingsFileWatcher, mock_repository: Mock) -> None:
        """設定ディレクトリ存在判定(False・存在しない)テスト"""
        mock_repository.exists.return_value = False

        result = watcher.is_settings_dir_exists()

        assert result is False
        mock_repository.exists.assert_called_once_with("test_project/30_設定集")
        mock_repository.is_directory.assert_not_called()

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-IS_SETTINGS_DIR_EXIS")
    def test_is_settings_dir_exists_false_not_directory(
        self, watcher: SettingsFileWatcher, mock_repository: Mock
    ) -> None:
        """設定ディレクトリ存在判定(False・ディレクトリでない)テスト"""
        mock_repository.exists.return_value = True
        mock_repository.is_directory.return_value = False

        result = watcher.is_settings_dir_exists()

        assert result is False

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-INITIALIZE_FILE_STAT")
    def test_initialize_file_states_success(self, watcher: SettingsFileWatcher, mock_repository: Mock) -> None:
        """ファイル状態初期化成功テスト"""
        # 設定ディレクトリが存在
        mock_repository.exists.return_value = True
        mock_repository.is_directory.return_value = True

        # ファイルリストを返す
        mock_files = [MagicMock(name="キャラクター.yaml"), MagicMock(name="世界観.yml")]
        mock_repository.list_files.return_value = mock_files

        # ファイル情報を返す
        file_info_1 = {"mtime": 1000, "size": 500, "hash": "abc123"}
        file_info_2 = {"mtime": 2000, "size": 800, "hash": "def456"}
        mock_repository.get_file_info.side_effect = [file_info_1, file_info_2]

        watcher.initialize_file_states()

        assert len(watcher._file_states) == 2
        assert "キャラクター.yaml" in watcher._file_states
        assert "世界観.yml" in watcher._file_states
        assert watcher._file_states["キャラクター.yaml"] == file_info_1
        assert watcher._file_states["世界観.yml"] == file_info_2
        assert watcher._last_check_time is not None

        mock_repository.list_files.assert_called_once_with("test_project/30_設定集", extensions={".yaml", ".yml"})

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-INITIALIZE_FILE_STAT")
    def test_initialize_file_states_directory_not_exists(
        self, watcher: SettingsFileWatcher, mock_repository: Mock
    ) -> None:
        """ディレクトリ存在しない場合の初期化テスト"""
        mock_repository.exists.return_value = False

        watcher.initialize_file_states()

        assert watcher._file_states == {}
        assert watcher._last_check_time is None
        mock_repository.list_files.assert_not_called()

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-INITIALIZE_FILE_STAT")
    def test_initialize_file_states_clears_existing_states(
        self, watcher: SettingsFileWatcher, mock_repository: Mock
    ) -> None:
        """既存状態クリアの初期化テスト"""
        # 既存の状態を設定
        watcher._file_states = {"old_file.yaml": {"mtime": 500}}

        # 新しい初期化
        mock_repository.exists.return_value = True
        mock_repository.is_directory.return_value = True
        mock_repository.list_files.return_value = []

        watcher.initialize_file_states()

        assert watcher._file_states == {}

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_FILE_STATES")
    def test_get_file_states(self, watcher: SettingsFileWatcher) -> None:
        """ファイル状態取得テスト"""
        test_states = {"file1.yaml": {"mtime": 1000}, "file2.yml": {"mtime": 2000}}
        watcher._file_states = test_states

        result = watcher.get_file_states()

        assert result == test_states
        # コピーが返されることを確認
        result["new_file"] = {"mtime": 3000}
        assert "new_file" not in watcher._file_states

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-DETECT_CHANGES_DIREC")
    def test_detect_changes_directory_not_exists(self, watcher: SettingsFileWatcher, mock_repository: Mock) -> None:
        """ディレクトリ存在しない場合の変更検出テスト"""
        mock_repository.exists.return_value = False

        changes = watcher.detect_changes()

        assert changes == []
        assert watcher._last_check_time is not None  # 時刻は更新される

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-DETECT_CHANGES_NEW_F")
    def test_detect_changes_new_file(self, watcher: SettingsFileWatcher, mock_repository: Mock) -> None:
        """新規ファイル検出テスト"""
        # 既存状態なし
        watcher._file_states = {}

        # 現在のファイルリスト
        mock_repository.exists.return_value = True
        mock_repository.is_directory.return_value = True
        new_file = MagicMock(name="新規ファイル.yaml")
        mock_repository.list_files.return_value = [new_file]

        # ファイル情報
        file_info = {"mtime": 1000, "size": 500, "hash": "abc123"}
        mock_repository.get_file_info.return_value = file_info

        changes = watcher.detect_changes()

        assert len(changes) == 1
        change = changes[0]
        assert change.file_name == "新規ファイル.yaml"
        assert change.change_type == FileChangeType.CREATED
        assert change.details["new_file"] is True
        assert change.details["path"] == str(new_file)

        # 状態が更新されることを確認
        assert "新規ファイル.yaml" in watcher._file_states
        assert watcher._file_states["新規ファイル.yaml"] == file_info

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-DETECT_CHANGES_DELET")
    def test_detect_changes_deleted_file(self, watcher: SettingsFileWatcher, mock_repository: Mock) -> None:
        """削除ファイル検出テスト"""
        # 既存状態に削除予定ファイルを設定
        watcher._file_states = {"削除ファイル.yaml": {"mtime": 1000}}

        # 現在のファイルリスト(空)
        mock_repository.exists.return_value = True
        mock_repository.is_directory.return_value = True
        mock_repository.list_files.return_value = []

        changes = watcher.detect_changes()

        assert len(changes) == 1
        change = changes[0]
        assert change.file_name == "削除ファイル.yaml"
        assert change.change_type == FileChangeType.DELETED
        assert change.details["deleted"] is True

        # 状態から削除されることを確認
        assert "削除ファイル.yaml" not in watcher._file_states

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-DETECT_CHANGES_MODIF")
    def test_detect_changes_modified_file(self, watcher: SettingsFileWatcher, mock_repository: Mock) -> None:
        """変更ファイル検出テスト"""
        # 既存状態
        old_info = {"mtime": 1000, "size": 500, "hash": "abc123"}
        watcher._file_states = {"変更ファイル.yaml": old_info}

        # 現在のファイルリスト
        mock_repository.exists.return_value = True
        mock_repository.is_directory.return_value = True
        modified_file = MagicMock(name="変更ファイル.yaml")
        mock_repository.list_files.return_value = [modified_file]

        # 新しいファイル情報(変更あり)
        new_info = {"mtime": 2000, "size": 600, "hash": "def456"}
        mock_repository.get_file_info.return_value = new_info

        changes = watcher.detect_changes()

        assert len(changes) == 1
        change = changes[0]
        assert change.file_name == "変更ファイル.yaml"
        assert change.change_type == FileChangeType.MODIFIED
        assert change.details["time_changed"] is True
        assert change.details["size_changed"] is True
        assert change.details["content_changed"] is True

        # 状態が更新されることを確認
        assert watcher._file_states["変更ファイル.yaml"] == new_info

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-DETECT_CHANGES_NO_CH")
    def test_detect_changes_no_changes(self, watcher: SettingsFileWatcher, mock_repository: Mock) -> None:
        """変更なしの検出テスト"""
        # 既存状態
        file_info = {"mtime": 1000, "size": 500, "hash": "abc123"}
        watcher._file_states = {"既存ファイル.yaml": file_info}

        # 現在のファイルリスト(同じファイル情報)
        mock_repository.exists.return_value = True
        mock_repository.is_directory.return_value = True
        existing_file = MagicMock(name="既存ファイル.yaml")
        mock_repository.list_files.return_value = [existing_file]
        mock_repository.get_file_info.return_value = file_info  # 同じ情報

        changes = watcher.detect_changes()

        assert changes == []

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-DETECT_CHANGES_MIXED")
    def test_detect_changes_mixed_changes(self, watcher: SettingsFileWatcher, mock_repository: Mock) -> None:
        """複合変更検出テスト"""
        # 既存状態(変更・削除対象)
        watcher._file_states = {
            "変更ファイル.yaml": {"mtime": 1000, "size": 500, "hash": "abc123"},
            "削除ファイル.yaml": {"mtime": 1500, "size": 300, "hash": "ghi789"},
        }

        # 現在のファイルリスト
        mock_repository.exists.return_value = True
        mock_repository.is_directory.return_value = True
        modified_file = MagicMock(name="変更ファイル.yaml")
        new_file = MagicMock(name="新規ファイル.yaml")
        mock_repository.list_files.return_value = [modified_file, new_file]

        # ファイル情報
        def get_file_info_side_effect(file_path):
            if file_path.name == "変更ファイル.yaml":
                return {"mtime": 2000, "size": 600, "hash": "def456"}  # 変更
            if file_path.name == "新規ファイル.yaml":
                return {"mtime": 3000, "size": 400, "hash": "jkl012"}  # 新規
            return None

        mock_repository.get_file_info.side_effect = get_file_info_side_effect

        changes = watcher.detect_changes()

        assert len(changes) == 3  # 新規、削除、変更

        # 変更タイプを確認
        change_types = {change.change_type for change in changes}
        assert FileChangeType.CREATED in change_types
        assert FileChangeType.DELETED in change_types
        assert FileChangeType.MODIFIED in change_types

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-COMPARE_FILE_INFO_TI")
    def test_compare_file_info_time_change(self, watcher: SettingsFileWatcher) -> None:
        """時刻変更の比較テスト"""
        old_info = {"mtime": 1000, "size": 500, "hash": "abc123"}
        new_info = {"mtime": 2000, "size": 500, "hash": "abc123"}

        changes = watcher._compare_file_info(old_info, new_info)

        assert changes is not None
        assert changes["time_changed"] is True
        assert changes["old_mtime"] == 1000
        assert changes["new_mtime"] == 2000
        assert "size_changed" not in changes
        assert "content_changed" not in changes

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-COMPARE_FILE_INFO_SI")
    def test_compare_file_info_size_change(self, watcher: SettingsFileWatcher) -> None:
        """サイズ変更の比較テスト"""
        old_info = {"mtime": 1000, "size": 500, "hash": "abc123"}
        new_info = {"mtime": 1000, "size": 600, "hash": "abc123"}

        changes = watcher._compare_file_info(old_info, new_info)

        assert changes is not None
        assert changes["size_changed"] is True
        assert changes["old_size"] == 500
        assert changes["new_size"] == 600
        assert "time_changed" not in changes
        assert "content_changed" not in changes

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-COMPARE_FILE_INFO_CO")
    def test_compare_file_info_content_change(self, watcher: SettingsFileWatcher) -> None:
        """コンテンツ変更の比較テスト"""
        old_info = {"mtime": 1000, "size": 500, "hash": "abc123"}
        new_info = {"mtime": 1000, "size": 500, "hash": "def456"}

        changes = watcher._compare_file_info(old_info, new_info)

        assert changes is not None
        assert changes["content_changed"] is True
        assert changes["old_hash"] == "abc123"
        assert changes["new_hash"] == "def456"
        assert "time_changed" not in changes
        assert "size_changed" not in changes

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-COMPARE_FILE_INFO_MU")
    def test_compare_file_info_multiple_changes(self, watcher: SettingsFileWatcher) -> None:
        """複数変更の比較テスト"""
        old_info = {"mtime": 1000, "size": 500, "hash": "abc123"}
        new_info = {"mtime": 2000, "size": 600, "hash": "def456"}

        changes = watcher._compare_file_info(old_info, new_info)

        assert changes is not None
        assert changes["time_changed"] is True
        assert changes["size_changed"] is True
        assert changes["content_changed"] is True

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-COMPARE_FILE_INFO_NO")
    def test_compare_file_info_no_changes(self, watcher: SettingsFileWatcher) -> None:
        """変更なしの比較テスト"""
        file_info = {"mtime": 1000, "size": 500, "hash": "abc123"}

        changes = watcher._compare_file_info(file_info, file_info)

        assert changes is None

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_WATCHED_FILE_COU")
    def test_get_watched_file_count(self, watcher: SettingsFileWatcher) -> None:
        """監視ファイル数取得テスト"""
        watcher._file_states = {
            "file1.yaml": {"mtime": 1000},
            "file2.yml": {"mtime": 2000},
            "file3.yaml": {"mtime": 3000},
        }

        count = watcher.get_watched_file_count()

        assert count == 3

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_WATCHED_FILE_COU")
    def test_get_watched_file_count_empty(self, watcher: SettingsFileWatcher) -> None:
        """空の監視ファイル数取得テスト"""
        assert watcher.get_watched_file_count() == 0

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-HAS_CHANGES_SINCE_TR")
    def test_has_changes_since_true(self, watcher: SettingsFileWatcher) -> None:
        """指定時刻以降変更有りテスト"""
        watcher._file_states = {
            "file1.yaml": {"mtime": 1000},
            "file2.yml": {"mtime": 2000},  # 指定時刻より新しい
        }

        has_changes = watcher.has_changes_since(1500)

        assert has_changes is True

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-HAS_CHANGES_SINCE_FA")
    def test_has_changes_since_false(self, watcher: SettingsFileWatcher) -> None:
        """指定時刻以降変更無しテスト"""
        watcher._file_states = {
            "file1.yaml": {"mtime": 1000},
            "file2.yml": {"mtime": 1200},  # 全て指定時刻より古い
        }

        has_changes = watcher.has_changes_since(1500)

        assert has_changes is False

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-HAS_CHANGES_SINCE_EM")
    def test_has_changes_since_empty_states(self, watcher: SettingsFileWatcher) -> None:
        """空状態での変更確認テスト"""
        has_changes = watcher.has_changes_since(1500)

        assert has_changes is False

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_FILE_NAMES")
    def test_get_file_names(self, watcher: SettingsFileWatcher) -> None:
        """ファイル名リスト取得テスト"""
        watcher._file_states = {
            "キャラクター.yaml": {"mtime": 1000},
            "世界観.yml": {"mtime": 2000},
            "用語集.yaml": {"mtime": 3000},
        }

        file_names = watcher.get_file_names()

        # ソートされた結果が返される
        expected_names = ["キャラクター.yaml", "世界観.yml", "用語集.yaml"]
        assert file_names == expected_names

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_FILE_NAMES_EMPTY")
    def test_get_file_names_empty(self, watcher: SettingsFileWatcher) -> None:
        """空のファイル名リスト取得テスト"""
        file_names = watcher.get_file_names()

        assert file_names == []

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-IS_WATCHING_TRUE")
    def test_is_watching_true(self, watcher: SettingsFileWatcher) -> None:
        """監視中判定(True)テスト"""
        watcher._file_states = {"test.yaml": {"mtime": 1000}}

        assert watcher.is_watching("test.yaml") is True

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-IS_WATCHING_FALSE")
    def test_is_watching_false(self, watcher: SettingsFileWatcher) -> None:
        """監視中判定(False)テスト"""
        watcher._file_states = {"other.yaml": {"mtime": 1000}}

        assert watcher.is_watching("test.yaml") is False

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_LAST_CHECK_TIME_")
    def test_get_last_check_time_none_initial(self, watcher: SettingsFileWatcher) -> None:
        """初期状態での最終チェック時刻取得テスト"""
        assert watcher.get_last_check_time() is None

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_LAST_CHECK_TIME_")
    def test_get_last_check_time_after_initialization(
        self, watcher: SettingsFileWatcher, mock_repository: Mock
    ) -> None:
        """初期化後の最終チェック時刻取得テスト"""
        mock_repository.exists.return_value = True
        mock_repository.is_directory.return_value = True
        mock_repository.list_files.return_value = []

        watcher.initialize_file_states()

        last_check_time = watcher.get_last_check_time()
        assert last_check_time is not None
        assert isinstance(last_check_time, float)

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-VALIDATE_PROJECT_STR")
    def test_validate_project_structure_success(self, watcher: SettingsFileWatcher, mock_repository: Mock) -> None:
        """プロジェクト構造検証成功テスト"""
        mock_repository.exists.return_value = True
        mock_repository.is_directory.return_value = True

        # 例外が発生しないことを確認
        watcher.validate_project_structure()

        mock_repository.exists.assert_called_once_with("test_project")
        mock_repository.is_directory.assert_called_once_with("test_project")

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-VALIDATE_PROJECT_STR")
    def test_validate_project_structure_not_exists(self, watcher: SettingsFileWatcher, mock_repository: Mock) -> None:
        """プロジェクトルート存在しない場合の検証エラーテスト"""
        mock_repository.exists.return_value = False

        with pytest.raises(DomainException, match="プロジェクトルートが存在しません: test_project"):
            watcher.validate_project_structure()

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-VALIDATE_PROJECT_STR")
    def test_validate_project_structure_not_directory(
        self, watcher: SettingsFileWatcher, mock_repository: Mock
    ) -> None:
        """プロジェクトルートがディレクトリでない場合の検証エラーテスト"""
        mock_repository.exists.return_value = True
        mock_repository.is_directory.return_value = False

        with pytest.raises(DomainException, match="プロジェクトルートがディレクトリではありません: test_project"):
            watcher.validate_project_structure()

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_CHANGE_SUMMARY_N")
    def test_get_change_summary_no_changes(self, watcher: SettingsFileWatcher) -> None:
        """変更なしのサマリー生成テスト"""
        changes = []

        summary = watcher.get_change_summary(changes)

        assert summary == "変更はありません"

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_CHANGE_SUMMARY_S")
    def test_get_change_summary_single_type_changes(self, watcher: SettingsFileWatcher) -> None:
        """単一タイプ変更のサマリー生成テスト"""
        changes = [
            FileChangeEvent("/test/file1.yaml", "ADDED", project_now().datetime),
            FileChangeEvent("/test/file2.yaml", "ADDED", project_now().datetime),
        ]

        summary = watcher.get_change_summary(changes)

        assert summary == "2件の新規ファイルを検出しました"

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_CHANGE_SUMMARY_M")
    def test_get_change_summary_mixed_changes(self, watcher: SettingsFileWatcher) -> None:
        """複合変更のサマリー生成テスト"""
        changes = [
            FileChangeEvent("/test/file1.yaml", "ADDED", project_now().datetime),
            FileChangeEvent("/test/file2.yaml", "MODIFIED", project_now().datetime),
            FileChangeEvent("/test/file3.yaml", "MODIFIED", project_now().datetime),
            FileChangeEvent("/test/file4.yaml", "DELETED", project_now().datetime),
        ]

        summary = watcher.get_change_summary(changes)

        assert "1件の新規ファイル" in summary
        assert "2件の変更" in summary
        assert "1件の削除" in summary
        assert "を検出しました" in summary

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-GET_CHANGE_SUMMARY_A")
    def test_get_change_summary_all_types(self, watcher: SettingsFileWatcher) -> None:
        """全タイプ変更のサマリー生成テスト"""
        changes = [
            FileChangeEvent("/test/new.yaml", "ADDED", project_now().datetime),
            FileChangeEvent("/test/modified.yaml", "MODIFIED", project_now().datetime),
            FileChangeEvent("/test/deleted.yaml", "DELETED", project_now().datetime),
        ]

        summary = watcher.get_change_summary(changes)

        expected_parts = ["1件の新規ファイル", "1件の変更", "1件の削除"]
        for part in expected_parts:
            assert part in summary
        assert "を検出しました" in summary

    @pytest.mark.spec("SPEC-SETTINGS_FILE_WATCHER-CREATE_CHANGE_EVENT")
    def test_create_change_event(self, watcher: SettingsFileWatcher) -> None:
        """変更イベント作成テスト"""
        file_name = "test.yaml"
        change_type = FileChangeType.MODIFIED
        details = {"test_key": "test_value"}

        event = watcher._create_change_event(file_name, change_type, details)

        assert event.file_name == file_name
        assert event.change_type == change_type
        assert event.details == details
        assert isinstance(event.timestamp, datetime)
