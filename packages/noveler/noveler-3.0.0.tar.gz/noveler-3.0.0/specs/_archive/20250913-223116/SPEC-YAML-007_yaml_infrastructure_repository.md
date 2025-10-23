# YAMLインフラストラクチャーリポジトリ仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、インフラストラクチャー統合アグリゲートとその設定の永続化を提供する。複数のアダプターやサービスの統合管理を行い、システム全体のインフラ設定を一元化する。

### 1.2 スコープ
- インフラストラクチャー設定の作成・保存・検索・削除機能
- アグリゲート状態の完全な永続化・復元機能
- サービス設定の動的管理
- バックアップ・復元・統計機能
- 複数実装（YAML、メモリ）のファクトリーパターン

### 1.3 アーキテクチャ位置
```
Domain Layer
├── InfrastructureIntegrationAggregate (Aggregate Root)    ← Infrastructure Layer
├── InfrastructureConfiguration (Value Object)            └── YamlInfrastructureRepository
├── ServiceConfiguration (Value Object)                   └── MemoryInfrastructureRepository
├── ServiceStatus (Enum)                                   └── InfrastructureRepositoryFactory
└── CacheConfiguration (Value Object)
```

### 1.4 ビジネス価値
- **統合インフラ管理**: 全サービス・アダプターの一元管理による運用効率向上
- **設定の永続化**: 複雑なインフラ設定の安全な保存と復元
- **スケーラブルアーキテクチャ**: マルチプロジェクト対応の拡張可能な設計
- **運用監視**: サービスメトリクス・統計の自動収集

## 2. 機能仕様

### 2.1 インフラストラクチャー設定管理
```python
# 基本CRUD操作
def save_infrastructure_configuration(
    project_id: str,
    config: InfrastructureConfiguration
) -> None

def load_infrastructure_configuration(
    project_id: str
) -> InfrastructureConfiguration | None

def delete_project_configuration(project_id: str) -> None
def list_project_configurations() -> list[str]
```

### 2.2 サービス設定管理
```python
# サービス固有の設定管理
def save_service_configuration(
    project_id: str,
    service_config: ServiceConfiguration
) -> None

def remove_service_configuration(
    project_id: str,
    service_name: str
) -> None
```

### 2.3 アグリゲート状態管理
```python
# アグリゲート永続化・復元
def save_aggregate_state(
    aggregate: InfrastructureIntegrationAggregate
) -> None

def load_aggregate_state(project_id: str) -> dict[str, Any] | None

def restore_aggregate(
    project_id: str
) -> InfrastructureIntegrationAggregate | None
```

### 2.4 バックアップ・復元機能
```python
# データ保護・復旧
def backup_configurations(backup_dir: Path | None = None) -> Path
def restore_from_backup(backup_dir: Path) -> None
def get_repository_statistics() -> dict[str, Any]
```

### 2.5 ファクトリーパターン
```python
# InfrastructureRepositoryFactory
@staticmethod
def create_yaml_repository(
    base_path: Path | None = None,
    create_directories: bool = True
) -> YamlInfrastructureRepository

@staticmethod
def create_memory_repository() -> MemoryInfrastructureRepository
```

## 3. データ構造仕様

### 3.1 ファイル配置
```
base_path/
├── infrastructure_configs/              # インフラ設定ディレクトリ
│   ├── project-001_infrastructure.yaml  # プロジェクト別インフラ設定
│   ├── project-001_aggregate_state.yaml # アグリゲート状態
│   ├── project-002_infrastructure.yaml
│   ├── project-002_aggregate_state.yaml
│   └── ...
└── infrastructure_backup_20250721_143022/ # タイムスタンプ付きバックアップ
    ├── project-001_infrastructure.yaml
    ├── project-001_aggregate_state.yaml
    └── ...
```

### 3.2 インフラストラクチャー設定YAML構造
```yaml
# project-001_infrastructure.yaml
metadata:
  project_id: "project-001"
  saved_at: "2025-07-21T14:30:22"
  version: "1.0"
  schema_version: "2.1.0"

configuration:
  performance:
    max_concurrent_operations: 10
    timeout_seconds: 30
    retry_count: 3
    circuit_breaker_threshold: 5
    memory_limit_mb: 256

  cache:
    enabled: true
    ttl_seconds: 3600
    max_entries: 1000
    storage_type: "memory"  # memory, redis, file
    compression_enabled: true
    cache_policy: "LRU"

  services:
    - service_id: "quality-checker-v2"
      service_type: "QUALITY_CHECKER"
      name: "統合品質チェッカー"
      adapter_class: "QualityCheckerAdapter"
      enabled: true
      priority: 1
      configuration:
        check_types: ["style", "composition", "consistency"]
        auto_fix_enabled: true
        severity_threshold: "warning"
        batch_size: 50

    - service_id: "backup-manager-v1"
      service_type: "BACKUP"
      name: "バックアップマネージャー"
      adapter_class: "BackupAdapter"
      enabled: true
      priority: 2
      configuration:
        backup_interval: "daily"
        retention_days: 30
        compression_level: 6
        storage_path: "/backup/project-001"

  integrations:
    git_integration:
      enabled: true
      auto_commit: true
      branch_strategy: "feature"

    notification_service:
      enabled: true
      channels: ["email", "slack"]
      severity_filter: "error"
```

### 3.3 アグリゲート状態YAML構造
```yaml
# project-001_aggregate_state.yaml
metadata:
  aggregate_id: "infra-agg-20250721-143022"
  project_id: "project-001"
  saved_at: "2025-07-21T14:30:22"
  version: "1.0"
  schema_version: "2.1.0"

aggregate_state:
  created_at: "2025-07-15T10:30:00"
  last_activity: "2025-07-21T14:30:22"
  total_executions: 1247
  successful_executions: 1198
  global_config:
    environment: "development"
    log_level: "INFO"
    debug_mode: false
  project_config:
    project_name: "転生したら最強の魔法使いだった件"
    target_quality_score: 85.0
    auto_enhancement: true
  cache_config:
    cache_size_mb: 128
    cache_hit_rate: 0.87
    cache_entries: 542

services:
  - service_id: "quality-checker-v2-instance-1"
    service_type: "QUALITY_CHECKER"
    name: "統合品質チェッカー"
    adapter_class: "QualityCheckerAdapter"
    status: "ACTIVE"
    created_at: "2025-07-15T10:30:00"
    last_execution: "2025-07-21T14:29:45"
    metrics:
      total_executions: 87
      successful_executions: 84
      failed_executions: 3
      average_execution_time: 1.23
      peak_memory_usage: 45.6
      error_rate: 0.034
      last_execution_time: "2025-07-21T14:29:45"
    configuration:
      check_types: ["style", "composition", "consistency"]
      auto_fix_enabled: true
      severity_threshold: "warning"

  - service_id: "backup-manager-v1-instance-1"
    service_type: "BACKUP"
    name: "バックアップマネージャー"
    adapter_class: "BackupAdapter"
    status: "STANDBY"
    created_at: "2025-07-15T10:35:00"
    last_execution: "2025-07-21T00:00:00"
    metrics:
      total_executions: 6
      successful_executions: 6
      failed_executions: 0
      average_execution_time: 15.2
      peak_memory_usage: 78.3
      error_rate: 0.0
      last_execution_time: "2025-07-21T00:00:00"
    configuration:
      backup_interval: "daily"
      retention_days: 30
```

## 4. 技術仕様

### 4.1 依存関係
```python
# 外部ライブラリ
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any
from __future__ import annotations

# ドメイン層
from domain.entities.infrastructure_integration_aggregate import (
    InfrastructureIntegrationAggregate, ServiceStatus
)
from domain.value_objects.infrastructure_configuration import (
    InfrastructureConfiguration, ServiceConfiguration,
    PerformanceConfiguration, CacheConfiguration
)

# インフラ層（オプショナル）
from infrastructure.utils.yaml_utils import YAMLHandler  # 高度なYAML処理
```

### 4.2 エラーハンドリング
```python
# カスタム例外
class InfrastructureRepositoryError(Exception):
    """インフラリポジトリ関連エラー"""
    pass

class ConfigurationLoadError(InfrastructureRepositoryError):
    """設定読み込みエラー"""
    pass

class ConfigurationSaveError(InfrastructureRepositoryError):
    """設定保存エラー"""
    pass

class AggregateStateError(InfrastructureRepositoryError):
    """アグリゲート状態エラー"""
    pass

class BackupRestoreError(InfrastructureRepositoryError):
    """バックアップ・復元エラー"""
    pass
```

### 4.3 設定検証
```python
def validate_infrastructure_config(self, config: InfrastructureConfiguration) -> bool:
    """インフラ設定の妥当性検証"""

def validate_service_config(self, service_config: ServiceConfiguration) -> bool:
    """サービス設定の妥当性検証"""

def validate_aggregate_state(self, state_data: dict) -> bool:
    """アグリゲート状態の妥当性検証"""
```

## 5. パフォーマンス要件

### 5.1 応答時間
- インフラ設定保存: 200ms以内
- インフラ設定読み込み: 100ms以内
- アグリゲート状態保存: 500ms以内（サービス数に依存）
- アグリゲート復元: 800ms以内
- バックアップ作成: 2秒以内（ファイル数に依存）

### 5.2 メモリ使用量
- 単一インフラ設定: 1MB以内
- アグリゲート状態: 10MB以内（サービス100個想定）
- 全プロジェクト同時読み込み: 100MB以内

### 5.3 ファイルサイズ制限
- インフラ設定ファイル: 5MB以内
- アグリゲート状態ファイル: 20MB以内
- バックアップ総量: 500MB以内

## 6. 品質保証

### 6.1 データ整合性
- インフラ設定とアグリゲート状態の同期保証
- サービス設定の一意性保証
- YAML スキーマ妥当性検証
- 設定バージョン管理

### 6.2 エラー回復
```python
# データ修復機能
def repair_corrupted_config(self, project_id: str) -> bool:
    """破損した設定ファイルの修復"""

def validate_and_fix_aggregate_state(self, project_id: str) -> bool:
    """アグリゲート状態の検証・修復"""

def recover_from_backup_automatically(self, project_id: str) -> bool:
    """バックアップからの自動復旧"""
```

### 6.3 設定マイグレーション
```python
def migrate_configuration_schema(
    self,
    project_id: str,
    from_version: str,
    to_version: str
) -> bool:
    """設定スキーマのマイグレーション"""
```

## 7. セキュリティ

### 7.1 アクセス制御
- ファイルシステム権限ベースの制御
- プロジェクト単位でのデータ隔離
- 設定ファイルの適切な権限設定（600）
- バックアップファイルの暗号化オプション

### 7.2 データ保護
- 機密情報（API キー等）の暗号化
- 設定変更の監査ログ
- 不正な設定変更の検出
- パス・インジェクション攻撃の防止

## 8. 拡張性・統合性

### 8.1 プラガブル・アーキテクチャ
```python
# 抽象インターフェース
class InfrastructureRepository(ABC):
    @abstractmethod
    def save_infrastructure_configuration(self, project_id: str, config: InfrastructureConfiguration) -> None:
        pass

    @abstractmethod
    def load_infrastructure_configuration(self, project_id: str) -> InfrastructureConfiguration | None:
        pass
```

### 8.2 外部システム連携
- CI/CD パイプラインとの統合
- 外部設定管理システム（Consul、etcd）との連携
- 監視システム（Prometheus）へのメトリクス公開
- 通知システム（Slack、メール）との統合

### 8.3 クラウド対応
- S3、GCS等のクラウドストレージ対応
- Kubernetes ConfigMap 連携
- Docker Compose 設定の自動生成
- Infrastructure as Code（Terraform）連携

## 9. 使用例

### 9.1 基本的な使用パターン
```python
# リポジトリ作成
repo = InfrastructureRepositoryFactory.create_yaml_repository(
    base_path=Path("/project/configs")
)

# インフラ設定作成・保存
config = InfrastructureConfiguration(
    performance=PerformanceConfiguration(max_concurrent_operations=10),
    cache=CacheConfiguration(enabled=True, ttl_seconds=3600),
    services=[
        ServiceConfiguration(
            service_id="quality-checker",
            service_type=ServiceType.QUALITY_CHECKER,
            name="統合品質チェッカー",
            adapter_class="QualityCheckerAdapter"
        )
    ]
)

repo.save_infrastructure_configuration("project-001", config)

# 設定読み込み
loaded_config = repo.load_infrastructure_configuration("project-001")
```

### 9.2 アグリゲート管理例
```python
# アグリゲート作成
aggregate = InfrastructureIntegrationAggregate(
    aggregate_id="infra-001",
    project_id="project-001",
    global_config={"environment": "production"},
    project_config={"target_quality_score": 90.0},
    cache_config={"cache_size_mb": 256}
)

# サービス登録
service_config = ServiceConfiguration(
    service_id="quality-checker-v2",
    service_type=ServiceType.QUALITY_CHECKER,
    name="品質チェッカーV2",
    adapter_class="EnhancedQualityCheckerAdapter"
)
service = aggregate.register_service(service_config)

# アグリゲート状態保存
repo.save_aggregate_state(aggregate)

# アグリゲート復元
restored_aggregate = repo.restore_aggregate("project-001")
```

### 9.3 サービス動的管理例
```python
# 新しいサービス追加
new_service = ServiceConfiguration(
    service_id="analytics-service",
    service_type=ServiceType.ANALYTICS,
    name="分析サービス",
    adapter_class="AnalyticsAdapter",
    configuration={"batch_size": 100, "interval": 300}
)

repo.save_service_configuration("project-001", new_service)

# サービス削除
repo.remove_service_configuration("project-001", "old-service")
```

### 9.4 バックアップ・復元例
```python
# 自動バックアップ
backup_dir = repo.backup_configurations()
print(f"バックアップ作成完了: {backup_dir}")

# 指定バックアップ
custom_backup = Path("/backups/manual_backup_20250721")
repo.backup_configurations(custom_backup)

# バックアップからの復元
repo.restore_from_backup(backup_dir)

# 統計情報取得
stats = repo.get_repository_statistics()
print(f"管理中プロジェクト数: {stats['total_projects']}")
print(f"総ファイルサイズ: {stats['total_size_bytes']} bytes")
```

## 10. テスト仕様

### 10.1 単体テスト
```python
class TestYamlInfrastructureRepository:
    def test_save_and_load_infrastructure_configuration(self):
        """インフラ設定の保存・読み込みテスト"""

    def test_service_configuration_management(self):
        """サービス設定の動的管理テスト"""

    def test_aggregate_state_persistence(self):
        """アグリゲート状態の永続化テスト"""

    def test_backup_and_restore(self):
        """バックアップ・復元機能テスト"""

    def test_error_handling(self):
        """エラーハンドリングテスト"""

class TestInfrastructureRepositoryFactory:
    def test_factory_pattern(self):
        """ファクトリーパターンのテスト"""

    def test_memory_repository_for_testing(self):
        """テスト用メモリリポジトリのテスト"""
```

### 10.2 統合テスト
```python
class TestInfrastructureRepositoryIntegration:
    def test_full_lifecycle_workflow(self):
        """設定→サービス登録→実行→状態保存の完全ワークフローテスト"""

    def test_multi_project_management(self):
        """複数プロジェクトの同時管理テスト"""

    def test_concurrent_access(self):
        """並行アクセステスト"""

    def test_large_configuration_performance(self):
        """大規模設定での性能テスト"""
```

### 10.3 エラーシナリオテスト
```python
def test_corrupted_yaml_handling(self):
    """破損YAMLファイルの処理テスト"""

def test_partial_backup_restoration(self):
    """部分的バックアップからの復元テスト"""

def test_configuration_schema_migration(self):
    """設定スキーママイグレーションテスト"""
```

## 11. 監視・メトリクス

### 11.1 運用メトリクス
```python
# 収集すべきメトリクス
metrics = {
    'repository_operations': {
        'config_saves_per_hour': 12,
        'config_loads_per_hour': 45,
        'aggregate_saves_per_hour': 8,
        'backup_operations_per_day': 24
    },
    'performance_metrics': {
        'average_save_time_ms': 150,
        'average_load_time_ms': 75,
        'average_backup_time_ms': 1200,
        'cache_hit_rate': 0.85
    },
    'storage_metrics': {
        'total_config_files': 15,
        'total_storage_mb': 45.6,
        'backup_storage_mb': 120.3,
        'largest_config_mb': 2.1
    },
    'error_metrics': {
        'config_load_errors_per_day': 2,
        'backup_failures_per_week': 0,
        'corrupted_files_detected': 1
    }
}
```

### 11.2 アラート条件
- 設定ファイルサイズ > 3MB
- バックアップ失敗率 > 5%
- 設定読み込みエラー率 > 2%
- ディスク使用量 > 400MB
- アグリゲート復元失敗

### 11.3 ヘルスチェック
```python
def health_check(self) -> dict[str, Any]:
    """リポジトリヘルスチェック"""
    return {
        'status': 'healthy',
        'config_directory_accessible': True,
        'backup_directory_writable': True,
        'recent_errors': 0,
        'last_successful_operation': datetime.now().isoformat(),
        'storage_usage_percentage': 15.2
    }
```

## 12. 実装メモ

### 12.1 実装ファイル
- **メインクラス**: `src/noveler/infrastructure/repositories/yaml_infrastructure_repository.py`
- **テストファイル**: `tests/unit/infrastructure/repositories/test_yaml_infrastructure_repository.py`
- **統合テスト**: `tests/integration/test_infrastructure_repository_workflow.py`
- **ファクトリー**: `InfrastructureRepositoryFactory` クラス内部実装

### 12.2 設計方針
- **DDD原則の厳格な遵守**: インフラ関心事とドメインロジックの完全分離
- **ファクトリーパターン**: 環境に応じたリポジトリ実装の切り替え
- **設定のイミュータブル性**: Value Object による設定変更の安全性保証
- **スキーマ進化対応**: バージョン管理による下位互換性維持

### 12.3 今後の改善点
- [ ] 分散設定管理（Consul、etcd）対応
- [ ] 設定変更の Real-time 同期
- [ ] GraphQL による設定クエリAPI
- [ ] 設定テンプレート機能
- [ ] 設定ドリフト検出機能
- [ ] 自動設定最適化機能
- [ ] Kubernetes Operator 統合
- [ ] Infrastructure as Code 生成機能
