# SPEC-EPISODE-011: episode 仕様書

## SPEC-EPISODE-005: エピソードエンティティ


## 1. 目的
小説の各話（エピソード）を表現するエンティティ。執筆から公開までのライフサイクルを管理し、品質保証を含むビジネスルールを実装する。

## 2. 前提条件
- DDD原則に基づくリッチなドメインエンティティ
- 値オブジェクト（EpisodeNumber, EpisodeTitle, WordCount, QualityScore）に依存
- エンティティは可変だが、ビジネスルールによる制約を持つ

## 3. 主要な振る舞い

### 3.1 ライフサイクル管理
エピソードは以下の状態遷移を持つ：

```
UNWRITTEN → DRAFT → IN_PROGRESS → COMPLETED → REVIEWED → PUBLISHED
                                         ↓
                                    ARCHIVED
```

### 3.2 ステータス定義
- **UNWRITTEN**: 未執筆（初期状態）
- **DRAFT**: 下書き（内容が入力された状態）
- **IN_PROGRESS**: 執筆中（アクティブに編集中）
- **COMPLETED**: 完成（執筆完了）
- **REVIEWED**: レビュー済み（品質チェック完了）
- **PUBLISHED**: 公開済み（読者に公開）
- **ARCHIVED**: アーカイブ済み（非公開保管）

### 3.3 ビジネスルール
1. **公開条件**:
   - ステータスがCOMPLETEDまたはREVIEWED
   - 品質スコア70点以上
   - 文字数1000文字以上

2. **編集制限**:
   - PUBLISHED状態では編集不可
   - ARCHIVED状態から復元可能

3. **品質管理**:
   - 最小文字数チェック（1000文字）
   - 品質スコア管理
   - 完成度計算（目標文字数に対する達成率）

### 3.4 メタデータ管理
- タグ付け機能
- カスタムメタデータ（key-value）
- バージョン管理

## 4. インターフェース仕様

```python
@dataclass
class Episode:
    """エピソードエンティティ"""

    # 必須属性
    number: EpisodeNumber
    title: EpisodeTitle
    content: str
    target_words: WordCount

    # 状態管理
    status: EpisodeStatus = EpisodeStatus.DRAFT
    quality_score: QualityScore | None = None
    word_count: WordCount  # 自動計算
    version: int = 1

    # タイムスタンプ
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    published_at: datetime | None = None
    archived_at: datetime | None = None

    # メタデータ
    tags: list[str] = []
    metadata: dict[str, Any] = {}

    # ビジネスメソッド
    def start_writing() -> None
    def update_content(new_content: str) -> None
    def complete() -> None
    def set_quality_score(score: QualityScore) -> None
    def publish() -> None
    def archive() -> None
    def restore_from_archive() -> None

    # 判定メソッド
    def can_publish() -> bool
    def is_ready_for_quality_check() -> bool
    def completion_percentage() -> float

    # メタデータ操作
    def add_tag(tag: str) -> None
    def remove_tag(tag: str) -> None
    def set_metadata(key: str, value: Any) -> None
```

## 5. エラーハンドリング

### 5.1 DomainException
- エピソード番号が1未満
- タイトルが空
- 目標文字数が1未満
- 公開済みエピソードの編集試行
- 未執筆エピソードへの品質スコア設定
- 公開条件未達成での公開試行

## 6. 使用例

```python
# エピソード作成
episode = Episode(
    number=EpisodeNumber(1),
    title=EpisodeTitle("始まりの朝"),
    content="",
    target_words=WordCount(3000)
)

# 執筆開始
episode.start_writing()
episode.update_content("昔々あるところに...")

# 完成処理
episode.complete()
episode.set_quality_score(QualityScore(85))

# 公開判定
if episode.can_publish():
    episode.publish()

# メタデータ管理
episode.add_tag("ファンタジー")
episode.set_metadata("viewpoint", "一人称")
```

## 7. 実装メモ
- テストファイル: `tests/unit/domain/entities/test_episode.py`
- 実装ファイル: `scripts/domain/entities/episode.py`
- 作成日: 2025-01-21

## 8. 未決定事項
- [ ] 下書き自動保存の間隔
- [ ] 公開予約機能
- [ ] 複数バージョンの管理方法
- [ ] 共同執筆対応
