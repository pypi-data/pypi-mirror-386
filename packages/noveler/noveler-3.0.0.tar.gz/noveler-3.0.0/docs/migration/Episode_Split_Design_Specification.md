# Episode.py分割設計仕様書

**Phase 1 Week 3-4: エンティティ職責分離**
**対象**: scripts/domain/entities/episode.py (現在356行)
**目標**: 4つのクラスに分割（50+30+40+25行）

## 🎯 分割戦略

### 1. Episode (コアエンティティ - 50行)
**責務**: エピソードの基本状態・不変条件・核となる振る舞い

**フィールド**:
- `number: EpisodeNumber` (主キー)
- `title: EpisodeTitle`
- `content: str`
- `target_words: WordCount`
- `status: EpisodeStatus`
- `word_count: WordCount` (calculated)
- `version: int`
- `created_at: datetime`
- `updated_at: datetime`

**メソッド**:
- `__post_init__()` - 初期化・不変条件検証
- `_validate_invariants()` - ビジネスルール検証
- `start_writing()` - 執筆開始
- `update_content()` - コンテンツ更新
- `complete()` - 完成
- `calculate_word_count()` - 文字数計算
- `completion_percentage()` - 完成度計算

### 2. EpisodePublisher (公開責務 - 30行)
**責務**: エピソードの公開・レビュー・公開条件判定

**フィールド**:
- `episode: Episode` (コアエンティティへの参照)
- `published_at: datetime | None`

**メソッド**:
- `publish()` - 公開実行
- `can_publish()` - 公開可能判定
- `review()` - レビュー済みマーク
- `is_ready_for_quality_check()` - 品質チェック準備完了判定

### 3. EpisodeQuality (品質管理責務 - 40行)
**責務**: 品質スコア管理・品質チェック・課題特定

**フィールド**:
- `episode: Episode` (コアエンティティへの参照)
- `quality_score: QualityScore | None`

**メソッド**:
- `set_quality_score()` - 品質スコア設定
- `get_quality_check_issues()` - 品質問題リスト取得
- `is_ready_for_quality_check()` - 品質チェック可能判定
- `validate_publishing_quality()` - 公開品質基準検証

### 4. EpisodeMetadata (メタデータ責務 - 25行)
**責務**: タグ・統計情報・付加的メタデータ管理

**フィールド**:
- `episode: Episode` (コアエンティティへの参照)
- `completed_at: datetime | None`
- `archived_at: datetime | None`
- `tags: list[str]`
- `metadata: dict[str, Any]`

**メソッド**:
- `add_tag()` / `remove_tag()` - タグ管理
- `set_metadata()` / `get_metadata()` - メタデータ管理
- `archive()` / `restore_from_archive()` - アーカイブ管理
- `get_writing_statistics()` - 執筆統計情報

## 🏗️ 実装パターン

### Aggregateパターン適用
```python
@dataclass
class Episode:
    """エピソード集約ルート"""
    # Core fields only
    number: EpisodeNumber
    title: EpisodeTitle
    content: str
    # ... core fields

    def __post_init__(self):
        # Create sub-entities
        self._publisher = EpisodePublisher(self)
        self._quality = EpisodeQuality(self)
        self._metadata = EpisodeMetadata(self)

    @property
    def publisher(self) -> EpisodePublisher:
        return self._publisher

    @property
    def quality(self) -> EpisodeQuality:
        return self._quality

    @property
    def metadata(self) -> EpisodeMetadata:
        return self._metadata
```

### DI統合
```python
# 各サブエンティティでLoggerService使用
try:
    from scripts.infrastructure.di.simple_di_container import get_container
    from scripts.domain.interfaces.logger_service import ILoggerService
    logger = get_container().get(ILoggerService)
except ImportError:
    logger = None
```

## 🔄 移行戦略

### Phase 1: 基盤準備
1. 新しい4クラスの実装
2. 既存のEpisodeクラス内にプロパティ追加
3. 後方互換性の確保

### Phase 2: 段階的移行
1. 新メソッドの優先使用
2. 既存メソッドの非推奨化
3. テスト更新・動作確認

### Phase 3: 完全移行
1. 旧メソッドの削除
2. インターフェース確定
3. パフォーマンス最適化

## 📊 期待される効果

- **行数削減**: 356行 → 145行 (60%削減)
- **責務明確化**: 単一責任原則完全準拠
- **テスト容易性**: 各責務の独立テスト可能
- **保守性向上**: 変更影響範囲の局所化
- **拡張性**: 新機能追加時の影響最小化

## 🚀 実装タイムライン

**Week 3 (3日間)**:
- Day 1: Episode + EpisodePublisher実装
- Day 2: EpisodeQuality + EpisodeMetadata実装
- Day 3: 統合・テスト・デバッグ

**Week 4 (2日間)**:
- Day 1: 既存コードとの統合テスト
- Day 2: パフォーマンステスト・最適化
