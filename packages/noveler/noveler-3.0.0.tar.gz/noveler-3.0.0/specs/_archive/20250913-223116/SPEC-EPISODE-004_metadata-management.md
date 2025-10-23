# SPEC-EPISODE-004: エピソードメタデータ管理システム

## 概要

エピソードの執筆・品質管理に関するメタデータを統合的に管理するドメインサービス。エピソードの基本情報、執筆状況、品質情報、技術的メタデータを一元化し、DDD設計に基づく堅牢なメタデータ管理を提供する。

## 要求仕様

### 機能要求

1. **エピソードメタデータ統合管理**
   - 基本メタデータ: タイトル、番号、執筆者、作成日時
   - 執筆メタデータ: 文字数、執筆時間、執筆ステータス
   - 品質メタデータ: 品質スコア、チェック結果、改善提案
   - 技術メタデータ: ファイルパス、バージョン、ハッシュ値

2. **メタデータ検索・フィルタリング**
   - 複合条件検索: 日付範囲、品質スコア範囲、執筆ステータス
   - ソート機能: 作成日時、更新日時、品質スコア順
   - ページネーション対応

3. **メタデータ統計・分析**
   - 執筆進捗統計: 期間別執筆数、文字数推移
   - 品質統計: 平均品質スコア、品質向上トレンド
   - パフォーマンス統計: 執筆速度、完成率

### 非機能要求

1. **パフォーマンス**: メタデータ検索 < 100ms
2. **拡張性**: 新しいメタデータ項目の追加容易性
3. **整合性**: メタデータとファイル実体の一貫性保証
4. **可用性**: メタデータ破損時の自動復旧

## DDD設計

### エンティティ

#### EpisodeMetadataAggregate
- **責務**: エピソードメタデータの集約ルート
- **不変条件**:
  - エピソード番号の一意性
  - メタデータ整合性の保証
  - 必須フィールドの存在確認

### 値オブジェクト

#### EpisodeMetadata
```python
@dataclass(frozen=True)
class EpisodeMetadata:
    episode_number: EpisodeNumber
    title: EpisodeTitle
    basic_info: BasicMetadata
    writing_info: WritingMetadata
    quality_info: QualityMetadata
    technical_info: TechnicalMetadata
    created_at: datetime
    updated_at: datetime
```

#### BasicMetadata
```python
@dataclass(frozen=True)
class BasicMetadata:
    author: str
    genre: GenreType
    tags: List[str]
    description: str
```

#### WritingMetadata
```python
@dataclass(frozen=True)
class WritingMetadata:
    word_count: WordCount
    writing_duration: WritingDuration
    status: EpisodeStatus
    completion_rate: CompletionRate
```

#### QualityMetadata
```python
@dataclass(frozen=True)
class QualityMetadata:
    overall_score: QualityScore
    category_scores: Dict[str, QualityScore]
    last_check_date: datetime
    improvement_suggestions: List[ImprovementSuggestion]
```

#### TechnicalMetadata
```python
@dataclass(frozen=True)
class TechnicalMetadata:
    file_path: FilePath
    file_hash: str
    version: VersionNumber
    backup_paths: List[FilePath]
```

### ドメインサービス

#### EpisodeMetadataManagementService
- **責務**: メタデータのライフサイクル管理
- **主要メソッド**:
  - `create_metadata()`: 新規メタデータ作成
  - `update_metadata()`: メタデータ更新
  - `merge_metadata()`: 複数ソースからのメタデータ統合
  - `validate_consistency()`: 整合性検証

### リポジトリ

#### EpisodeMetadataRepository
```python
class EpisodeMetadataRepository(ABC):
    @abstractmethod
    def find_by_episode_number(self, episode_number: EpisodeNumber) -> Optional[EpisodeMetadata]:
        pass

    @abstractmethod
    def search_by_criteria(self, criteria: MetadataSearchCriteria) -> List[EpisodeMetadata]:
        pass

    @abstractmethod
    def save(self, metadata: EpisodeMetadata) -> None:
        pass

    @abstractmethod
    def get_statistics(self, period: AnalysisPeriod) -> MetadataStatistics:
        pass
```

## テストケース

### ユニットテスト

1. **EpisodeMetadata値オブジェクト**
   - 不変性の検証
   - バリデーション機能の検証
   - 等価性比較の検証

2. **EpisodeMetadataManagementService**
   - メタデータ作成・更新・削除
   - 整合性検証機能
   - エラーハンドリング

### 統合テスト

1. **メタデータ永続化**
   - YAMLファイルへの保存・読み込み
   - 複数メタデータの一括操作
   - トランザクション整合性

2. **検索・フィルタリング**
   - 複合条件検索の正確性
   - パフォーマンス要件の充足
   - ページネーション機能

### E2Eテスト

1. **執筆ワークフロー統合**
   - エピソード作成→メタデータ自動生成
   - 品質チェック→メタデータ更新
   - 完成処理→メタデータ確定

## 実装

### Phase 1: 基本構造
- EpisodeMetadata値オブジェクト
- EpisodeMetadataManagementService
- YamlEpisodeMetadataRepository

### Phase 2: 高度機能
- 検索・フィルタリング機能
- 統計・分析機能
- メタデータ同期機能

### Phase 3: 統合
- 既存システムとの統合
- パフォーマンス最適化
- 監視・ログ機能
