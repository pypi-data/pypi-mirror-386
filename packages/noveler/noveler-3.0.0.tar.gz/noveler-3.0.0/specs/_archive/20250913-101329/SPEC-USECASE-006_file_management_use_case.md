# ファイル管理ユースケース仕様書

## 概要
`FileManagementUseCase`は、小説プロジェクトのファイルとディレクトリを管理するユースケースです。ファイルの作成・移動・削除、バックアップ管理、アーカイブ処理、ファイル整合性チェック、一括操作を包括的に提供し、プロジェクトファイルの安全で効率的な管理を実現します。

## クラス設計

### FileManagementUseCase

**責務**
- ファイルとディレクトリの操作
- バックアップの作成と復元
- アーカイブの管理
- ファイル整合性の検証
- 一括ファイル操作
- ファイル命名規則の適用

## データ構造

### FileOperation (Enum)
```python
class FileOperation(Enum):
    CREATE = "create"            # 作成
    MOVE = "move"                # 移動
    COPY = "copy"                # コピー
    DELETE = "delete"            # 削除
    RENAME = "rename"            # 名前変更
    ARCHIVE = "archive"          # アーカイブ
    RESTORE = "restore"          # 復元
```

### FileType (Enum)
```python
class FileType(Enum):
    MANUSCRIPT = "manuscript"    # 原稿
    PLOT = "plot"                # プロット
    SETTING = "setting"          # 設定
    MANAGEMENT = "management"    # 管理資料
    BACKUP = "backup"            # バックアップ
    TEMPLATE = "template"        # テンプレート
```

### FileInfo (DataClass)
```python
@dataclass
class FileInfo:
    path: Path                   # ファイルパス
    file_type: FileType          # ファイルタイプ
    size: int                    # ファイルサイズ
    created_at: datetime         # 作成日時
    modified_at: datetime        # 更新日時
    checksum: str                # チェックサム
    metadata: dict[str, any]     # メタデータ
    is_valid: bool = True        # 有効性
    warnings: list[str] = []     # 警告
```

### FileManagementRequest (DataClass)
```python
@dataclass
class FileManagementRequest:
    project_name: str            # プロジェクト名
    operation: FileOperation     # 操作タイプ
    target_files: list[str]      # 対象ファイル
    options: dict[str, any] = {} # オプション
    dry_run: bool = False        # ドライラン
    force: bool = False          # 強制実行
```

### FileManagementResponse (DataClass)
```python
@dataclass
class FileManagementResponse:
    success: bool                # 処理成功フラグ
    processed_files: list[str]   # 処理されたファイル
    skipped_files: list[str]     # スキップされたファイル
    errors: list[FileError]      # エラー情報
    operation_log: list[str]     # 操作ログ
    statistics: dict[str, int]   # 統計情報
```

## パブリックメソッド

### execute_file_operation()

**シグネチャ**
```python
def execute_file_operation(
    self,
    request: FileManagementRequest
) -> FileManagementResponse:
```

**目的**
指定されたファイル操作を実行する。

**引数**
- `request`: ファイル管理リクエスト

**戻り値**
- `FileManagementResponse`: 操作結果

**処理フロー**
1. **権限確認**: 操作権限の確認
2. **対象検証**: ファイルの存在と状態確認
3. **操作準備**: 必要な準備処理
4. **操作実行**: 指定された操作の実行
5. **整合性確認**: 操作後の整合性チェック
6. **結果記録**: 操作ログの記録

### create_backup()

**シグネチャ**
```python
def create_backup(
    self,
    project_name: str,
    backup_type: str = "full",
    description: str = ""
) -> BackupInfo:
```

**目的**
プロジェクトのバックアップを作成する。

### restore_from_backup()

**シグネチャ**
```python
def restore_from_backup(
    self,
    project_name: str,
    backup_id: str,
    restore_options: dict[str, any] = {}
) -> bool:
```

**目的**
バックアップから復元する。

### verify_file_integrity()

**シグネチャ**
```python
def verify_file_integrity(
    self,
    project_name: str,
    file_patterns: list[str] = []
) -> IntegrityReport:
```

**目的**
ファイルの整合性を検証する。

### organize_files()

**シグネチャ**
```python
def organize_files(
    self,
    project_name: str,
    organization_rules: dict[str, any]
) -> OrganizationResult:
```

**目的**
ファイルを整理・再配置する。

## プライベートメソッド

### _validate_file_operation()

**シグネチャ**
```python
def _validate_file_operation(
    self,
    operation: FileOperation,
    target_files: list[str]
) -> ValidationResult:
```

**目的**
ファイル操作の妥当性を検証する。

### _apply_naming_convention()

**シグネチャ**
```python
def _apply_naming_convention(
    self,
    file_path: Path,
    file_type: FileType
) -> Path:
```

**目的**
ファイル命名規則を適用する。

**命名規則**
```python
naming_conventions = {
    FileType.MANUSCRIPT: "第{episode_number:03d}話_{title}.md",
    FileType.PLOT: "{type}_{identifier}.yaml",
    FileType.SETTING: "{category}_{name}.yaml",
    FileType.BACKUP: "{project}_{date}_{time}_{type}.zip"
}
```

### _calculate_checksum()

**シグネチャ**
```python
def _calculate_checksum(
    self,
    file_path: Path
) -> str:
```

**目的**
ファイルのチェックサムを計算する。

### _create_file_metadata()

**シグネチャ**
```python
def _create_file_metadata(
    self,
    file_path: Path,
    file_type: FileType
) -> dict[str, any]:
```

**目的**
ファイルメタデータを作成する。

### _handle_file_conflicts()

**シグネチャ**
```python
def _handle_file_conflicts(
    self,
    source: Path,
    destination: Path,
    conflict_strategy: str
) -> Path:
```

**目的**
ファイル競合を処理する。

## ファイル操作詳細

### バックアップ戦略
```python
backup_strategies = {
    "full": {
        "description": "完全バックアップ",
        "includes": ["**/*"],
        "compression": "high"
    },
    "incremental": {
        "description": "増分バックアップ",
        "includes": ["modified_since_last"],
        "compression": "normal"
    },
    "manuscript_only": {
        "description": "原稿のみ",
        "includes": ["40_原稿/**/*.md"],
        "compression": "low"
    }
}
```

### アーカイブ処理
```python
archive_rules = {
    "old_drafts": {
        "condition": "modified_days > 90 and status == 'draft'",
        "destination": "backup/old_drafts",
        "compress": True
    },
    "completed_episodes": {
        "condition": "status == 'published' and days_since_publish > 30",
        "destination": "backup/published",
        "compress": False
    }
}
```

## 依存関係

### ドメインサービス
- `FileValidator`: ファイル検証
- `ChecksumCalculator`: チェックサム計算
- `NamingConventionService`: 命名規則サービス

### インフラストラクチャ
- `FileSystemService`: ファイルシステム操作
- `CompressionService`: 圧縮・解凍サービス
- `StorageService`: ストレージ管理

### リポジトリ
- `FileMetadataRepository`: ファイルメタデータ管理
- `BackupRepository`: バックアップ情報管理
- `OperationLogRepository`: 操作ログ管理

## 設計原則遵守

### DDD準拠
- ✅ エンティティ（`FileInfo`）の適切な使用
- ✅ 値オブジェクト（列挙型）の活用
- ✅ ドメインサービスの適切な活用
- ✅ リポジトリパターンによるデータアクセス抽象化

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的なエラーハンドリング
- ✅ 型安全な実装
- ✅ 列挙型による型安全性

## 使用例

```python
# 依存関係の準備
file_validator = FileValidator()
checksum_calculator = ChecksumCalculator()
naming_convention_service = NamingConventionService()
file_system_service = FileSystemService()
compression_service = CompressionService()
storage_service = StorageService()
file_metadata_repo = FileMetadataRepository()
backup_repo = BackupRepository()
operation_log_repo = OperationLogRepository()

# ユースケース作成
use_case = FileManagementUseCase(
    file_validator=file_validator,
    checksum_calculator=checksum_calculator,
    naming_convention_service=naming_convention_service,
    file_system_service=file_system_service,
    compression_service=compression_service,
    storage_service=storage_service,
    file_metadata_repository=file_metadata_repo,
    backup_repository=backup_repo,
    operation_log_repository=operation_log_repo
)

# ファイルの移動操作
move_request = FileManagementRequest(
    project_name="fantasy_adventure",
    operation=FileOperation.MOVE,
    target_files=[
        "40_原稿/第001話_冒険の始まり.md",
        "40_原稿/第002話_出会い.md"
    ],
    options={
        "destination": "40_原稿/第1章",
        "create_directory": True,
        "preserve_metadata": True
    },
    dry_run=True
)

# ドライラン実行
dry_response = use_case.execute_file_operation(move_request)

if dry_response.success:
    print("=== 移動プレビュー ===")
    for file in dry_response.processed_files:
        print(f"  移動予定: {file}")

    if input("実行しますか？ [y/N]: ").lower() == 'y':
        move_request.dry_run = False
        response = use_case.execute_file_operation(move_request)
        print(f"移動完了: {len(response.processed_files)}ファイル")

# フルバックアップの作成
backup_info = use_case.create_backup(
    project_name="fantasy_adventure",
    backup_type="full",
    description="第1部完成記念バックアップ"
)

print(f"\nバックアップ作成完了:")
print(f"  ID: {backup_info.backup_id}")
print(f"  サイズ: {backup_info.size / 1024 / 1024:.1f}MB")
print(f"  ファイル数: {backup_info.file_count}")
print(f"  保存先: {backup_info.path}")

# ファイル整合性チェック
integrity_report = use_case.verify_file_integrity(
    project_name="fantasy_adventure",
    file_patterns=["40_原稿/**/*.md", "50_管理資料/**/*.yaml"]
)

print(f"\n=== 整合性チェック結果 ===")
print(f"チェック対象: {integrity_report.total_files}ファイル")
print(f"正常: {integrity_report.valid_files}ファイル")

if integrity_report.issues:
    print(f"\n⚠️ 問題検出: {len(integrity_report.issues)}件")
    for issue in integrity_report.issues:
        print(f"  - {issue.file}: {issue.description}")

# ファイル整理
organization_rules = {
    "group_by_chapter": True,
    "archive_old_drafts": True,
    "normalize_names": True,
    "remove_duplicates": True
}

organization_result = use_case.organize_files(
    project_name="fantasy_adventure",
    organization_rules=organization_rules
)

print(f"\n=== ファイル整理結果 ===")
print(f"移動: {organization_result.moved_count}ファイル")
print(f"リネーム: {organization_result.renamed_count}ファイル")
print(f"アーカイブ: {organization_result.archived_count}ファイル")
print(f"重複削除: {organization_result.duplicates_removed}ファイル")

# 一括削除（古い下書き）
delete_request = FileManagementRequest(
    project_name="fantasy_adventure",
    operation=FileOperation.DELETE,
    target_files=[],  # 条件で自動選択
    options={
        "condition": "file_type == 'draft' and age_days > 180",
        "move_to_trash": True,
        "confirm_each": False
    }
)

# 削除対象の確認
targets = use_case.find_files_by_condition(
    project_name="fantasy_adventure",
    condition=delete_request.options["condition"]
)

if targets:
    print(f"\n削除対象: {len(targets)}ファイル")
    for target in targets[:5]:  # 最初の5件表示
        print(f"  - {target}")

    if input(f"\n{len(targets)}ファイルを削除しますか？ [y/N]: ").lower() == 'y':
        delete_request.target_files = targets
        delete_response = use_case.execute_file_operation(delete_request)
        print(f"削除完了: {len(delete_response.processed_files)}ファイル")

# バックアップからの復元
available_backups = use_case.list_backups("fantasy_adventure")

print(f"\n=== 利用可能なバックアップ ===")
for backup in available_backups:
    print(f"{backup.backup_id}: {backup.created_at} - {backup.description}")

# 特定ファイルのみ復元
restore_success = use_case.restore_from_backup(
    project_name="fantasy_adventure",
    backup_id=backup_info.backup_id,
    restore_options={
        "files": ["40_原稿/第010話_*.md"],
        "overwrite": False,
        "restore_to": "restored_files"
    }
)

if restore_success:
    print("復元完了")
```

## ファイル命名規則

### エピソードファイル
```
第{番号:03d}話_{タイトル}.md
例: 第001話_冒険の始まり.md
```

### 設定ファイル
```
{カテゴリ}_{名前}.yaml
例: キャラクター_主人公.yaml
```

### バックアップファイル
```
{プロジェクト}_{日付}_{時刻}_{タイプ}.zip
例: fantasy_adventure_20240120_143052_full.zip
```

## エラーハンドリング

### ファイル競合
```python
if destination.exists() and not request.force:
    if request.options.get("conflict_strategy") == "rename":
        destination = self._generate_unique_name(destination)
    elif request.options.get("conflict_strategy") == "skip":
        skipped_files.append(str(source))
        continue
    else:
        raise FileConflictError(f"ファイルが既に存在: {destination}")
```

### 権限エラー
```python
try:
    self.file_system_service.move(source, destination)
except PermissionError:
    if request.options.get("skip_permission_errors"):
        logger.warning(f"権限エラーをスキップ: {source}")
        skipped_files.append(str(source))
    else:
        raise
```

## パフォーマンス最適化

### バッチ処理
```python
def _process_files_batch(self, files: list[Path], operation: callable):
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for file in files:
            future = executor.submit(operation, file)
            futures.append((file, future))

        for file, future in futures:
            try:
                result = future.result(timeout=30)
                yield file, result
            except Exception as e:
                yield file, FileOperationError(str(e))
```

### 増分バックアップ
```python
def _create_incremental_backup(self, project_path: Path, last_backup: BackupInfo):
    changed_files = []
    for file in project_path.rglob("*"):
        if file.is_file() and file.stat().st_mtime > last_backup.created_at.timestamp():
            changed_files.append(file)

    # 変更されたファイルのみバックアップ
    return self._create_backup_archive(changed_files, "incremental")
```

## テスト観点

### 単体テスト
- ファイル操作の正確性
- 命名規則の適用
- チェックサム計算
- 競合処理
- エラー条件

### 統合テスト
- 大量ファイルの処理
- バックアップと復元
- 整合性チェック
- 並行処理の安全性

## 品質基準

- **安全性**: データ損失の防止
- **信頼性**: 確実なバックアップと復元
- **効率性**: 大量ファイルの高速処理
- **整合性**: ファイル状態の一貫性維持
- **追跡性**: 全操作の詳細なログ記録
