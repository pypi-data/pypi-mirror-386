# YAMLエピソードリポジトリ仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、エピソードエンティティのYAMLファイルベース永続化を提供する。

### 1.2 スコープ
- エピソード作成・保存・検索・削除の完全な永続化機能
- 原稿ファイル（Markdown）と管理データ（YAML）の分離管理
- 高度な検索・統計・バックアップ機能
- レガシーシステムとの互換性確保

### 1.3 アーキテクチャ位置
```
Domain Layer
├── EpisodeRepository (Interface) ← Infrastructure Layer
└── Episode (Entity)              └── YamlEpisodeRepository (Implementation)
```

## 2. 機能仕様

### 2.1 基本CRUD操作
```python
# 保存
def save(episode: Episode, project_id: str) -> None

# 検索
def find_by_number(project_id: str, number: EpisodeNumber) -> Episode | None
def find_by_id(episode_id: str, project_id: str) -> Episode | None
def find_all(project_id: str) -> list[Episode]

# 存在確認
def exists(project_id: str, number: EpisodeNumber) -> bool

# 削除
def delete(episode_id: str, project_id: str) -> bool
```

### 2.2 高度な検索機能
```python
# ステータス検索
def find_by_status(project_id: str, status: str) -> list[Episode]

# 日付範囲検索
def find_by_date_range(
    project_id: str,
    start_date: datetime,
    end_date: datetime
) -> list[Episode]

# 品質スコア範囲検索
def find_by_quality_score_range(
    project_id: str,
    min_score: float,
    max_score: float
) -> list[Episode]

# タグ検索
def find_by_tags(project_id: str, tags: list[str]) -> list[Episode]

# 公開準備完了検索
def find_ready_for_publication(project_id: str) -> list[Episode]
```

### 2.3 統計・分析機能
```python
# 統計情報取得
def get_statistics(project_id: str) -> dict[str, Any]
# 戻り値例:
{
    "total_episodes": 15,
    "total_word_count": 45230,
    "status_distribution": {
        "DRAFT": 3,
        "IN_PROGRESS": 5,
        "COMPLETED": 7
    },
    "average_quality_score": 87.3,
    "publishable_count": 7
}

# カウント機能
def get_episode_count(project_id: str) -> int
def get_total_word_count(project_id: str) -> int
```

### 2.4 バックアップ・復元機能
```python
# バックアップ作成
def backup_episode(episode_id: str, project_id: str) -> bool

# バックアップからの復元
def restore_episode(
    episode_id: str,
    project_id: str,
    backup_version: str
) -> bool
```

### 2.5 一括操作
```python
# 一括ステータス更新
def bulk_update_status(
    project_id: str,
    episode_ids: list[str],
    new_status: str
) -> int
```

## 3. データ構造仕様

### 3.1 ファイル配置
```
プロジェクトルート/
├── 40_原稿/                    # 原稿ファイル（Markdown）
│   ├── 第001話_異世界転生.md
│   ├── 第002話_魔法学校.md
│   └── ...
├── 50_管理資料/                # 管理データ（YAML）
│   └── 話数管理.yaml
└── backup/                     # バックアップ（任意）
    └── 20250721_143022/
        ├── 第001話_異世界転生.md
        └── episode_1_metadata.yaml
```

### 3.2 話数管理YAML構造
```yaml
episodes:
  - number: 1
    title: "異世界転生"
    status: "COMPLETED"
    word_count: 3247
    target_words: 3000
    version: 2
    quality_score: 88.5
    created_at: "2025-07-15T10:30:00"
    completed_at: "2025-07-16T15:45:00"
    updated_at: "2025-07-21T14:30:22"
  - number: 2
    title: "魔法学校"
    status: "IN_PROGRESS"
    word_count: 1850
    target_words: 3000
    version: 1
    quality_score: null
    created_at: "2025-07-17T09:15:00"
    completed_at: null
    updated_at: "2025-07-21T14:30:22"

updated_at: "2025-07-21T14:30:22"
```

### 3.3 原稿ファイル命名規則
```
第{番号:03d}話_{タイトル}.md

例:
第001話_異世界転生.md
第002話_魔法学校.md
第123話_最終決戦.md
```

## 4. 技術仕様

### 4.1 依存関係
```python
# 外部ライブラリ
import yaml
from datetime import datetime
from pathlib import Path

# ドメイン層
from domain.entities.episode import Episode, EpisodeStatus
from domain.repositories.episode_repository import EpisodeRepository
from domain.value_objects.episode_number import EpisodeNumber
from domain.value_objects.episode_title import EpisodeTitle
from domain.value_objects.quality_score import QualityScore
from domain.value_objects.word_count import WordCount
```

### 4.2 エラーハンドリング
```python
# カスタム例外（必要に応じて定義）
class EpisodeRepositoryError(Exception):
    pass

class EpisodeNotFoundError(EpisodeRepositoryError):
    pass

class InvalidEpisodeDataError(EpisodeRepositoryError):
    pass
```

## 5. パフォーマンス要件

### 5.1 応答時間
- 単一エピソード検索: 50ms以内
- 全エピソード読み込み: 500ms以内（100エピソード）
- 保存操作: 100ms以内

### 5.2 メモリ使用量
- 単一エピソード: 10MB以内
- 全エピソード同時読み込み: 1GB以内

### 5.3 同時実行性
- 読み取り操作: 並行実行可能
- 書き込み操作: ファイルロック機構で排他制御

## 6. 品質保証

### 6.1 データ整合性
- エピソード番号の一意性保証
- 原稿ファイルと管理データの同期保証
- YAMLフォーマットの妥当性検証

### 6.2 エラー回復
- 破損したYAMLファイルの自動修復
- 欠損した原稿ファイルの検出・通知
- バックアップからの自動復元オプション

### 6.3 バージョン管理
- エピソードバージョンの自動インクリメント
- 更新日時の自動記録
- 変更履歴の追跡（オプション）

## 7. セキュリティ

### 7.1 アクセス制御
- ファイルシステム権限に基づくアクセス制御
- プロジェクトID単位でのデータ分離

### 7.2 データ保護
- エンコーディング: UTF-8統一
- 特殊文字のエスケープ処理
- パス インジェクション攻撃の防止

## 8. 互換性

### 8.1 レガシーシステム
- 既存の原稿ファイル形式との完全互換
- 段階的移行サポート
- 既存データの自動変換

### 8.2 将来拡張性
- 新しいメタデータフィールドの追加対応
- 異なるファイル形式への拡張（JSON, XML等）
- 分散ストレージへの移行準備

## 9. 使用例

### 9.1 基本的な使用パターン
```python
# リポジトリ初期化
project_path = Path("/path/to/project")
repo = YamlEpisodeRepository(project_path)

# エピソード作成・保存
episode = Episode(
    number=EpisodeNumber(1),
    title=EpisodeTitle("異世界転生"),
    content="俺の名前は田中太郎...",
    target_words=WordCount(3000)
)
repo.save(episode, "project-001")

# 検索
found_episode = repo.find_by_number("project-001", EpisodeNumber(1))
all_episodes = repo.find_all("project-001")

# 統計取得
stats = repo.get_statistics("project-001")
print(f"総エピソード数: {stats['total_episodes']}")
```

### 9.2 高度な検索例
```python
# 公開準備完了のエピソード取得
ready_episodes = repo.find_ready_for_publication("project-001")

# 品質スコア80点以上のエピソード検索
high_quality = repo.find_by_quality_score_range(
    "project-001", 80.0, 100.0
)

# 最近1週間のエピソード検索
from datetime import datetime, timedelta
last_week = datetime.now() - timedelta(days=7)
recent = repo.find_by_date_range(
    "project-001", last_week, datetime.now()
)
```

### 9.3 バックアップ・復元例
```python
# バックアップ作成
success = repo.backup_episode("1", "project-001")

# 復元実行
restored = repo.restore_episode(
    "1", "project-001", "20250721_143022"
)
```

## 10. テスト仕様

### 10.1 単体テスト
- 各CRUDメソッドの動作確認
- エラーケースの処理確認
- 境界値テスト
- 性能テスト

### 10.2 統合テスト
- 実際のファイルシステムでの動作確認
- 大量データでの性能テスト
- 同時実行テスト

### 10.3 エラーシナリオ
- ディスク容量不足
- ファイル権限エラー
- 破損したYAMLファイル
- ネットワークドライブでの動作

## 11. 運用・監視

### 11.1 ログ出力
- 重要な操作（保存、削除）のログ記録
- エラー発生時の詳細ログ
- パフォーマンス測定ログ

### 11.2 メトリクス
- 操作回数・実行時間の統計
- エラー発生率の監視
- ディスク使用量の監視

### 11.3 アラート
- データ整合性エラー
- パフォーマンス劣化
- ディスク容量警告

## 12. 実装メモ

### 12.1 実装ファイル
- **メインクラス**: `src/noveler/infrastructure/repositories/yaml_episode_repository.py`
- **テストファイル**: `tests/unit/infrastructure/repositories/test_yaml_episode_repository.py`

### 12.2 設計方針
- DDD原則の厳格な遵守
- ドメインエンティティの完全な復元
- エラー時のグレースフルデグラデーション
- 将来の拡張性を考慮した設計

### 12.3 今後の改善点
- [ ] 非同期I/O対応による性能向上
- [ ] 分散ファイルシステム対応
- [ ] リアルタイム変更通知機能
- [ ] 自動バックアップスケジュール機能
- [ ] 圧縮によるディスク使用量最適化
