# SPEC-GENERAL-023: ローカルファイルシステムリポジトリ仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、ローカルファイルシステムの操作を統一的なインターフェースで提供する。ファイル・ディレクトリ操作の抽象化により、アプリケーション層とドメイン層をファイルシステム固有の実装詳細から分離する。

### 1.2 スコープ
- ファイル・ディレクトリの作成・読み込み・更新・削除（CRUD）操作
- パス管理とバリデーション機能
- ファイル内容の読み書き（テキスト・バイナリ）
- ディレクトリ探索と検索機能
- ファイルメタデータ管理（サイズ、更新日時、権限等）
- アトミックファイル操作（排他制御・安全な更新）
- バックアップ・復元・アーカイブ機能

### 1.3 アーキテクチャ位置
```
Domain Layer
├── FileSystemEntity (Aggregate Root)              ← Infrastructure Layer
├── FilePath (Value Object)                       └── LocalFileSystemRepository
├── FileContent (Value Object)                    └── MemoryFileSystemRepository (テスト用)
├── FileMetadata (Value Object)                   └── FileSystemRepositoryFactory
└── DirectoryInfo (Value Object)
```

### 1.4 ビジネス価値
- **操作の安全性**: アトミック操作による一貫性保証とデータ保護
- **開発効率**: 統一インターフェースによる開発・テストの効率化
- **拡張性**: 将来的なクラウドストレージ対応への道筋確保
- **保守性**: ファイルシステム操作の一元管理によるメンテナンス性向上

## 2. 機能仕様

### 2.1 基本ファイル操作
```python
# CRUD操作
def create_file(
    file_path: FilePath,
    content: FileContent,
    overwrite: bool = False
) -> bool

def read_file(file_path: FilePath) -> FileContent | None

def update_file(
    file_path: FilePath,
    content: FileContent,
    create_backup: bool = True
) -> bool

def delete_file(file_path: FilePath, safe_delete: bool = True) -> bool

# 存在チェック
def file_exists(file_path: FilePath) -> bool
def is_readable(file_path: FilePath) -> bool
def is_writable(file_path: FilePath) -> bool
```

### 2.2 ディレクトリ操作
```python
# ディレクトリ管理
def create_directory(
    dir_path: FilePath,
    parents: bool = True,
    mode: int = 0o755
) -> bool

def list_directory(
    dir_path: FilePath,
    pattern: str | None = None,
    recursive: bool = False
) -> list[FilePath]

def delete_directory(
    dir_path: FilePath,
    recursive: bool = False,
    safe_delete: bool = True
) -> bool

def directory_exists(dir_path: FilePath) -> bool
def is_empty_directory(dir_path: FilePath) -> bool
```

### 2.3 ファイル検索・フィルタリング
```python
# 検索機能
def find_files(
    search_path: FilePath,
    pattern: str,
    file_type: FileType | None = None,
    max_results: int | None = None
) -> list[FilePath]

def find_files_by_content(
    search_path: FilePath,
    content_pattern: str,
    file_extensions: list[str] | None = None
) -> list[FilePath]

def filter_files_by_metadata(
    file_paths: list[FilePath],
    size_range: tuple[int, int] | None = None,
    date_range: tuple[datetime, datetime] | None = None
) -> list[FilePath]
```

### 2.4 メタデータ管理
```python
# ファイル情報取得
def get_file_metadata(file_path: FilePath) -> FileMetadata | None
def get_file_size(file_path: FilePath) -> int | None
def get_file_modified_time(file_path: FilePath) -> datetime | None
def get_file_permissions(file_path: FilePath) -> int | None

# メタデータ更新
def set_file_permissions(file_path: FilePath, permissions: int) -> bool
def set_file_modified_time(file_path: FilePath, modified_time: datetime) -> bool
```

### 2.5 アトミック操作・安全な更新
```python
# アトミック操作
def atomic_write(
    file_path: FilePath,
    content: FileContent,
    backup_extension: str = ".backup"
) -> bool

def atomic_move(source_path: FilePath, target_path: FilePath) -> bool
def atomic_copy(source_path: FilePath, target_path: FilePath) -> bool

# ロック機能
def acquire_file_lock(file_path: FilePath, timeout: float = 5.0) -> bool
def release_file_lock(file_path: FilePath) -> bool
def is_file_locked(file_path: FilePath) -> bool
```

### 2.6 バックアップ・アーカイブ
```python
# バックアップ機能
def create_backup(
    source_path: FilePath,
    backup_dir: FilePath | None = None,
    timestamp: bool = True
) -> FilePath | None

def restore_from_backup(
    original_path: FilePath,
    backup_path: FilePath
) -> bool

# アーカイブ機能
def create_archive(
    source_paths: list[FilePath],
    archive_path: FilePath,
    compression: ArchiveType = ArchiveType.ZIP
) -> bool

def extract_archive(
    archive_path: FilePath,
    target_dir: FilePath
) -> list[FilePath]
```

## 3. データ構造仕様

### 3.1 ファイルパス構造
```python
# FilePath値オブジェクト
@dataclass(frozen=True)
class FilePath:
    path: str

    def __post_init__(self):
        if not self._is_valid_path():
            raise ValueError(f"Invalid file path: {self.path}")

    @property
    def parent(self) -> FilePath:
        """親ディレクトリのパスを取得"""

    @property
    def name(self) -> str:
        """ファイル名を取得"""

    @property
    def suffix(self) -> str:
        """ファイル拡張子を取得"""

    @property
    def stem(self) -> str:
        """拡張子を除いたファイル名を取得"""

    def join(self, *paths: str) -> FilePath:
        """パスを結合"""

    def resolve(self) -> FilePath:
        """絶対パスに解決"""

    def is_absolute(self) -> bool:
        """絶対パスかどうか判定"""
```

### 3.2 ファイル内容構造
```python
# FileContent値オブジェクト
@dataclass(frozen=True)
class FileContent:
    content: bytes | str
    encoding: str = "utf-8"
    content_type: ContentType = ContentType.TEXT

    @classmethod
    def from_text(cls, text: str, encoding: str = "utf-8") -> FileContent:
        """テキストからFileContentを作成"""

    @classmethod
    def from_bytes(cls, data: bytes) -> FileContent:
        """バイナリデータからFileContentを作成"""

    def to_text(self) -> str:
        """テキストとして取得"""

    def to_bytes(self) -> bytes:
        """バイナリデータとして取得"""

    @property
    def size(self) -> int:
        """コンテンツサイズを取得"""
```

### 3.3 ファイルメタデータ構造
```python
# FileMetadata値オブジェクト
@dataclass(frozen=True)
class FileMetadata:
    file_path: FilePath
    size: int
    created_time: datetime
    modified_time: datetime
    accessed_time: datetime
    permissions: int
    is_directory: bool
    is_symlink: bool
    owner: str | None
    group: str | None

    @property
    def size_human_readable(self) -> str:
        """人間が読みやすいサイズ表示"""

    def is_older_than(self, days: int) -> bool:
        """指定日数より古いかどうか判定"""

    def has_write_permission(self) -> bool:
        """書き込み権限があるかどうか判定"""
```

### 3.4 ディレクトリ情報構造
```python
# DirectoryInfo値オブジェクト
@dataclass(frozen=True)
class DirectoryInfo:
    directory_path: FilePath
    total_files: int
    total_directories: int
    total_size: int
    file_types: dict[str, int]  # 拡張子別ファイル数
    largest_file: FilePath | None
    newest_file: FilePath | None
    oldest_file: FilePath | None

    @property
    def is_empty(self) -> bool:
        """空ディレクトリかどうか判定"""

    def get_file_type_distribution(self) -> dict[str, float]:
        """ファイルタイプの分布（パーセンテージ）"""
```

## 4. 技術仕様

### 4.1 依存関係
```python
# 標準ライブラリ
import os
import shutil
import pathlib
from datetime import datetime
from pathlib import Path
from typing import Any
from __future__ import annotations
import tempfile
import zipfile
import tarfile
import fcntl  # Unix系でのファイルロック
import msvcrt  # Windows系でのファイルロック

# ドメイン層
from domain.value_objects.file_path import FilePath
from domain.value_objects.file_content import FileContent, ContentType
from domain.value_objects.file_metadata import FileMetadata
from domain.value_objects.directory_info import DirectoryInfo

# エナム
from domain.enums.file_type import FileType
from domain.enums.archive_type import ArchiveType
```

### 4.2 エラーハンドリング
```python
# カスタム例外
class FileSystemRepositoryError(Exception):
    """ファイルシステムリポジトリ関連エラー"""
    pass

class FileOperationError(FileSystemRepositoryError):
    """ファイル操作エラー"""
    pass

class DirectoryOperationError(FileSystemRepositoryError):
    """ディレクトリ操作エラー"""
    pass

class PathValidationError(FileSystemRepositoryError):
    """パス検証エラー"""
    pass

class PermissionError(FileSystemRepositoryError):
    """権限エラー"""
    pass

class FileLockError(FileSystemRepositoryError):
    """ファイルロックエラー"""
    pass

class BackupOperationError(FileSystemRepositoryError):
    """バックアップ操作エラー"""
    pass

class ArchiveOperationError(FileSystemRepositoryError):
    """アーカイブ操作エラー"""
    pass
```

### 4.3 設定・バリデーション
```python
# 設定クラス
@dataclass
class FileSystemConfig:
    max_file_size_mb: int = 100
    default_encoding: str = "utf-8"
    backup_retention_days: int = 30
    enable_file_locking: bool = True
    safe_delete_to_trash: bool = True
    atomic_write_temp_suffix: str = ".tmp"

def validate_file_path(self, file_path: FilePath) -> bool:
    """ファイルパスの妥当性検証"""

def validate_file_size(self, size_bytes: int) -> bool:
    """ファイルサイズの妥当性検証"""

def validate_permissions(self, permissions: int) -> bool:
    """権限の妥当性検証"""
```

## 5. パフォーマンス要件

### 5.1 応答時間
- 小ファイル読み込み（1KB以下）: 10ms以内
- 中ファイル読み込み（1MB以下）: 100ms以内
- 大ファイル読み込み（10MB以下）: 1秒以内
- ディレクトリ一覧取得: 50ms以内（1000ファイル以下）
- ファイル検索: 500ms以内（10000ファイル対象）

### 5.2 メモリ使用量
- 小ファイル（1KB以下）: ファイルサイズ × 2以内
- 中ファイル（1MB以下）: ファイルサイズ × 1.5以内
- 大ファイル（10MB以上）: チャンク処理で最大10MB
- ディレクトリ一覧: ファイル数 × 1KB以内

### 5.3 並行処理
- 同時ファイル読み込み: 10スレッドまで対応
- ファイルロック: デッドロック回避機構
- アトミック操作: 並行アクセス時の一貫性保証

## 6. 品質保証

### 6.1 データ整合性
- アトミック書き込みによる部分更新防止
- ファイルロックによる並行アクセス制御
- バックアップ機能による障害対策
- チェックサム検証による破損検出

### 6.2 エラー回復
```python
# データ修復機能
def repair_corrupted_file(self, file_path: FilePath) -> bool:
    """破損ファイルの修復（バックアップから）"""

def verify_file_integrity(self, file_path: FilePath) -> bool:
    """ファイル整合性チェック"""

def auto_recover_from_backup(self, file_path: FilePath) -> bool:
    """バックアップからの自動復旧"""
```

### 6.3 監査・ログ機能
```python
def log_file_operation(
    self,
    operation: str,
    file_path: FilePath,
    success: bool,
    details: str | None = None
) -> None:
    """ファイル操作のログ記録"""

def get_operation_history(
    self,
    file_path: FilePath,
    days: int = 7
) -> list[dict[str, Any]]:
    """操作履歴の取得"""
```

## 7. セキュリティ

### 7.1 パスセキュリティ
- パストラバーサル攻撃の防止
- シンボリックリンク攻撃の防止
- 許可されたディレクトリ外へのアクセス拒否
- 危険なファイル名の検出・拒否

### 7.2 権限管理
- ファイル・ディレクトリ権限の適切な設定
- 実行権限の慎重な管理
- 一時ファイルの安全な権限設定
- セキュアな削除（データ完全消去オプション）

### 7.3 情報保護
```python
def secure_delete(self, file_path: FilePath, passes: int = 3) -> bool:
    """セキュアな削除（データ上書き）"""

def sanitize_filename(self, filename: str) -> str:
    """ファイル名のサニタイズ"""

def check_malicious_content(self, content: FileContent) -> bool:
    """悪意のあるコンテンツの検出"""
```

## 8. 拡張性・統合性

### 8.1 プラガブル・アーキテクチャ
```python
# 抽象インターフェース
class FileSystemRepository(ABC):
    @abstractmethod
    def create_file(self, file_path: FilePath, content: FileContent) -> bool:
        pass

    @abstractmethod
    def read_file(self, file_path: FilePath) -> FileContent | None:
        pass

    @abstractmethod
    def update_file(self, file_path: FilePath, content: FileContent) -> bool:
        pass

    @abstractmethod
    def delete_file(self, file_path: FilePath) -> bool:
        pass
```

### 8.2 外部システム連携
- バージョン管理システム（Git）との統合
- クラウドストレージ（AWS S3、Google Cloud Storage）対応
- ネットワークファイルシステム（NFS、SMB）対応
- 暗号化ファイルシステム対応

### 8.3 監視・通知機能
- ファイルシステム監視（inotify、WatchService）
- 容量監視とアラート
- 操作統計とレポート
- 異常操作の検出・通知

## 9. 使用例

### 9.1 基本的なファイル操作例
```python
# リポジトリ作成
repo = FileSystemRepositoryFactory.create_local_repository()

# ファイル作成
content = FileContent.from_text("Hello, World!")
file_path = FilePath("/project/hello.txt")
repo.create_file(file_path, content)

# ファイル読み込み
loaded_content = repo.read_file(file_path)
print(loaded_content.to_text())  # "Hello, World!"

# ファイル更新
updated_content = FileContent.from_text("Hello, Updated World!")
repo.update_file(file_path, updated_content, create_backup=True)

# メタデータ取得
metadata = repo.get_file_metadata(file_path)
print(f"サイズ: {metadata.size_human_readable}")
```

### 9.2 ディレクトリ操作例
```python
# ディレクトリ作成
dir_path = FilePath("/project/documents")
repo.create_directory(dir_path, parents=True)

# ファイル一覧取得
files = repo.list_directory(dir_path, pattern="*.md", recursive=True)
for file in files:
    print(f"見つかったファイル: {file.name}")

# ディレクトリ情報取得
dir_info = repo.get_directory_info(dir_path)
print(f"総ファイル数: {dir_info.total_files}")
print(f"総サイズ: {dir_info.total_size}")
```

### 9.3 検索・フィルタリング例
```python
# ファイル検索
search_path = FilePath("/project")
found_files = repo.find_files(
    search_path,
    pattern="*.py",
    file_type=FileType.REGULAR,
    max_results=100
)

# 内容による検索
content_files = repo.find_files_by_content(
    search_path,
    content_pattern="def test_",
    file_extensions=[".py"]
)

# メタデータによるフィルタリング
today = datetime.now()
yesterday = today - timedelta(days=1)
recent_files = repo.filter_files_by_metadata(
    found_files,
    date_range=(yesterday, today)
)
```

### 9.4 アトミック操作・バックアップ例
```python
# アトミック書き込み
large_content = FileContent.from_text("大量のデータ..." * 1000)
repo.atomic_write(FilePath("/project/large_file.txt"), large_content)

# バックアップ作成
backup_path = repo.create_backup(
    FilePath("/project/important.txt"),
    timestamp=True
)
print(f"バックアップ作成: {backup_path}")

# アーカイブ作成
source_files = [
    FilePath("/project/file1.txt"),
    FilePath("/project/file2.txt"),
]
repo.create_archive(
    source_files,
    FilePath("/backups/project_backup.zip"),
    compression=ArchiveType.ZIP
)
```

## 10. テスト仕様

### 10.1 単体テスト
```python
class TestLocalFileSystemRepository:
    def test_create_and_read_file(self):
        """ファイル作成・読み込みテスト"""

    def test_update_file_with_backup(self):
        """バックアップ付きファイル更新テスト"""

    def test_directory_operations(self):
        """ディレクトリ操作テスト"""

    def test_file_search_and_filtering(self):
        """ファイル検索・フィルタリングテスト"""

    def test_metadata_management(self):
        """メタデータ管理テスト"""

    def test_atomic_operations(self):
        """アトミック操作テスト"""

    def test_file_locking(self):
        """ファイルロック機能テスト"""

    def test_backup_and_restore(self):
        """バックアップ・復元テスト"""

    def test_archive_operations(self):
        """アーカイブ操作テスト"""

    def test_error_handling(self):
        """エラーハンドリングテスト"""

class TestFileSystemRepositoryFactory:
    def test_factory_pattern(self):
        """ファクトリーパターンのテスト"""

    def test_memory_repository_for_testing(self):
        """テスト用メモリリポジトリのテスト"""
```

### 10.2 統合テスト
```python
class TestFileSystemRepositoryIntegration:
    def test_large_file_handling(self):
        """大容量ファイル処理テスト"""

    def test_concurrent_file_access(self):
        """並行ファイルアクセステスト"""

    def test_cross_platform_compatibility(self):
        """クロスプラットフォーム互換性テスト"""

    def test_performance_benchmarks(self):
        """パフォーマンステスト"""
```

### 10.3 エラーシナリオテスト
```python
def test_insufficient_disk_space(self):
    """ディスク容量不足時の処理テスト"""

def test_permission_denied_scenarios(self):
    """権限エラーシナリオテスト"""

def test_file_system_corruption_recovery(self):
    """ファイルシステム破損からの復旧テスト"""

def test_network_file_system_failures(self):
    """ネットワークファイルシステム障害テスト"""
```

## 11. 監視・メトリクス

### 11.1 運用メトリクス
```python
# 収集すべきメトリクス
metrics = {
    'file_operations': {
        'files_created_per_hour': 25,
        'files_read_per_hour': 150,
        'files_updated_per_hour': 40,
        'files_deleted_per_hour': 8
    },
    'performance_metrics': {
        'average_read_time_ms': 15,
        'average_write_time_ms': 35,
        'average_search_time_ms': 120,
        'cache_hit_rate': 0.78
    },
    'storage_metrics': {
        'total_files_managed': 5420,
        'total_storage_gb': 12.5,
        'backup_storage_gb': 3.8,
        'largest_file_mb': 45.2
    },
    'error_metrics': {
        'file_operation_errors_per_day': 3,
        'permission_errors_per_day': 1,
        'corruption_incidents_per_month': 0
    }
}
```

### 11.2 アラート条件
- ディスク使用量 > 90%
- ファイル操作エラー率 > 5%
- 大ファイル読み込み時間 > 5秒
- バックアップ失敗
- 権限エラー頻発（> 10回/日）

### 11.3 ヘルスチェック
```python
def health_check(self) -> dict[str, Any]:
    """リポジトリヘルスチェック"""
    return {
        'status': 'healthy',
        'file_system_accessible': True,
        'write_permissions_ok': True,
        'disk_usage_percentage': 45.2,
        'recent_errors': 0,
        'last_successful_operation': datetime.now().isoformat(),
        'backup_system_status': 'operational'
    }
```

## 12. 実装メモ

### 12.1 実装ファイル
- **メインクラス**: `scripts/infrastructure/repositories/local_file_system_repository.py`
- **テストファイル**: `tests/unit/infrastructure/repositories/test_local_file_system_repository.py`
- **統合テスト**: `tests/integration/test_file_system_repository_workflow.py`
- **ファクトリー**: `FileSystemRepositoryFactory` クラス内部実装

### 12.2 設計方針
- **DDD原則の厳格な遵守**: ファイルシステム操作の技術詳細とドメインロジックの完全分離
- **プラットフォーム抽象化**: Windows/Linux/macOS対応の統一インターフェース
- **安全性優先**: アトミック操作・バックアップ・検証による信頼性確保
- **パフォーマンス最適化**: 大容量ファイル・大量ファイルへの効率的対応

### 12.3 今後の改善点
- [ ] クラウドストレージ統合（AWS S3、Google Cloud Storage）
- [ ] 分散ファイルシステム対応（HDFS、GlusterFS）
- [ ] ファイル暗号化・復号化機能
- [ ] リアルタイム同期機能
- [ ] 重複除去（deduplication）機能
- [ ] ファイル圧縮・展開の自動化
- [ ] ネットワークファイルシステム最適化
- [ ] AIベースのファイル分類・整理機能
