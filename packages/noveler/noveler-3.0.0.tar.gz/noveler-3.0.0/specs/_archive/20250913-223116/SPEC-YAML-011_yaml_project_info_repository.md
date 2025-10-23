# YAMLプロジェクト情報リポジトリ仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、プロジェクト情報（メタデータ・設定・統計）のYAMLファイルベース永続化を提供する。

### 1.2 スコープ
- プロジェクト基本情報（名称・説明・ジャンル等）の管理
- プロジェクト設定（品質基準・執筆設定等）の永続化
- プロジェクト統計情報の収集・保存
- プロジェクト間の関連性管理
- 設定変更履歴とバックアップ機能

### 1.3 アーキテクチャ位置
```
Domain Layer
├── ProjectInfoRepository (Interface) ← Infrastructure Layer
└── ProjectInfo (Entity)              └── YamlProjectInfoRepository (Implementation)
```

## 2. 機能仕様

### 2.1 基本CRUD操作
```python
# 保存
def save(project_info: ProjectInfo, project_id: str) -> None

# 検索
def find_by_id(project_id: str) -> ProjectInfo | None
def find_by_name(name: str) -> ProjectInfo | None
def find_all() -> list[ProjectInfo]

# 存在確認
def exists(project_id: str) -> bool

# 削除
def delete(project_id: str) -> bool
```

### 2.2 プロジェクト基本情報管理
```python
# 基本情報更新
def update_basic_info(
    project_id: str,
    name: str,
    description: str,
    genre: str,
    tags: list[str]
) -> None

# 作者情報管理
def update_author_info(
    project_id: str,
    author_name: str,
    author_profile: dict[str, Any]
) -> None

# ステータス管理
def update_project_status(project_id: str, status: str) -> None
def get_project_status(project_id: str) -> str
```

### 2.3 プロジェクト設定管理
```python
# 執筆設定
def update_writing_settings(
    project_id: str,
    settings: dict[str, Any]
) -> None

def get_writing_settings(project_id: str) -> dict[str, Any]

# 品質基準設定
def update_quality_standards(
    project_id: str,
    standards: dict[str, Any]
) -> None

def get_quality_standards(project_id: str) -> dict[str, Any]

# 公開設定
def update_publication_settings(
    project_id: str,
    settings: dict[str, Any]
) -> None

def get_publication_settings(project_id: str) -> dict[str, Any]
```

### 2.4 統計情報管理
```python
# 執筆統計更新
def update_writing_statistics(
    project_id: str,
    episode_count: int,
    total_words: int,
    completion_rate: float
) -> None

# 品質統計更新
def update_quality_statistics(
    project_id: str,
    average_quality: float,
    quality_distribution: dict[str, int]
) -> None

# 公開統計更新
def update_publication_statistics(
    project_id: str,
    published_count: int,
    reader_stats: dict[str, Any]
) -> None

# 統計情報取得
def get_statistics(project_id: str) -> dict[str, Any]
```

### 2.5 プロジェクト検索・フィルタリング
```python
# ジャンル検索
def find_by_genre(genre: str) -> list[ProjectInfo]

# ステータス検索
def find_by_status(status: str) -> list[ProjectInfo]

# タグ検索
def find_by_tags(tags: list[str]) -> list[ProjectInfo]

# 作成日範囲検索
def find_by_creation_date_range(
    start_date: datetime,
    end_date: datetime
) -> list[ProjectInfo]

# アクティブプロジェクト検索
def find_active_projects() -> list[ProjectInfo]

# 完成プロジェクト検索
def find_completed_projects() -> list[ProjectInfo]
```

### 2.6 関連性・依存関係管理
```python
# 関連プロジェクト管理
def add_related_project(
    project_id: str,
    related_project_id: str,
    relation_type: str
) -> None

def remove_related_project(
    project_id: str,
    related_project_id: str
) -> None

def get_related_projects(project_id: str) -> list[dict[str, str]]

# シリーズ管理
def add_to_series(project_id: str, series_name: str, order: int) -> None
def get_series_projects(series_name: str) -> list[ProjectInfo]
```

### 2.7 設定履歴・バックアップ管理
```python
# 設定変更履歴
def add_change_log(
    project_id: str,
    change_type: str,
    description: str,
    changed_fields: list[str]
) -> None

def get_change_history(
    project_id: str,
    limit: int = 50
) -> list[dict[str, Any]]

# バックアップ・復元
def backup_project_info(project_id: str) -> str
def restore_project_info(project_id: str, backup_id: str) -> bool
```

### 2.8 システム管理機能
```python
# 全プロジェクト統計
def get_global_statistics() -> dict[str, Any]

# プロジェクト整合性チェック
def validate_project_info(project_id: str) -> dict[str, list[str]]

# 一括更新
def bulk_update_field(
    project_ids: list[str],
    field_name: str,
    field_value: Any
) -> int
```

## 3. データ構造仕様

### 3.1 ファイル配置
```
プロジェクトルート/
├── プロジェクト設定.yaml         # メインプロジェクト情報ファイル
├── 50_管理資料/                  # 詳細管理データ
│   ├── プロジェクト詳細.yaml     # 詳細設定・統計
│   ├── 変更履歴.yaml             # 設定変更履歴
│   └── 関連プロジェクト.yaml     # 関連性管理
└── backup/                       # バックアップ（任意）
    └── project_info_20250721_143022/
        ├── プロジェクト設定.yaml
        └── プロジェクト詳細.yaml
```

### 3.2 メインプロジェクト設定YAML構造
```yaml
# プロジェクト設定.yaml
project_basic_info:
  id: "project-001"
  name: "転生したら最強の魔法使いだった件"
  title_kana: "テンセイシタラサイキョウノマホウツカイダッタケン"
  description: "現代日本で事故死した主人公が異世界に転生し、強大な魔法力を手に入れる物語"
  genre: "異世界ファンタジー"
  sub_genre: ["転生", "魔法", "学園"]
  tags: ["異世界", "転生", "魔法", "学園", "成長", "バトル"]
  target_audience: "10代～30代男性"
  content_rating: "全年齢"

author_info:
  pen_name: "魔法文庫太郎"
  real_name: ""  # オプション
  profile: "異世界ファンタジー専門の作家"
  contact: "author@example.com"
  social_links:
    twitter: "@author_handle"
    website: "https://author-website.com"

project_status:
  status: "ACTIVE"  # PLANNING, ACTIVE, PAUSED, COMPLETED, ARCHIVED
  phase: "WRITING"  # PLANNING, PLOTTING, WRITING, EDITING, PUBLISHING
  priority: "HIGH"  # LOW, MEDIUM, HIGH, CRITICAL
  visibility: "PRIVATE"  # PRIVATE, TEAM, PUBLIC

project_schedule:
  start_date: "2025-07-15"
  target_completion: "2025-12-31"
  publication_schedule: "weekly"  # daily, weekly, monthly, irregular
  update_frequency: 2  # per week

project_goals:
  target_episodes: 100
  target_total_words: 300000
  target_readers: 10000
  publication_platform: ["小説家になろう", "カクヨム"]

metadata:
  created_at: "2025-07-15T10:00:00"
  updated_at: "2025-07-21T14:30:22"
  version: 3
  last_backup: "2025-07-21T14:00:00"
```

### 3.3 プロジェクト詳細YAML構造
```yaml
# 50_管理資料/プロジェクト詳細.yaml
writing_settings:
  default_episode_length: 3000
  minimum_episode_length: 2000
  maximum_episode_length: 5000
  writing_style: "三人称"
  narrative_tense: "過去形"
  chapter_structure: "複数話構成"

quality_standards:
  minimum_quality_score: 70.0
  target_quality_score: 85.0
  required_checks:
    - "basic_writing_style"
    - "story_structure"
    - "character_consistency"
  auto_fix_enabled: true
  review_required_threshold: 60.0

publication_settings:
  auto_publish: false
  publish_delay_hours: 24
  backup_before_publish: true
  quality_gate_enabled: true
  minimum_publish_score: 80.0

writing_statistics:
  total_episodes: 15
  completed_episodes: 12
  total_word_count: 45230
  average_episode_length: 3015
  writing_days: 25
  words_per_day: 1809
  last_writing_date: "2025-07-21"

quality_statistics:
  average_quality_score: 87.3
  quality_distribution:
    excellent: 5  # 90-100
    good: 7       # 80-89
    fair: 3       # 70-79
    poor: 0       # <70
  improvement_trend: 2.5  # points per episode

publication_statistics:
  published_episodes: 10
  total_views: 15420
  total_bookmarks: 234
  total_reviews: 18
  average_rating: 4.2
  follower_count: 89
  last_published: "2025-07-20T18:00:00"

performance_metrics:
  daily_views:
    "2025-07-21": 345
    "2025-07-20": 423
  engagement_rate: 15.2  # %
  retention_rate: 68.5   # %

technical_info:
  encoding: "UTF-8"
  line_ending: "LF"
  backup_retention_days: 90
  auto_save_interval: 300  # seconds

updated_at: "2025-07-21T14:30:22"
```

### 3.4 関連プロジェクトYAML構造
```yaml
# 50_管理資料/関連プロジェクト.yaml
related_projects:
  - project_id: "project-002"
    project_name: "転生魔法使いの学園生活"
    relation_type: "SEQUEL"  # PREQUEL, SEQUEL, SPIN_OFF, SAME_UNIVERSE
    description: "第1作の続編"
    created_at: "2025-07-18T15:00:00"

  - project_id: "project-003"
    project_name: "魔法世界の歴史"
    relation_type: "SAME_UNIVERSE"
    description: "同一世界観での別視点作品"
    created_at: "2025-07-19T12:00:00"

series_info:
  series_name: "異世界魔法使いシリーズ"
  series_order: 1
  series_description: "異世界転生を主軸としたファンタジーシリーズ"
  total_planned_works: 3

dependencies:
  requires: []  # この作品が依存する作品
  required_by: ["project-002"]  # この作品に依存する作品

cross_references:
  characters:
    - character_name: "主人公・太郎"
      appears_in: ["project-001", "project-002"]
    - character_name: "魔法学校校長"
      appears_in: ["project-001", "project-003"]

  locations:
    - location_name: "魔法学校"
      appears_in: ["project-001", "project-002", "project-003"]

updated_at: "2025-07-21T14:30:22"
```

## 4. 技術仕様

### 4.1 依存関係
```python
# 外部ライブラリ
import yaml
from datetime import datetime, date
from pathlib import Path
from typing import Any, Optional, Dict, List

# ドメイン層
from domain.entities.project_info import ProjectInfo, ProjectStatus, ProjectPhase
from domain.repositories.project_info_repository import ProjectInfoRepository
from domain.value_objects.project_id import ProjectId
from domain.value_objects.project_name import ProjectName
from domain.value_objects.author_info import AuthorInfo
from domain.value_objects.project_statistics import ProjectStatistics
```

### 4.2 エラーハンドリング
```python
# カスタム例外
class ProjectInfoRepositoryError(Exception):
    pass

class ProjectInfoNotFoundError(ProjectInfoRepositoryError):
    pass

class InvalidProjectInfoDataError(ProjectInfoRepositoryError):
    pass

class ProjectInfoConsistencyError(ProjectInfoRepositoryError):
    pass

class ProjectInfoConfigurationError(ProjectInfoRepositoryError):
    pass
```

## 5. パフォーマンス要件

### 5.1 応答時間
- プロジェクト情報検索: 20ms以内
- 全プロジェクト一覧取得: 200ms以内（100プロジェクト）
- 設定更新操作: 50ms以内
- 統計情報計算: 100ms以内

### 5.2 メモリ使用量
- 単一プロジェクト情報: 2MB以内
- 全プロジェクト同時読み込み: 200MB以内
- 統計計算時: 50MB以内

### 5.3 同時実行性
- 読み取り操作: 並行実行可能
- 設定更新操作: プロジェクト単位でロック
- 統計更新: 順次実行

## 6. 品質保証

### 6.1 データ整合性
- プロジェクトIDの一意性保証
- 必須フィールドの存在確認
- 設定値の妥当性検証
- 関連プロジェクトの存在確認

### 6.2 エラー回復
- 破損したYAMLファイルの自動修復
- デフォルト設定での補完機能
- 統計データの再計算機能
- バックアップからの自動復元

### 6.3 設定管理
- 設定変更の詳細履歴記録
- 無効な設定値の自動修正
- 設定競合の自動解決
- 設定の妥当性検証

## 7. セキュリティ

### 7.1 アクセス制御
- ファイルシステム権限に基づくアクセス制御
- 機密情報（作者個人情報等）の保護
- プロジェクト間のデータ分離

### 7.2 データ保護
- エンコーディング: UTF-8統一
- 個人情報のマスキング機能
- パス インジェクション攻撃の防止
- YAMLインジェクション攻撃の防止

## 8. 互換性

### 8.1 レガシーシステム
- 既存のプロジェクト設定ファイルとの互換
- 段階的移行サポート
- 旧形式からの自動変換

### 8.2 将来拡張性
- 新しい設定項目の追加対応
- 異なるファイル形式への拡張準備
- クラウドストレージ連携準備
- 外部システム連携インターフェース

## 9. 使用例

### 9.1 基本的な使用パターン
```python
# リポジトリ初期化
project_path = Path("/path/to/project")
repo = YamlProjectInfoRepository(project_path)

# プロジェクト情報作成・保存
project_info = ProjectInfo(
    id=ProjectId("project-001"),
    name=ProjectName("転生したら最強の魔法使いだった件"),
    description="異世界転生ファンタジー小説",
    genre="異世界ファンタジー",
    author_name="魔法文庫太郎"
)
repo.save(project_info, "project-001")

# 情報検索
found_info = repo.find_by_id("project-001")
all_projects = repo.find_all()
```

### 9.2 設定管理の使用例
```python
# 執筆設定更新
writing_settings = {
    "default_episode_length": 3000,
    "writing_style": "三人称",
    "auto_save_interval": 300
}
repo.update_writing_settings("project-001", writing_settings)

# 品質基準設定
quality_standards = {
    "minimum_quality_score": 70.0,
    "target_quality_score": 85.0,
    "auto_fix_enabled": True
}
repo.update_quality_standards("project-001", quality_standards)
```

### 9.3 統計管理の使用例
```python
# 執筆統計更新
repo.update_writing_statistics(
    "project-001",
    episode_count=15,
    total_words=45230,
    completion_rate=75.0
)

# 統計情報取得
stats = repo.get_statistics("project-001")
print(f"総エピソード数: {stats['total_episodes']}")
print(f"完成度: {stats['completion_rate']:.1f}%")

# 全プロジェクト統計
global_stats = repo.get_global_statistics()
print(f"管理中プロジェクト数: {global_stats['total_projects']}")
```

### 9.4 関連性管理の使用例
```python
# 関連プロジェクト追加
repo.add_related_project(
    "project-001",
    "project-002",
    "SEQUEL"
)

# シリーズ管理
repo.add_to_series("project-001", "異世界魔法使いシリーズ", 1)

# 関連プロジェクト取得
related = repo.get_related_projects("project-001")
```

## 10. テスト仕様

### 10.1 単体テスト
- 各CRUDメソッドの動作確認
- 設定更新・取得機能のテスト
- 統計計算機能の正確性テスト
- エラーケースの処理確認
- データ検証機能のテスト

### 10.2 統合テスト
- 実際のファイルシステムでの動作確認
- 複数プロジェクトの同時管理テスト
- 設定変更履歴の整合性テスト
- バックアップ・復元機能のテスト

### 10.3 エラーシナリオ
- ディスク容量不足時の動作
- ファイル権限エラーの処理
- 破損した設定ファイルの復旧
- 無効な設定値の処理
- 関連プロジェクトの整合性エラー

## 11. 運用・監視

### 11.1 ログ出力
- 設定変更操作の詳細ログ
- エラー発生時の詳細情報
- 統計更新の実行ログ
- パフォーマンス測定ログ

### 11.2 メトリクス
- 設定変更頻度の統計
- エラー発生率の監視
- プロジェクト活動状況の分析
- システム使用状況の監視

### 11.3 アラート
- 設定整合性エラーの通知
- プロジェクト状態異常の検出
- バックアップ失敗の通知
- 容量不足の早期警告

## 12. 実装メモ

### 12.1 実装ファイル
- **メインクラス**: `src/noveler/infrastructure/repositories/yaml_project_info_repository.py`
- **テストファイル**: `tests/unit/infrastructure/repositories/test_yaml_project_info_repository.py`

### 12.2 設計方針
- DDD原則の厳格な遵守
- 設定データの完全な復元
- 統計情報の正確性保証
- エラー時のグレースフルデグラデーション
- 将来の拡張性を考慮した設計

### 12.3 今後の改善点
- [ ] クラウドバックアップ機能
- [ ] プロジェクトテンプレート機能
- [ ] 設定の自動最適化機能
- [ ] 外部統計サービス連携
- [ ] リアルタイム統計ダッシュボード
- [ ] AI による設定推奨機能
- [ ] プロジェクト間の自動関連性検出
