# YAML品質記録リポジトリ仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、品質記録エンティティのYAMLファイルベース永続化を提供する。品質チェック結果、改訂履歴、エピソード状態管理を統合的に行う。

### 1.2 スコープ
- 品質記録の作成・保存・検索・削除の完全な永続化機能
- トランザクション管理による複数ファイルの整合性保証
- エピソード状態管理との連携
- 改訂履歴の自動記録
- データ整合性とエラー回復機能

### 1.3 アーキテクチャ位置
```
Domain Layer
├── QualityRecordRepository (Interface)         ← Infrastructure Layer
├── EpisodeManagementRepository (Interface)     └── YamlQualityRecordRepository (Implementation)
├── RevisionHistoryRepository (Interface)       └── YamlEpisodeManagementRepository (Implementation)
├── RecordTransactionManager (Interface)        └── YamlRevisionHistoryRepository (Implementation)
└── QualityRecord (Entity)                      └── YamlRecordTransactionManager (Implementation)
```

### 1.4 ビジネス価値
- **執筆品質の継続的向上**: AI学習型品質分析による個人化改善提案
- **データ駆動型執筆**: 長期的な品質トレンド分析と成長可視化
- **信頼性の高いデータ管理**: トランザクション管理による完全性保証

## 2. 機能仕様

### 2.1 基本CRUD操作
```python
# YamlQualityRecordRepository
def find_by_project(project_name: str) -> QualityRecord | None
def save(quality_record: QualityRecord) -> None
def exists(project_name: str) -> bool
def delete(project_name: str) -> bool
```

### 2.2 エピソード状態管理
```python
# YamlEpisodeManagementRepository
def update_quality_scores(
    project_path: Path,
    episode_number: int,
    quality_result: QualityCheckResult
) -> None

def get_episode_info(project_path: Path, episode_number: int) -> dict | None
```

### 2.3 改訂履歴管理
```python
# YamlRevisionHistoryRepository
def add_quality_revision(project_path: Path, quality_result: QualityCheckResult) -> None
def get_recent_revisions(
    project_path: Path,
    episode_number: int,
    limit: int = 10
) -> list[dict]
```

### 2.4 トランザクション管理
```python
# YamlRecordTransactionManager
@contextmanager
def begin_transaction() -> YamlTransaction:
    """統合トランザクション管理"""

# YamlTransaction
def update_quality_record(quality_record: QualityRecord) -> None
def update_episode_management(
    project_path: Path,
    episode_number: int,
    quality_result: QualityCheckResult
) -> None
def update_revision_history(project_path: Path, quality_result: QualityCheckResult) -> None
def commit() -> None
def rollback() -> None
```

## 3. データ構造仕様

### 3.1 ファイル配置
```
プロジェクトルート/
├── 50_管理資料/                    # 管理データ（YAML）
│   ├── 品質記録.yaml               # 品質記録統合ファイル
│   ├── 話数管理.yaml               # 話数管理メタデータ
│   ├── 改訂履歴.yaml               # 改訂履歴
│   └── .backup/                    # バックアップファイル
│       ├── 品質記録_20250721_143022.yaml
│       ├── 話数管理_20250721_143022.yaml
│       └── 改訂履歴_20250721_143022.yaml
└── backup/                         # アーカイブバックアップ（オプション）
```

### 3.2 品質記録YAML構造
```yaml
metadata:
  project_name: "転生したら最強の魔法使いだった件"
  created_at: "2025-07-15T10:30:00"
  last_updated: "2025-07-21T14:30:22"
  total_checks: 15
  schema_version: "2.1.0"

quality_checks:
  - id: "quality-check-20250721-143022-001"
    episode_number: 1
    timestamp: "2025-07-21T14:30:22"
    checker_version: "2.1.0"
    results:
      category_scores:
        basic_style: 88.5
        composition: 92.3
        character_consistency: 85.7
        readability: 90.1
      overall_score: 89.2
      error_count: 2
      warning_count: 5
      errors:
        - type: "style_inconsistency"
          message: "敬語の使い分けが不一致"
          line_number: 45
          severity: "error"
          fixed: false
          suggestion: "文脈に応じた敬語使用を確認してください"
      warnings:
        - type: "readability"
          message: "長い文章が続いています"
          line_number: 23
          severity: "warning"
          fixed: false
          suggestion: "文章を分割することを検討してください"
      auto_fixes:
        - type: "punctuation"
          description: "句読点の統一"
          count: 3
          affected_lines: [12, 28, 35]
    metadata:
      execution_time_ms: 1250
      file_size_bytes: 8472
      original_errors: 5
      ai_learning_data:
        improvement_trend: 5.2
        common_issues: ["punctuation", "sentence_length"]
        writer_level: "intermediate"

  - id: "quality-check-20250720-091500-001"
    episode_number: 1
    timestamp: "2025-07-20T09:15:00"
    # 以前のチェック結果...

ai_learning:
  improvement_trends:
    overall_quality: 12.3
    category_improvements:
      basic_style: 8.5
      composition: 15.2
      character_consistency: 10.8
  common_issues:
    - issue_type: "punctuation"
      frequency: 0.23
      improvement_rate: 0.85
    - issue_type: "sentence_length"
      frequency: 0.18
      improvement_rate: 0.72
  writer_profile:
    level: "intermediate"
    strengths: ["composition", "character_consistency"]
    focus_areas: ["basic_style", "readability"]
    learning_velocity: 1.2
```

### 3.3 話数管理YAML構造
```yaml
episodes:
  - episode_number: 1
    title: "異世界転生"
    status: "quality_checked"
    quality_score: 89.2
    last_check: "2025-07-21T14:30:22"
    error_count: 2
    warning_count: 5
    word_count: 3247
    target_words: 3000
    version: 2

metadata:
  last_updated: "2025-07-21T14:30:22"
  total_episodes: 15
  average_quality: 87.3
  quality_trend: "improving"
```

### 3.4 改訂履歴YAML構造
```yaml
revisions:
  - id: "quality-20250721-143022-1"
    timestamp: "2025-07-21T14:30:22"
    episode_number: 1
    revision_type: "quality_check"
    quality_score: 89.2
    error_count: 2
    warning_count: 5
    auto_fix_count: 3
    checker_version: "2.1.0"
    description: "Episode 1 quality check (Score: 89.2)"

metadata:
  total_revisions: 48
  last_updated: "2025-07-21T14:30:22"
```

## 4. 技術仕様

### 4.1 依存関係
```python
# 外部ライブラリ
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any
from contextlib import contextmanager

# ドメイン層
from domain.entities.quality_record import QualityRecord, QualityRecordEntry
from domain.repositories.quality_record_repository import (
    QualityRecordRepository, EpisodeManagementRepository,
    RevisionHistoryRepository, RecordTransactionManager
)
from domain.value_objects.quality_check_result import (
    QualityCheckResult, CategoryScores, QualityScore, QualityError, AutoFix
)
from domain.exceptions import QualityRecordError, RecordTransactionError

# インフラ層
from infrastructure.utils.yaml_utils import YAMLHandler  # オプショナル
```

### 4.2 エラーハンドリング
```python
# カスタム例外
class QualityRecordError(Exception):
    """品質記録関連エラー"""
    pass

class RecordTransactionError(Exception):
    """トランザクション関連エラー"""
    pass

class QualityRecordParseError(QualityRecordError):
    """品質記録解析エラー"""
    pass

class QualityRecordSaveError(QualityRecordError):
    """品質記録保存エラー"""
    pass
```

### 4.3 バックアップ戦略
```python
def _create_backup(self, file_path: Path) -> None:
    """自動バックアップ作成

    - タイムスタンプ付きファイル名
    - .backup/フォルダに格納
    - メタデータ保持
    """
```

## 5. パフォーマンス要件

### 5.1 応答時間
- 品質記録検索: 100ms以内
- 品質記録保存: 200ms以内（バックアップ含む）
- トランザクション実行: 500ms以内
- 改訂履歴検索: 50ms以内

### 5.2 メモリ使用量
- 単一品質記録: 5MB以内
- 全履歴同時読み込み: 50MB以内
- トランザクション処理: 10MB以内

### 5.3 ファイルサイズ制限
- 品質記録ファイル: 100MB以内
- バックアップファイル総量: 1GB以内
- 改訂履歴ファイル: 20MB以内

## 6. 品質保証

### 6.1 データ整合性
- 品質記録とエピソード状態の同期保証
- トランザクション完全性の保証
- YAMLスキーマの妥当性検証
- エピソード番号の一意性保証

### 6.2 エラー回復
```python
# データ破損検出と復旧
def validate_quality_record(self, data: dict) -> bool:
    """品質記録データの妥当性検証"""

def repair_corrupted_data(self, file_path: Path) -> bool:
    """破損データの自動修復"""

def restore_from_backup(self, project_name: str, backup_timestamp: str) -> bool:
    """バックアップからの復元"""
```

### 6.3 バージョン管理
- スキーマバージョンの追跡
- 下位互換性の保証
- マイグレーション機能
- データフォーマット変換

## 7. セキュリティ

### 7.1 アクセス制御
- ファイルシステム権限に基づく制御
- プロジェクト単位でのデータ分離
- バックアップファイルの適切な権限設定

### 7.2 データ保護
- UTF-8エンコーディング統一
- 特殊文字のエスケープ処理
- パスインジェクション攻撃の防止
- 機密情報の適切な除去

## 8. 拡張性・互換性

### 8.1 スキーマ進化
- 新しい品質指標の追加対応
- AI学習データの拡張
- メタデータフィールドの動的追加
- 下位互換性の維持

### 8.2 外部システム連携
- 他の品質管理システムとの連携
- CI/CDパイプラインとの統合
- 分析ツールへのデータエクスポート
- リアルタイム通知システム

## 9. 使用例

### 9.1 基本的な使用パターン
```python
# リポジトリ初期化
base_path = Path("/path/to/projects")
quality_repo = YamlQualityRecordRepository(base_path)
episode_repo = YamlEpisodeManagementRepository()
revision_repo = YamlRevisionHistoryRepository()

# 品質記録の保存
quality_record = QualityRecord("project-001", entries)
quality_repo.save(quality_record)

# 品質記録の検索
found_record = quality_repo.find_by_project("project-001")
```

### 9.2 トランザクション使用例
```python
# トランザクションマネージャー初期化
tx_manager = YamlRecordTransactionManager(
    quality_repo, episode_repo, revision_repo
)

# 統合更新処理
with tx_manager.begin_transaction() as tx:
    # 品質記録更新
    tx.update_quality_record(updated_record)

    # エピソード状態更新
    tx.update_episode_management(project_path, 1, quality_result)

    # 改訂履歴追加
    tx.update_revision_history(project_path, quality_result)

    # 自動コミット（エラー時は自動ロールバック）
```

### 9.3 AI学習データ活用例
```python
# 品質記録からAI学習データを取得
quality_record = quality_repo.find_by_project("project-001")
learning_data = quality_record.get_ai_learning_data()

# 改善提案の生成
suggestions = learning_data.generate_improvement_suggestions()
print(f"推奨改善項目: {suggestions['focus_areas']}")
print(f"成長トレンド: {suggestions['improvement_trend']}")
```

### 9.4 データ分析・レポート例
```python
# 品質トレンド分析
def analyze_quality_trend(project_name: str) -> dict:
    record = quality_repo.find_by_project(project_name)
    if not record:
        return {}

    # 時系列での品質変化を分析
    entries = record.get_recent_entries(30)  # 直近30回
    trend_data = {
        'average_quality': sum(e.quality_result.overall_score.to_float()
                             for e in entries) / len(entries),
        'improvement_rate': calculate_improvement_rate(entries),
        'common_issues': extract_common_issues(entries)
    }

    return trend_data
```

## 10. テスト仕様

### 10.1 単体テスト
```python
# 主要テストケース
class TestYamlQualityRecordRepository:
    def test_save_and_find_quality_record(self):
        """品質記録の保存・検索機能テスト"""

    def test_quality_record_serialization(self):
        """シリアライゼーション・デシリアライゼーションテスト"""

    def test_backup_creation(self):
        """バックアップ作成テスト"""

    def test_error_handling(self):
        """エラーハンドリングテスト"""

class TestYamlRecordTransactionManager:
    def test_successful_transaction(self):
        """正常トランザクションテスト"""

    def test_transaction_rollback(self):
        """トランザクションロールバックテスト"""

    def test_concurrent_transactions(self):
        """並行トランザクションテスト"""
```

### 10.2 統合テスト
```python
class TestQualityRecordIntegration:
    def test_full_quality_check_workflow(self):
        """品質チェック→記録→分析の完全ワークフローテスト"""

    def test_multi_project_isolation(self):
        """複数プロジェクトでのデータ分離テスト"""

    def test_large_dataset_performance(self):
        """大量データでの性能テスト"""
```

### 10.3 エラーシナリオテスト
```python
def test_corrupted_yaml_recovery(self):
    """破損YAMLファイルの復旧テスト"""

def test_disk_space_shortage(self):
    """ディスク容量不足時の動作テスト"""

def test_concurrent_write_conflict(self):
    """並行書き込み競合の処理テスト"""
```

## 11. AI学習統合機能

### 11.1 学習データ構造
```yaml
ai_learning:
  improvement_trends:
    overall_quality: 12.3        # 全体的な改善度
    category_improvements:
      basic_style: 8.5          # カテゴリ別改善度
      composition: 15.2
      character_consistency: 10.8
      readability: 9.7

  common_issues:
    - issue_type: "punctuation"
      frequency: 0.23           # 発生頻度
      improvement_rate: 0.85    # 改善率
      severity_trend: "decreasing"

  writer_profile:
    level: "intermediate"       # 執筆レベル
    strengths: ["composition", "character_consistency"]
    focus_areas: ["basic_style", "readability"]
    learning_velocity: 1.2     # 学習速度
    consistency_score: 0.78    # 一貫性スコア

  predictions:
    next_quality_score: 91.5   # 次回品質予測
    improvement_timeline: "2-3 weeks"
    recommended_focus: "sentence_structure"
```

### 11.2 AI分析機能
```python
class AILearningDataAnalyzer:
    def analyze_writing_pattern(self, entries: list[QualityRecordEntry]) -> WritingPattern:
        """執筆パターン分析"""

    def generate_personalized_suggestions(self, writer_profile: WriterProfile) -> list[str]:
        """個人化改善提案生成"""

    def predict_quality_trend(self, historical_data: list[QualityCheckResult]) -> QualityPrediction:
        """品質トレンド予測"""

    def identify_improvement_opportunities(self, recent_checks: list[QualityCheckResult]) -> list[ImprovementOpportunity]:
        """改善機会の特定"""
```

## 12. 運用・監視

### 12.1 ログ出力
```python
# 重要操作のログ記録
logger.info(f"Quality record saved: project={project_name}, entries={len(entries)}")
logger.error(f"Failed to parse quality record: {error_message}")
logger.warning(f"Large quality record detected: size={file_size}MB")
logger.debug(f"Transaction completed: operations={operation_count}, duration={duration}ms")
```

### 12.2 メトリクス収集
```python
# パフォーマンスメトリクス
metrics = {
    'save_operations_per_hour': 45,
    'average_save_time_ms': 125,
    'backup_file_count': 128,
    'total_storage_usage_mb': 256,
    'transaction_success_rate': 0.998
}
```

### 12.3 アラート条件
- 品質記録ファイルサイズ > 50MB
- トランザクション失敗率 > 1%
- バックアップ作成失敗
- ディスク使用量 > 80%
- YAMLパースエラー頻発

## 13. 実装メモ

### 13.1 実装ファイル
- **メインクラス**: `src/noveler/infrastructure/repositories/yaml_quality_record_repository.py`
- **テストファイル**: `tests/unit/infrastructure/repositories/test_yaml_quality_record_repository.py`
- **統合テスト**: `tests/integration/test_quality_record_workflow.py`

### 13.2 設計方針
- **DDD原則の厳格な遵守**: ドメインロジックの完全分離
- **トランザクション整合性**: ACID特性の部分的実装
- **エラー時のグレースフルデグラデーション**: 部分的復旧機能
- **AI学習データの構造化**: 機械学習フレンドリーなデータ形式

### 13.3 今後の改善点
- [ ] 分散ファイルシステム対応
- [ ] リアルタイムデータ同期
- [ ] 機械学習モデルとの直接統合
- [ ] GraphQL APIによるデータ公開
- [ ] 分析ダッシュボードの構築
- [ ] 自動データクレンジング機能
- [ ] 異常検知アルゴリズムの統合
- [ ] クラウドストレージバックアップ
