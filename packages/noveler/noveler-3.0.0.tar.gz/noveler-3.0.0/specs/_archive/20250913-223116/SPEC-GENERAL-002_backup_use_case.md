# SPEC-GENERAL-002: バックアップユースケース仕様書

## 概要
`BackupUseCase`は、小説プロジェクトのバックアップ機能を提供するユースケースです。フル・増分・エピソード単位・選択的バックアップに対応し、圧縮・履歴記録・サイズ制限などの機能を提供します。

## クラス設計

### BackupUseCase

**責務**
- バックアップリクエストの処理
- バックアップタイプ別の実行制御
- 圧縮・サイズチェック・履歴記録
- エラーハンドリングとレスポンス構築

## データ構造

### BackupType (Enum)
```python
class BackupType(Enum):
    FULL = "full"           # 全体バックアップ
    INCREMENTAL = "incremental"  # 増分バックアップ
    EPISODE = "episode"     # エピソード単位
    SELECTIVE = "selective" # 選択的バックアップ
```

### BackupStatus (Enum)
```python
class BackupStatus(Enum):
    SUCCESS = "success"     # 成功
    FAILED = "failed"       # 失敗
    PARTIAL = "partial"     # 一部成功
```

### BackupRequest (DataClass)
```python
@dataclass
class BackupRequest:
    project_name: str                    # プロジェクト名
    backup_type: BackupType = FULL       # バックアップタイプ
    include_manuscripts: bool = True     # 原稿を含む
    include_settings: bool = True        # 設定を含む
    include_plots: bool = True           # プロットを含む
    compress: bool = True                # 圧縮フラグ
    episode_number: int | None = None    # エピソード番号
    max_size_mb: int | None = None       # 最大サイズ制限
    last_backup_time: datetime | None = None  # 前回バックアップ時刻
    record_history: bool = False         # 履歴記録フラグ
```

### BackupResponse (DataClass)
```python
@dataclass
class BackupResponse:
    status: BackupStatus                 # バックアップステータス
    backup_path: Path                    # バックアップファイルパス
    total_files: int                     # 総ファイル数
    total_size: int                      # 総サイズ（バイト）
    duration: float                      # 実行時間（秒）
    message: str                         # 結果メッセージ
    history_id: str | None = None        # 履歴ID
    errors: list[str] = None             # エラー一覧
```

## パブリックメソッド

### execute()

**シグネチャ**
```python
def execute(self, request: BackupRequest) -> BackupResponse:
```

**目的**
バックアップリクエストを受け取り、指定された設定でバックアップを実行する。

**引数**
- `request`: バックアップリクエスト

**戻り値**
- `BackupResponse`: バックアップ実行結果

**処理フロー**
1. プロジェクトの存在確認
2. バックアップディレクトリの準備
3. バックアップタイプ別の処理実行
4. 圧縮処理（必要に応じて）
5. サイズ制限チェック
6. 履歴記録（必要に応じて）
7. レスポンス構築

**例外処理**
- プロジェクト不存在時：`ValueError`
- ファイルアクセスエラー：`BackupStatus.FAILED`で返却
- 一部ファイルエラー：`BackupStatus.PARTIAL`で返却

## プライベートメソッド

### _prepare_backup_directory()

**目的**
タイムスタンプ付きのバックアップディレクトリを作成する。

**戻り値**
- `Path`: 作成されたバックアップディレクトリパス

### _execute_full_backup()

**目的**
プロジェクト全体のフルバックアップを実行する。

**処理内容**
- 全ディレクトリ・ファイルをコピー
- システムファイル（.、__pycache__）を除外
- エラーファイルを記録

### _execute_incremental_backup()

**目的**
前回バックアップ以降に変更されたファイルのみバックアップする。

**処理内容**
- `last_backup_time`以降の変更ファイルを特定
- 前回時刻未指定時はフルバックアップ実行
- ファイル変更時刻で判定

### _execute_episode_backup()

**目的**
指定されたエピソードのみバックアップする。

**処理内容**
- エピソード番号でエピソードを特定
- エピソードファイルを生成・保存
- 存在しないエピソードは`ValueError`

### _execute_selective_backup()

**目的**
選択された項目のみバックアップする。

**処理内容**
- `include_manuscripts`: 40_原稿ディレクトリ
- `include_settings`: 30_設定集ディレクトリ
- `include_plots`: 20_プロットディレクトリ
- 各項目は独立してエラー処理

### _compress_backup()

**目的**
バックアップディレクトリをZIP圧縮する。

**処理内容**
- ZIP_DEFLATED形式で圧縮
- 元ディレクトリを削除
- 相対パスでアーカイブ作成

### _calculate_total_size()

**目的**
バックアップの総サイズを計算する。

### _generate_message()

**目的**
バックアップタイプに応じた完了メッセージを生成する。

### _record_backup_history()

**目的**
バックアップ履歴を記録し、履歴IDを返す。

## 依存関係

### ドメイン層
- `EpisodeRepository`: エピソードリポジトリ
- `ProjectRepository`: プロジェクトリポジトリ
- `EpisodeNumber`: エピソード番号値オブジェクト

### 標準ライブラリ
- `shutil`: ファイル・ディレクトリ操作
- `zipfile`: ZIP圧縮
- `pathlib`: パス操作
- `dataclasses`: データクラス
- `enum`: 列挙型

## 設計原則遵守

### DDD準拠
- ✅ リポジトリパターンでデータアクセス抽象化
- ✅ 値オブジェクト（`EpisodeNumber`）の適切な使用
- ✅ ドメインロジックの明確な分離

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的なエラーハンドリング
- ✅ 型安全な実装

## 使用例

```python
# リポジトリの準備
project_repo = YamlProjectRepository()
episode_repo = YamlEpisodeRepository()
use_case = BackupUseCase(project_repo, episode_repo)

# フルバックアップ
request = BackupRequest(
    project_name="sample_novel",
    backup_type=BackupType.FULL,
    compress=True,
    record_history=True
)
response = use_case.execute(request)

if response.status == BackupStatus.SUCCESS:
    print(f"バックアップ完了: {response.backup_path}")
    print(f"ファイル数: {response.total_files}")
    print(f"サイズ: {response.total_size / 1024 / 1024:.1f}MB")
else:
    print(f"バックアップ失敗: {response.message}")
    for error in response.errors or []:
        print(f"エラー: {error}")

# エピソード単位バックアップ
episode_request = BackupRequest(
    project_name="sample_novel",
    backup_type=BackupType.EPISODE,
    episode_number=5,
    compress=False
)
episode_response = use_case.execute(episode_request)

# 選択的バックアップ
selective_request = BackupRequest(
    project_name="sample_novel",
    backup_type=BackupType.SELECTIVE,
    include_manuscripts=True,
    include_settings=False,
    include_plots=True,
    max_size_mb=100
)
selective_response = use_case.execute(selective_request)
```

## テスト観点

### 単体テスト
- 各バックアップタイプの正常処理
- プロジェクト不存在時のエラー処理
- ファイルアクセスエラー時の処理
- 圧縮機能の動作
- サイズ制限チェック
- 履歴記録機能

### 統合テスト
- 実際のプロジェクトファイルでのバックアップ
- リポジトリとの連携動作
- 大容量ファイルでの性能

## 品質基準

- **信頼性**: ファイルアクセスエラーの安全な処理
- **性能**: 大容量プロジェクトでの効率的なバックアップ
- **使いやすさ**: 明確なエラーメッセージと進捗表示
- **保守性**: 明確な責務分離と拡張可能な設計
- **セキュリティ**: パストラバーサル攻撃の防御
