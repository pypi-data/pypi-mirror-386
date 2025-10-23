# シンプルYAMLエピソードリポジトリ仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、エピソードエンティティの軽量なYAMLファイルベース永続化を提供する。複雑な機能を排除し、基本的なCRUD操作に特化したシンプルな実装。

### 1.2 スコープ
- エピソードの基本CRUD操作（作成・読み取り・更新・削除）
- 単一YAMLファイルによる軽量管理
- 最小限のメタデータ記録
- ファイルシステムベースの単純な永続化
- 小規模プロジェクト向けの高速アクセス

### 1.3 アーキテクチャ位置
```
Domain Layer
├── EpisodeRepository (Interface)     ← Infrastructure Layer
└── Episode (Entity)                  └── SimpleYamlEpisodeRepository (Implementation)
```

### 1.4 ビジネス価値
- **軽量性**: 最小限のオーバーヘッドでの高速動作
- **シンプルさ**: 複雑な設定や依存関係のない直感的な操作
- **透明性**: 人間が読み書き可能なYAMLフォーマット
- **可搬性**: 単純なファイル構造による高い移植性

## 2. 機能仕様

### 2.1 基本CRUD操作
```python
# エピソード保存
def save_episode(episode: Episode) -> None

# エピソード検索
def find_by_number(episode_number: EpisodeNumber) -> Episode | None
def find_by_id(episode_id: str) -> Episode | None
def find_all() -> list[Episode]

# エピソード存在確認
def exists(episode_number: EpisodeNumber) -> bool

# エピソード削除
def delete(episode_number: EpisodeNumber) -> bool
```

### 2.2 基本統計機能
```python
# 統計情報取得
def get_episode_count() -> int
def get_total_word_count() -> int
def get_average_quality_score() -> float | None

# 基本リスト機能
def list_episode_numbers() -> list[int]
def list_episode_titles() -> list[str]
```

### 2.3 ステータス管理
```python
# ステータス別検索
def find_by_status(status: EpisodeStatus) -> list[Episode]

# ステータス更新
def update_status(episode_number: EpisodeNumber, status: EpisodeStatus) -> bool
```

### 2.4 単純バックアップ
```python
# バックアップ作成
def create_backup() -> Path

# バックアップからの復元
def restore_from_backup(backup_path: Path) -> bool
```

## 3. データ構造仕様

### 3.1 ファイル配置
```
プロジェクトルート/
├── 40_原稿/                         # 原稿ファイル（Markdown）
│   ├── 第001話_異世界転生.md
│   ├── 第002話_魔法学校.md
│   └── ...
├── 50_管理資料/                     # 管理データ（YAML）
│   └── エピソード一覧.yaml           # 単一のエピソード管理ファイル
└── .backup/                         # バックアップ（オプション）
    └── エピソード一覧_20250721.yaml
```

### 3.2 エピソード一覧YAML構造
```yaml
# エピソード一覧.yaml
metadata:
  created_at: "2025-07-15T10:30:00"
  last_updated: "2025-07-21T14:30:22"
  total_episodes: 15
  schema_version: "1.0.0"

episodes:
  - number: 1
    id: "episode-001"
    title: "異世界転生"
    status: "COMPLETED"
    word_count: 3247
    quality_score: 88.5
    created_at: "2025-07-15T10:30:00"
    updated_at: "2025-07-21T14:30:22"
    file_name: "第001話_異世界転生.md"
    tags: ["転生", "魔法"]

  - number: 2
    id: "episode-002"
    title: "魔法学校"
    status: "IN_PROGRESS"
    word_count: 1850
    quality_score: null
    created_at: "2025-07-17T09:15:00"
    updated_at: "2025-07-21T12:45:00"
    file_name: "第002話_魔法学校.md"
    tags: ["学校", "成長"]

  - number: 3
    id: "episode-003"
    title: "新たな友人"
    status: "DRAFT"
    word_count: 0
    quality_score: null
    created_at: "2025-07-21T14:30:22"
    updated_at: "2025-07-21T14:30:22"
    file_name: "第003話_新たな友人.md"
    tags: ["友情"]
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
from typing import Any

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
# カスタム例外
class SimpleEpisodeRepositoryError(Exception):
    """シンプルエピソードリポジトリエラー"""
    pass

class EpisodeFileNotFoundError(SimpleEpisodeRepositoryError):
    """エピソードファイル未発見エラー"""
    pass

class EpisodeDataFormatError(SimpleEpisodeRepositoryError):
    """エピソードデータフォーマットエラー"""
    pass

class EpisodeDuplicateError(SimpleEpisodeRepositoryError):
    """エピソード重複エラー"""
    pass
```

### 4.3 設定管理
```python
@dataclass
class SimpleRepositoryConfig:
    """シンプルリポジトリ設定"""
    project_root: Path
    episode_list_filename: str = "エピソード一覧.yaml"
    backup_enabled: bool = True
    auto_backup_on_save: bool = False
    encoding: str = "utf-8"
```

## 5. パフォーマンス要件

### 5.1 応答時間
- 単一エピソード検索: 20ms以内
- 全エピソード読み込み: 100ms以内（50エピソード）
- エピソード保存: 50ms以内
- バックアップ作成: 200ms以内

### 5.2 メモリ使用量
- 単一エピソード: 1MB以内
- 全エピソード同時読み込み: 50MB以内
- リポジトリインスタンス: 5MB以内

### 5.3 ファイルサイズ制限
- エピソード一覧ファイル: 10MB以内（500エピソード想定）
- 単一エピソード原稿: 1MB以内
- バックアップファイル: 20MB以内

## 6. 品質保証

### 6.1 データ整合性
```python
def validate_episode_data(self, episode_data: dict) -> bool:
    """エピソードデータの基本検証"""
    required_fields = ['number', 'id', 'title', 'status']
    return all(field in episode_data for field in required_fields)

def validate_episode_number_uniqueness(self, episode_number: int) -> bool:
    """エピソード番号の一意性検証"""

def validate_file_consistency(self) -> list[str]:
    """ファイル整合性検証（原稿ファイルとYAMLの同期確認）"""
```

### 6.2 エラー回復
```python
def repair_missing_episodes(self) -> int:
    """欠損エピソードの検出・修復"""

def fix_data_format_errors(self) -> bool:
    """データフォーマットエラーの自動修正"""

def restore_from_backup_if_corrupted(self) -> bool:
    """破損時のバックアップからの自動復元"""
```

### 6.3 データ同期
```python
def sync_with_manuscript_files(self) -> dict[str, Any]:
    """原稿ファイルとの同期処理"""

def update_metadata_from_files(self) -> int:
    """ファイルからメタデータの更新"""
```

## 7. セキュリティ

### 7.1 アクセス制御
- ファイルシステム権限による基本的なアクセス制御
- プロジェクトフォルダ単位でのデータ隔離
- 読み取り専用・書き込み可能の権限分離

### 7.2 データ保護
```python
def sanitize_filename(self, title: str) -> str:
    """ファイル名の安全な文字列変換"""

def validate_path_safety(self, path: Path) -> bool:
    """パストラバーサル攻撃の防止"""

def backup_before_critical_operations(self) -> None:
    """重要操作前の自動バックアップ"""
```

## 8. 互換性・拡張性

### 8.1 スキーマ進化
```python
def migrate_schema(self, from_version: str, to_version: str) -> bool:
    """スキーママイグレーション（シンプル版）"""

def add_new_field_with_default(self, field_name: str, default_value: Any) -> None:
    """新フィールドの追加（デフォルト値付き）"""
```

### 8.2 他システムとの連携
```python
def export_to_json(self) -> dict:
    """JSON形式でのデータエクスポート"""

def import_from_json(self, json_data: dict) -> bool:
    """JSON形式からのデータインポート"""

def export_to_csv(self) -> str:
    """CSV形式でのエピソード一覧エクスポート"""
```

### 8.3 将来拡張への準備
- プラグイン機能のためのフック機能
- 複数ファイル分割への移行パス
- 外部データベース連携への拡張可能性

## 9. 使用例

### 9.1 基本的な使用パターン
```python
# リポジトリ初期化
project_root = Path("/path/to/project")
repo = SimpleYamlEpisodeRepository(project_root)

# エピソード作成・保存
episode = Episode(
    number=EpisodeNumber(1),
    title=EpisodeTitle("異世界転生"),
    content="俺の名前は田中太郎...",
    status=EpisodeStatus.DRAFT
)
repo.save_episode(episode)

# エピソード検索
found_episode = repo.find_by_number(EpisodeNumber(1))
all_episodes = repo.find_all()

# 統計情報取得
total_count = repo.get_episode_count()
total_words = repo.get_total_word_count()
avg_quality = repo.get_average_quality_score()
```

### 9.2 ステータス管理例
```python
# ドラフト状態のエピソード一覧取得
draft_episodes = repo.find_by_status(EpisodeStatus.DRAFT)

# エピソードステータス更新
repo.update_status(EpisodeNumber(1), EpisodeStatus.COMPLETED)

# 完成済みエピソード数確認
completed = repo.find_by_status(EpisodeStatus.COMPLETED)
print(f"完成済み: {len(completed)}話")
```

### 9.3 バックアップ・復元例
```python
# バックアップ作成
backup_path = repo.create_backup()
print(f"バックアップ作成: {backup_path}")

# バックアップからの復元
success = repo.restore_from_backup(backup_path)
if success:
    print("復元完了")
```

### 9.4 データ検証・修復例
```python
# データ整合性チェック
issues = repo.validate_file_consistency()
if issues:
    print(f"整合性問題発見: {issues}")

# 自動修復実行
fixed_count = repo.repair_missing_episodes()
print(f"修復完了: {fixed_count}件")

# 原稿ファイルとの同期
sync_result = repo.sync_with_manuscript_files()
print(f"同期結果: 更新{sync_result['updated']}件, 新規{sync_result['added']}件")
```

## 10. テスト仕様

### 10.1 単体テスト
```python
class TestSimpleYamlEpisodeRepository:
    def test_save_and_find_episode(self):
        """基本的な保存・検索機能テスト"""

    def test_episode_number_uniqueness(self):
        """エピソード番号一意性テスト"""

    def test_status_filter_search(self):
        """ステータス別検索テスト"""

    def test_statistics_calculation(self):
        """統計計算機能テスト"""

    def test_backup_and_restore(self):
        """バックアップ・復元テスト"""

    def test_data_validation(self):
        """データ検証機能テスト"""

    def test_file_consistency_check(self):
        """ファイル整合性チェックテスト"""

    def test_error_handling(self):
        """エラーハンドリングテスト"""
```

### 10.2 統合テスト
```python
class TestSimpleEpisodeRepositoryIntegration:
    def test_full_episode_lifecycle(self):
        """エピソードの完全ライフサイクルテスト"""

    def test_concurrent_access_safety(self):
        """並行アクセス安全性テスト"""

    def test_large_dataset_performance(self):
        """大量データでの性能テスト"""

    def test_file_system_integration(self):
        """ファイルシステム統合テスト"""
```

### 10.3 エラーシナリオテスト
```python
def test_corrupted_yaml_handling(self):
    """破損YAMLファイルの処理テスト"""

def test_missing_manuscript_files(self):
    """原稿ファイル不足時の処理テスト"""

def test_disk_full_scenario(self):
    """ディスク容量不足時の処理テスト"""

def test_permission_denied_handling(self):
    """ファイル権限エラー時の処理テスト"""
```

## 11. 設定・カスタマイズ

### 11.1 設定ファイル
```yaml
# simple_episode_repository_config.yaml
repository:
  episode_list_filename: "エピソード一覧.yaml"
  manuscript_directory: "40_原稿"
  backup_directory: ".backup"

backup:
  enabled: true
  auto_backup_on_save: false
  retention_days: 30

validation:
  strict_mode: false
  auto_fix_minor_issues: true
  check_file_consistency: true

performance:
  cache_enabled: true
  lazy_loading: false
  batch_size: 50
```

### 11.2 カスタマイズポイント
```python
# カスタムフィールド追加
def add_custom_field(self, field_name: str, field_type: type, default_value: Any) -> None:
    """カスタムフィールドの動的追加"""

# カスタムバリデーション
def add_custom_validator(self, validator_func: Callable[[dict], bool]) -> None:
    """カスタムバリデーションルールの追加"""

# カスタムファイルネーミング
def set_custom_naming_rule(self, naming_func: Callable[[Episode], str]) -> None:
    """カスタムファイル命名規則の設定"""
```

## 12. 運用・監視

### 12.1 ログ出力
```python
# 基本ログ
logger.info(f"Episode saved: number={episode.number}, title='{episode.title}'")
logger.warning(f"Backup file is old: {backup_path}")
logger.error(f"Failed to save episode: {error_message}")

# 統計ログ
logger.info(f"Repository stats: episodes={count}, total_words={words}")
```

### 12.2 メトリクス
```python
# 簡単なメトリクス収集
metrics = {
    'total_episodes': len(episodes),
    'completed_episodes': len([e for e in episodes if e.status == 'COMPLETED']),
    'total_word_count': sum(e.word_count for e in episodes),
    'average_episode_length': total_words / len(episodes),
    'repository_file_size_mb': file_size_mb,
    'last_backup_age_hours': (datetime.now() - last_backup).total_seconds() / 3600
}
```

### 12.3 健全性チェック
```python
def health_check(self) -> dict[str, Any]:
    """リポジトリの健全性チェック"""
    return {
        'status': 'healthy',
        'yaml_file_accessible': True,
        'manuscript_files_present': True,
        'data_integrity_ok': True,
        'backup_available': backup_exists,
        'last_operation': self.last_operation_time.isoformat()
    }
```

## 13. 実装メモ

### 13.1 実装ファイル
- **メインクラス**: `src/noveler/infrastructure/repositories/simple_yaml_episode_repository.py`
- **設定クラス**: `SimpleRepositoryConfig` クラス
- **テストファイル**: `tests/unit/infrastructure/repositories/test_simple_yaml_episode_repository.py`
- **統合テスト**: `tests/integration/test_simple_episode_workflow.py`

### 13.2 設計方針
- **KISS原則**: 機能を最小限に絞った単純な設計
- **透明性**: YAMLファイルを人間が直接編集可能
- **堅牢性**: エラー時の安全な縮退動作
- **移植性**: 外部依存関係を最小限に抑制

### 13.3 パフォーマンス最適化
```python
# キャッシュ機能（オプション）
def _load_with_cache(self) -> dict:
    """キャッシュ付きデータ読み込み"""

# 遅延読み込み（オプション）
def _lazy_load_episodes(self) -> Iterator[Episode]:
    """遅延読み込みによるメモリ最適化"""

# バッチ処理（オプション）
def save_episodes_batch(self, episodes: list[Episode]) -> None:
    """バッチ保存によるI/O最適化"""
```

### 13.4 今後の改善点
- [ ] インメモリキャッシュ機能の追加
- [ ] 増分バックアップ機能
- [ ] ファイルウォッチ機能による自動同期
- [ ] 軽量なインデックス機能
- [ ] 圧縮によるファイルサイズ最適化
- [ ] 並行アクセス時の排他制御強化
- [ ] エピソードテンプレート機能
- [ ] 簡単なデータ分析機能

## 14. 利用シナリオ

### 14.1 個人プロジェクト
- 小規模な小説プロジェクト（〜50話）
- 個人執筆者向けの簡単管理
- 学習・実験プロジェクト

### 14.2 プロトタイプ開発
- 新機能のプロトタイプ実装
- 概念実証（Proof of Concept）
- システム設計の検証

### 14.3 教育用途
- DDD学習用のシンプルな実装例
- リポジトリパターンの理解
- YAML操作の学習
