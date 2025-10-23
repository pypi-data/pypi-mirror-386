# SPEC-EPISODE-014: エピソードリスト管理ユースケース仕様書

## 概要
`EpisodeListManagementUseCase`は、小説プロジェクトのエピソード一覧を管理するユースケースです。エピソードの作成・更新・削除、順序管理、ステータス追跡、メタデータ管理、一括操作を包括的に提供し、効率的なエピソード管理を実現します。

## クラス設計

### EpisodeListManagementUseCase

**責務**
- エピソード一覧の取得と表示
- エピソードの追加・更新・削除
- エピソード順序の管理と並び替え
- ステータスの一括更新
- メタデータの統合管理
- エピソード間の関連性管理

## データ構造

### EpisodeStatus (Enum)
```python
class EpisodeStatus(Enum):
    PLANNED = "planned"              # 計画中
    DRAFT = "draft"                  # 下書き
    WRITING = "writing"              # 執筆中
    REVIEW = "review"                # レビュー中
    COMPLETED = "completed"          # 完成
    PUBLISHED = "published"          # 公開済み
    ARCHIVED = "archived"            # アーカイブ
```

### EpisodeListView (Enum)
```python
class EpisodeListView(Enum):
    ALL = "all"                      # 全エピソード
    ACTIVE = "active"                # アクティブのみ
    PUBLISHED = "published"          # 公開済みのみ
    DRAFT = "draft"                  # 下書きのみ
    BY_CHAPTER = "by_chapter"        # 章別表示
    BY_STATUS = "by_status"          # ステータス別表示
```

### EpisodeInfo (DataClass)
```python
@dataclass
class EpisodeInfo:
    episode_number: int              # エピソード番号
    title: str                       # タイトル
    status: EpisodeStatus            # ステータス
    word_count: int                  # 文字数
    chapter: int | None              # 所属章
    created_at: datetime             # 作成日時
    updated_at: datetime             # 更新日時
    published_at: datetime | None    # 公開日時
    tags: list[str] = []             # タグ
    quality_score: float | None = None # 品質スコア
    view_count: int = 0              # 閲覧数
    file_path: Path | None = None    # ファイルパス
```

### EpisodeListRequest (DataClass)
```python
@dataclass
class EpisodeListRequest:
    project_name: str                # プロジェクト名
    view_type: EpisodeListView       # 表示タイプ
    filter_criteria: dict[str, any] = {} # フィルタ条件
    sort_by: str = "episode_number"  # ソート基準
    sort_order: str = "asc"          # ソート順
    page: int = 1                    # ページ番号
    per_page: int = 50               # ページあたり件数
    include_metadata: bool = True    # メタデータ含む
```

### EpisodeListResponse (DataClass)
```python
@dataclass
class EpisodeListResponse:
    success: bool                    # 処理成功フラグ
    episodes: list[EpisodeInfo]      # エピソード情報
    total_count: int                 # 総件数
    page_info: PageInfo              # ページング情報
    statistics: EpisodeStatistics    # 統計情報
    message: str = ""                # メッセージ
```

### EpisodeBulkOperation (DataClass)
```python
@dataclass
class EpisodeBulkOperation:
    operation_type: str              # 操作タイプ
    target_episodes: list[int]       # 対象エピソード番号
    parameters: dict[str, any]       # 操作パラメータ
    dry_run: bool = False            # ドライラン
```

## パブリックメソッド

### get_episode_list()

**シグネチャ**
```python
def get_episode_list(self, request: EpisodeListRequest) -> EpisodeListResponse:
```

**目的**
指定された条件でエピソード一覧を取得する。

**引数**
- `request`: エピソードリスト取得リクエスト

**戻り値**
- `EpisodeListResponse`: エピソード一覧情報

**処理フロー**
1. **プロジェクト検証**: プロジェクトの存在確認
2. **データ収集**: エピソード情報の収集
3. **フィルタリング**: 条件に基づくフィルタ
4. **ソート**: 指定基準でのソート
5. **ページング**: ページ分割処理
6. **統計計算**: 統計情報の生成
7. **レスポンス構築**: 結果の構築

### add_episode()

**シグネチャ**
```python
def add_episode(
    self,
    project_name: str,
    title: str,
    chapter: int | None = None,
    position: int | None = None
) -> EpisodeInfo:
```

**目的**
新しいエピソードを追加する。

### update_episode()

**シグネチャ**
```python
def update_episode(
    self,
    project_name: str,
    episode_number: int,
    updates: dict[str, any]
) -> bool:
```

**目的**
既存エピソードの情報を更新する。

### reorder_episodes()

**シグネチャ**
```python
def reorder_episodes(
    self,
    project_name: str,
    new_order: list[int]
) -> bool:
```

**目的**
エピソードの順序を変更する。

### execute_bulk_operation()

**シグネチャ**
```python
def execute_bulk_operation(
    self,
    project_name: str,
    operation: EpisodeBulkOperation
) -> BulkOperationResult:
```

**目的**
複数エピソードに対する一括操作を実行する。

## プライベートメソッド

### _collect_episode_data()

**シグネチャ**
```python
def _collect_episode_data(
    self,
    project_name: str
) -> list[EpisodeInfo]:
```

**目的**
プロジェクトの全エピソードデータを収集する。

### _apply_filters()

**シグネチャ**
```python
def _apply_filters(
    self,
    episodes: list[EpisodeInfo],
    filter_criteria: dict[str, any]
) -> list[EpisodeInfo]:
```

**目的**
フィルタ条件を適用してエピソードを絞り込む。

**フィルタ条件例**
```python
filter_criteria = {
    "status": ["draft", "writing"],
    "chapter": 3,
    "word_count_min": 3000,
    "word_count_max": 5000,
    "tags": ["重要", "クライマックス"],
    "date_range": {
        "start": datetime(2024, 1, 1),
        "end": datetime(2024, 12, 31)
    }
}
```

### _sort_episodes()

**シグネチャ**
```python
def _sort_episodes(
    self,
    episodes: list[EpisodeInfo],
    sort_by: str,
    sort_order: str
) -> list[EpisodeInfo]:
```

**目的**
指定された基準でエピソードをソートする。

### _calculate_statistics()

**シグネチャ**
```python
def _calculate_statistics(
    self,
    episodes: list[EpisodeInfo]
) -> EpisodeStatistics:
```

**目的**
エピソード一覧の統計情報を計算する。

**統計情報**
```python
statistics = {
    "total_episodes": int,
    "total_words": int,
    "average_words": float,
    "status_distribution": dict[str, int],
    "chapter_distribution": dict[int, int],
    "completion_rate": float,
    "publishing_rate": float,
    "recent_updates": int,
    "quality_metrics": dict[str, float]
}
```

### _validate_reorder()

**シグネチャ**
```python
def _validate_reorder(
    self,
    current_episodes: list[int],
    new_order: list[int]
) -> tuple[bool, str]:
```

**目的**
エピソード順序変更の妥当性を検証する。

## 一括操作

### ステータス一括更新
```python
bulk_status_update = EpisodeBulkOperation(
    operation_type="update_status",
    target_episodes=[1, 2, 3, 4, 5],
    parameters={
        "new_status": "review",
        "update_timestamp": True
    }
)
```

### 章の一括割り当て
```python
bulk_chapter_assign = EpisodeBulkOperation(
    operation_type="assign_chapter",
    target_episodes=[10, 11, 12, 13],
    parameters={
        "chapter": 3,
        "reorder_within_chapter": True
    }
)
```

### タグの一括追加
```python
bulk_tag_add = EpisodeBulkOperation(
    operation_type="add_tags",
    target_episodes=[15, 16, 17],
    parameters={
        "tags": ["重要", "伏線"],
        "merge": True
    }
)
```

## 依存関係

### ドメインサービス
- `EpisodeNumberingService`: エピソード番号管理
- `EpisodeValidator`: エピソード検証
- `StatisticsCalculator`: 統計計算

### リポジトリ
- `EpisodeRepository`: エピソード情報管理
- `ProjectRepository`: プロジェクト情報管理
- `MetadataRepository`: メタデータ管理

### 外部サービス
- `FileSystemService`: ファイルシステム操作
- `CacheService`: キャッシュ管理

## 設計原則遵守

### DDD準拠
- ✅ エンティティ（`EpisodeInfo`）の適切な使用
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
episode_numbering_service = EpisodeNumberingService()
episode_validator = EpisodeValidator()
statistics_calculator = StatisticsCalculator()
episode_repo = YamlEpisodeRepository()
project_repo = YamlProjectRepository()
metadata_repo = YamlMetadataRepository()
file_system_service = FileSystemService()
cache_service = CacheService()

# ユースケース作成
use_case = EpisodeListManagementUseCase(
    episode_numbering_service=episode_numbering_service,
    episode_validator=episode_validator,
    statistics_calculator=statistics_calculator,
    episode_repository=episode_repo,
    project_repository=project_repo,
    metadata_repository=metadata_repo,
    file_system_service=file_system_service,
    cache_service=cache_service
)

# 全エピソード一覧の取得
list_request = EpisodeListRequest(
    project_name="fantasy_adventure",
    view_type=EpisodeListView.ALL,
    sort_by="episode_number",
    sort_order="asc",
    include_metadata=True
)

response = use_case.get_episode_list(list_request)

if response.success:
    print(f"エピソード一覧: {response.total_count}件")

    # 統計情報表示
    stats = response.statistics
    print(f"\n=== 統計情報 ===")
    print(f"総文字数: {stats.total_words:,}文字")
    print(f"平均文字数: {stats.average_words:,.0f}文字")
    print(f"完成率: {stats.completion_rate:.1f}%")
    print(f"公開率: {stats.publishing_rate:.1f}%")

    # ステータス分布
    print(f"\nステータス分布:")
    for status, count in stats.status_distribution.items():
        print(f"  {status}: {count}件")

    # エピソード一覧表示
    print(f"\n=== エピソード一覧 ===")
    for episode in response.episodes[:10]:  # 最初の10件
        status_mark = "✅" if episode.status == EpisodeStatus.PUBLISHED else "📝"
        print(f"{status_mark} 第{episode.episode_number:03d}話: {episode.title}")
        print(f"   文字数: {episode.word_count:,} | 状態: {episode.status.value}")

# フィルタリングされた一覧取得
filtered_request = EpisodeListRequest(
    project_name="fantasy_adventure",
    view_type=EpisodeListView.ACTIVE,
    filter_criteria={
        "status": ["draft", "writing"],
        "chapter": 3,
        "word_count_min": 3000
    },
    sort_by="updated_at",
    sort_order="desc"
)

filtered_response = use_case.get_episode_list(filtered_request)

print(f"\n執筆中のエピソード: {filtered_response.total_count}件")

# 新しいエピソードの追加
new_episode = use_case.add_episode(
    project_name="fantasy_adventure",
    title="新たなる挑戦",
    chapter=4,
    position=None  # 自動的に最後に追加
)

print(f"\n新規エピソード追加: 第{new_episode.episode_number}話")

# エピソードの更新
success = use_case.update_episode(
    project_name="fantasy_adventure",
    episode_number=25,
    updates={
        "title": "決戦の時",
        "status": EpisodeStatus.REVIEW,
        "tags": ["クライマックス", "重要"]
    }
)

# エピソードの並び替え
# 第10話と第11話を入れ替え
current_order = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
new_order = [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 10, 12]

reorder_success = use_case.reorder_episodes(
    project_name="fantasy_adventure",
    new_order=new_order
)

if reorder_success:
    print("エピソード順序を更新しました")

# 一括操作: 第3章のエピソードを全てレビュー状態に
bulk_op = EpisodeBulkOperation(
    operation_type="update_status",
    target_episodes=[15, 16, 17, 18, 19, 20],
    parameters={
        "new_status": "review",
        "reason": "第3章の執筆完了"
    },
    dry_run=True  # まずドライラン
)

dry_result = use_case.execute_bulk_operation(
    project_name="fantasy_adventure",
    operation=bulk_op
)

print(f"\n一括操作プレビュー:")
print(f"影響エピソード: {dry_result.affected_count}件")
print(f"変更内容: {dry_result.preview}")

# 実際に実行
if input("実行しますか？ [y/N]: ").lower() == 'y':
    bulk_op.dry_run = False
    result = use_case.execute_bulk_operation(
        project_name="fantasy_adventure",
        operation=bulk_op
    )
    print(f"一括操作完了: {result.success_count}件成功")

# 章別表示
chapter_request = EpisodeListRequest(
    project_name="fantasy_adventure",
    view_type=EpisodeListView.BY_CHAPTER,
    sort_by="episode_number"
)

chapter_response = use_case.get_episode_list(chapter_request)

print("\n=== 章別エピソード ===")
for chapter, episodes in chapter_response.episodes_by_chapter.items():
    print(f"\n第{chapter}章: {len(episodes)}話")
    for ep in episodes[:3]:  # 各章の最初の3話
        print(f"  - 第{ep.episode_number}話: {ep.title}")
```

## 表示フォーマット例

### 標準リスト表示
```
エピソード一覧 (全50話)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
No. | タイトル              | 文字数  | 状態    | 更新日
────┼─────────────────────┼────────┼────────┼──────────
001 | 冒険の始まり          | 4,235  | 公開済  | 2024-01-15
002 | 出会い                | 3,987  | 公開済  | 2024-01-16
003 | 最初の試練            | 4,512  | 公開済  | 2024-01-17
004 | 師との修行            | 4,123  | 執筆中  | 2024-01-20
005 | [下書き]              | 1,234  | 下書き  | 2024-01-21
```

### ステータス別グループ表示
```
=== ステータス別 ===

📝 執筆中 (3話)
  - 第004話: 師との修行
  - 第008話: 謎の洞窟
  - 第012話: 約束の地へ

✏️ 下書き (5話)
  - 第005話: [下書き]
  - 第009話: [下書き]
  - 第013話: [下書き]

✅ 公開済 (42話)
  - 第001話: 冒険の始まり
  - 第002話: 出会い
  - 第003話: 最初の試練
  ...
```

## エラーハンドリング

### エピソード番号重複
```python
try:
    new_episode = self.add_episode(project_name, title)
except EpisodeNumberConflictError:
    # 自動的に次の利用可能な番号を割り当て
    next_number = self.episode_numbering_service.get_next_available_number()
    new_episode = self.add_episode(project_name, title, episode_number=next_number)
```

### 無効な並び替え
```python
is_valid, error_message = self._validate_reorder(current_order, new_order)
if not is_valid:
    raise InvalidReorderError(error_message)
```

## パフォーマンス最適化

### キャッシュ活用
```python
def get_episode_list(self, request: EpisodeListRequest) -> EpisodeListResponse:
    cache_key = self._generate_cache_key(request)

    # キャッシュチェック
    cached_result = self.cache_service.get(cache_key)
    if cached_result and not request.force_refresh:
        return cached_result

    # 実際の処理
    result = self._process_episode_list(request)

    # キャッシュ保存
    self.cache_service.set(cache_key, result, ttl=300)  # 5分間

    return result
```

### バッチ処理
```python
def _collect_episode_data_batch(self, project_name: str) -> list[EpisodeInfo]:
    # 並列でファイル読み込み
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for episode_file in episode_files:
            future = executor.submit(self._read_episode_file, episode_file)
            futures.append(future)

        episodes = [f.result() for f in futures]

    return episodes
```

## テスト観点

### 単体テスト
- フィルタリングロジック
- ソート機能
- ページング処理
- 統計計算の正確性
- 一括操作の動作

### 統合テスト
- 大量エピソードでの性能
- キャッシュの効果
- 並行処理の安全性
- ファイルシステムとの連携

## 品質基準

- **効率性**: 大量エピソードの高速処理
- **柔軟性**: 多様な表示・フィルタオプション
- **正確性**: 統計情報の正確な計算
- **使いやすさ**: 直感的な操作インターフェース
- **安全性**: 一括操作でのデータ保護
