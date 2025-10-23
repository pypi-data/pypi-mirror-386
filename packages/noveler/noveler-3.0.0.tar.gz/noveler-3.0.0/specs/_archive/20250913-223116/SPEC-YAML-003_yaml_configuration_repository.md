# YAML設定管理リポジトリ仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、アプリケーション設定、プロジェクト設定、システム設定の統合的なYAMLファイルベース永続化を提供する。階層的な設定管理と環境別設定を支援する。

### 1.2 スコープ
- 多層設定アーキテクチャ（システム・プロジェクト・ユーザー設定）
- 環境別設定管理（開発・テスト・本番環境）
- 設定継承・オーバーライド機能
- 設定値検証・型安全機能
- 設定変更履歴・バージョン管理
- 動的設定リロード・ホットスワップ

### 1.3 アーキテクチャ位置
```
Domain Layer
├── ConfigurationRepository (Interface)       ← Infrastructure Layer
├── Configuration (Aggregate Root)            └── YamlConfigurationRepository (Implementation)
├── ConfigurationSection (Entity)             └── ConfigurationFactory
├── ConfigurationValue (Value Object)         └── ConfigurationValidator
└── ConfigurationScope (Enum)                 └── ConfigurationMigrator
```

### 1.4 ビジネス価値
- **柔軟な設定管理**: 環境・プロジェクト・ユーザー別の階層的設定
- **運用効率向上**: 設定変更の即座反映とロールバック機能
- **品質保証**: 設定値の型安全性と妥当性検証
- **拡張性**: 新しい設定項目の動的追加と管理

## 2. 機能仕様

### 2.1 基本設定管理
```python
# 設定CRUD操作
def save_configuration(config: Configuration) -> None
def load_configuration(scope: ConfigurationScope, identifier: str) -> Configuration | None
def delete_configuration(scope: ConfigurationScope, identifier: str) -> bool
def exists_configuration(scope: ConfigurationScope, identifier: str) -> bool

# 階層設定管理
def get_effective_configuration(project_id: str, user_id: str | None = None) -> Configuration
def merge_configurations(configs: list[Configuration]) -> Configuration
```

### 2.2 設定セクション管理
```python
# セクション操作
def add_configuration_section(scope: ConfigurationScope, section: ConfigurationSection) -> None
def remove_configuration_section(scope: ConfigurationScope, section_name: str) -> bool
def update_configuration_section(scope: ConfigurationScope, section: ConfigurationSection) -> None
def get_configuration_section(scope: ConfigurationScope, section_name: str) -> ConfigurationSection | None
```

### 2.3 動的設定管理
```python
# 値操作
def set_configuration_value(scope: ConfigurationScope, key_path: str, value: Any) -> None
def get_configuration_value(scope: ConfigurationScope, key_path: str, default: Any = None) -> Any
def remove_configuration_value(scope: ConfigurationScope, key_path: str) -> bool

# パスベース操作（例: "quality.basic_style.threshold"）
def get_value_by_path(path: str, context: ConfigurationContext) -> Any
def set_value_by_path(path: str, value: Any, context: ConfigurationContext) -> None
```

### 2.4 環境・スコープ管理
```python
# 環境設定
def load_environment_configuration(environment: str) -> Configuration
def switch_environment(environment: str) -> None
def get_current_environment() -> str

# スコープ優先順位設定
def set_scope_priority(priorities: list[ConfigurationScope]) -> None
def get_scope_hierarchy() -> list[ConfigurationScope]
```

### 2.5 設定検証・型安全
```python
# 設定検証
def validate_configuration(config: Configuration) -> ValidationResult
def validate_configuration_value(key: str, value: Any, schema: dict) -> bool

# 型変換
def get_typed_value(key: str, value_type: type, default: Any = None) -> Any
def set_typed_value(key: str, value: Any, expected_type: type) -> None
```

### 2.6 履歴・バージョン管理
```python
# 変更履歴
def get_configuration_history(scope: ConfigurationScope, identifier: str) -> list[ConfigurationChange]
def rollback_configuration(scope: ConfigurationScope, identifier: str, version: str) -> bool

# バージョン管理
def create_configuration_snapshot(scope: ConfigurationScope, identifier: str, description: str) -> str
def list_configuration_snapshots(scope: ConfigurationScope, identifier: str) -> list[ConfigurationSnapshot]
```

## 3. データ構造仕様

### 3.1 ファイル配置
```
設定ベースディレクトリ/
├── system/                              # システム設定
│   ├── app_config.yaml                  # アプリケーション設定
│   ├── quality_standards.yaml          # 品質基準設定
│   └── default_templates.yaml          # デフォルトテンプレート
├── projects/                            # プロジェクト別設定
│   ├── project-001/
│   │   ├── project_config.yaml         # プロジェクト設定
│   │   ├── quality_config.yaml         # 品質設定
│   │   └── writing_preferences.yaml    # 執筆設定
│   └── project-002/
│       └── ...
├── users/                               # ユーザー別設定
│   ├── user-123/
│   │   ├── personal_config.yaml        # 個人設定
│   │   ├── ui_preferences.yaml         # UI設定
│   │   └── shortcuts.yaml              # ショートカット設定
│   └── user-456/
│       └── ...
├── environments/                        # 環境別設定
│   ├── development.yaml
│   ├── staging.yaml
│   └── production.yaml
├── history/                             # 履歴・バックアップ
│   ├── system_20250721_143022.yaml
│   ├── project-001_20250721_143022.yaml
│   └── ...
└── schemas/                             # 設定スキーマ
    ├── system_config_schema.json
    ├── project_config_schema.json
    └── user_config_schema.json
```

### 3.2 システム設定YAML構造
```yaml
# system/app_config.yaml
metadata:
  scope: "SYSTEM"
  identifier: "app_config"
  version: "2.1.0"
  created_at: "2025-07-15T10:30:00"
  updated_at: "2025-07-21T14:30:22"
  description: "システム全体の基本設定"

application:
  name: "小説執筆支援システム"
  version: "2.1.0"
  debug_mode: false
  log_level: "INFO"
  max_concurrent_operations: 10
  timeout_seconds: 30

database:
  type: "yaml_files"
  base_path: "/data/projects"
  backup_enabled: true
  backup_interval: "daily"

quality:
  default_standards:
    basic_style_threshold: 80.0
    composition_threshold: 85.0
    character_consistency_threshold: 75.0
  auto_fix_enabled: true
  severity_levels: ["info", "warning", "error", "critical"]

performance:
  cache_enabled: true
  cache_ttl_seconds: 3600
  max_memory_mb: 512
  gc_threshold: 0.8

notifications:
  enabled: true
  channels: ["console", "file"]
  error_notifications: true
  success_notifications: false
```

### 3.3 プロジェクト設定YAML構造
```yaml
# projects/project-001/project_config.yaml
metadata:
  scope: "PROJECT"
  identifier: "project-001"
  project_name: "転生したら最強の魔法使いだった件"
  version: "1.5.0"
  created_at: "2025-07-15T10:30:00"
  updated_at: "2025-07-21T14:30:22"
  inherits_from: ["SYSTEM"]

project:
  title: "転生したら最強の魔法使いだった件"
  author: "山田太郎"
  genre: ["ファンタジー", "転生"]
  target_audience: "young_adult"
  status: "ongoing"

writing:
  target_word_count_per_episode: 3000
  quality_target: 88.0
  auto_save_enabled: true
  auto_backup_enabled: true

publication:
  platform: "小説家になろう"
  schedule: "weekly"
  publication_day: "sunday"
  auto_publish: false

workflow:
  use_quality_gate: true
  require_review: true
  auto_complete_episodes: false

custom:
  magic_system_complexity: "high"
  character_count_limit: 50
  world_building_depth: "detailed"
```

### 3.4 ユーザー設定YAML構造
```yaml
# users/user-123/personal_config.yaml
metadata:
  scope: "USER"
  identifier: "user-123"
  user_name: "執筆者A"
  version: "1.2.0"
  created_at: "2025-07-15T10:30:00"
  updated_at: "2025-07-21T14:30:22"
  inherits_from: ["SYSTEM", "PROJECT"]

ui_preferences:
  theme: "dark"
  font_family: "Noto Sans JP"
  font_size: 14
  line_height: 1.6
  show_word_count: true
  show_quality_meter: true

editor:
  auto_complete: true
  spell_check: true
  grammar_check: true
  real_time_preview: false

notifications:
  email_enabled: true
  email_address: "writer@example.com"
  desktop_notifications: true
  sound_enabled: false

productivity:
  daily_word_goal: 1000
  writing_streak_tracking: true
  productivity_reports: true
  break_reminders: true

shortcuts:
  save: "Ctrl+S"
  new_episode: "Ctrl+N"
  quality_check: "Ctrl+Q"
  preview: "Ctrl+P"
```

### 3.5 環境設定YAML構造
```yaml
# environments/development.yaml
metadata:
  scope: "ENVIRONMENT"
  identifier: "development"
  version: "1.0.0"
  description: "開発環境設定"

application:
  debug_mode: true
  log_level: "DEBUG"
  detailed_errors: true

database:
  backup_enabled: false
  validate_on_save: true

quality:
  strict_validation: false
  auto_fix_enabled: true

performance:
  cache_enabled: false
  profiling_enabled: true

testing:
  mock_external_services: true
  test_data_enabled: true
  fast_quality_checks: true
```

## 4. 技術仕様

### 4.1 依存関係
```python
# 外部ライブラリ
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum
import jsonschema

# ドメイン層
from domain.entities.configuration import Configuration, ConfigurationSection
from domain.value_objects.configuration_value import ConfigurationValue, ConfigurationScope
from domain.repositories.configuration_repository import ConfigurationRepository
from domain.services.configuration_service import ConfigurationMergeService

# インフラ層
from infrastructure.utils.yaml_utils import YAMLHandler
from infrastructure.validation.configuration_validator import ConfigurationValidator
```

### 4.2 設定スコープ定義
```python
class ConfigurationScope(Enum):
    """設定スコープ（優先順位順）"""
    USER = "USER"           # 最高優先度
    PROJECT = "PROJECT"     # 中間優先度
    ENVIRONMENT = "ENVIRONMENT"  # 中間優先度
    SYSTEM = "SYSTEM"       # 最低優先度

class ConfigurationContext:
    """設定コンテキスト"""
    def __init__(self,
                 project_id: str | None = None,
                 user_id: str | None = None,
                 environment: str = "development"):
        self.project_id = project_id
        self.user_id = user_id
        self.environment = environment
```

### 4.3 エラーハンドリング
```python
# カスタム例外
class ConfigurationRepositoryError(Exception):
    """設定リポジトリエラー"""
    pass

class ConfigurationNotFoundError(ConfigurationRepositoryError):
    """設定未発見エラー"""
    pass

class ConfigurationValidationError(ConfigurationRepositoryError):
    """設定検証エラー"""
    pass

class ConfigurationMergeError(ConfigurationRepositoryError):
    """設定マージエラー"""
    pass

class ConfigurationSchemaError(ConfigurationRepositoryError):
    """設定スキーマエラー"""
    pass
```

### 4.4 設定検証機能
```python
class ConfigurationValidator:
    def validate_configuration(self, config: Configuration, schema: dict) -> ValidationResult:
        """設定の完全検証"""

    def validate_value_type(self, value: Any, expected_type: type) -> bool:
        """値の型検証"""

    def validate_value_range(self, value: Any, min_val: Any, max_val: Any) -> bool:
        """値の範囲検証"""

    def validate_enum_value(self, value: Any, allowed_values: list) -> bool:
        """列挙値検証"""
```

## 5. パフォーマンス要件

### 5.1 応答時間
- 単一設定読み込み: 30ms以内
- 階層設定マージ: 100ms以内
- 設定保存: 50ms以内
- 設定検証: 20ms以内
- 動的リロード: 200ms以内

### 5.2 メモリ使用量
- 単一設定: 1MB以内
- 統合設定キャッシュ: 10MB以内
- 履歴データ: 50MB以内

### 5.3 同時実行性
- 読み込み操作: 完全な並行処理
- 書き込み操作: セクション単位の排他制御
- キャッシュ: スレッドセーフな実装

## 6. 品質保証

### 6.1 データ整合性
```python
def validate_configuration_hierarchy(self) -> list[str]:
    """設定階層の整合性検証"""

def check_circular_inheritance(self) -> bool:
    """循環継承の検出"""

def validate_schema_compliance(self, config: Configuration) -> ValidationResult:
    """スキーマ準拠性検証"""
```

### 6.2 設定マイグレーション
```python
class ConfigurationMigrator:
    def migrate_configuration(self, from_version: str, to_version: str, config_data: dict) -> dict:
        """設定のバージョンマイグレーション"""

    def add_missing_defaults(self, config: Configuration) -> Configuration:
        """不足デフォルト値の補完"""

    def remove_deprecated_settings(self, config: Configuration) -> Configuration:
        """非推奨設定の削除"""
```

### 6.3 エラー回復
```python
def repair_corrupted_configuration(self, scope: ConfigurationScope, identifier: str) -> bool:
    """破損設定の修復"""

def restore_from_backup(self, scope: ConfigurationScope, identifier: str, timestamp: str) -> bool:
    """バックアップからの復元"""

def merge_partial_configurations(self, configs: list[dict]) -> Configuration:
    """部分設定のマージ復元"""
```

## 7. セキュリティ

### 7.1 アクセス制御
```python
class ConfigurationAccessControl:
    def can_read_configuration(self, user: User, scope: ConfigurationScope, identifier: str) -> bool:
        """設定読み取り権限チェック"""

    def can_write_configuration(self, user: User, scope: ConfigurationScope, identifier: str) -> bool:
        """設定書き込み権限チェック"""

    def can_delete_configuration(self, user: User, scope: ConfigurationScope, identifier: str) -> bool:
        """設定削除権限チェック"""
```

### 7.2 機密情報保護
```python
def encrypt_sensitive_values(self, config: Configuration) -> Configuration:
    """機密情報の暗号化"""

def decrypt_sensitive_values(self, config: Configuration) -> Configuration:
    """機密情報の復号化"""

def mask_sensitive_values(self, config: Configuration) -> Configuration:
    """ログ出力用の機密情報マスク"""
```

## 8. 拡張性・統合性

### 8.1 プラグイン機能
```python
class ConfigurationPlugin:
    @abstractmethod
    def on_configuration_loaded(self, config: Configuration) -> Configuration:
        """設定読み込み後処理"""

    @abstractmethod
    def on_configuration_saved(self, config: Configuration) -> None:
        """設定保存後処理"""

    @abstractmethod
    def validate_custom_settings(self, config: Configuration) -> ValidationResult:
        """カスタム設定検証"""
```

### 8.2 外部システム連携
```python
def export_to_json(self, scope: ConfigurationScope, identifier: str) -> dict:
    """JSON形式エクスポート"""

def import_from_json(self, scope: ConfigurationScope, identifier: str, json_data: dict) -> None:
    """JSON形式インポート"""

def sync_with_external_config(self, external_source: str) -> None:
    """外部設定システムとの同期"""
```

## 9. 使用例

### 9.1 基本的な使用パターン
```python
# リポジトリ初期化
config_repo = YamlConfigurationRepository(base_path=Path("/config"))

# システム設定作成
system_config = Configuration(
    scope=ConfigurationScope.SYSTEM,
    identifier="app_config",
    sections={
        "application": ConfigurationSection("application", {
            "name": ConfigurationValue("小説執筆支援システム"),
            "version": ConfigurationValue("2.1.0"),
            "debug_mode": ConfigurationValue(False)
        })
    }
)
config_repo.save_configuration(system_config)

# プロジェクト設定作成
project_config = Configuration(
    scope=ConfigurationScope.PROJECT,
    identifier="project-001",
    inherits_from=[ConfigurationScope.SYSTEM]
)
project_config.add_section("writing", {
    "target_word_count": ConfigurationValue(3000),
    "quality_target": ConfigurationValue(88.0)
})
config_repo.save_configuration(project_config)
```

### 9.2 階層設定の利用例
```python
# コンテキスト設定
context = ConfigurationContext(
    project_id="project-001",
    user_id="user-123",
    environment="development"
)

# 効果的な設定を取得（USER > PROJECT > SYSTEM の順で優先）
effective_config = config_repo.get_effective_configuration(
    context.project_id,
    context.user_id
)

# 設定値の取得
quality_target = effective_config.get_value("writing.quality_target", 85.0)
debug_mode = effective_config.get_value("application.debug_mode", False)
```

### 9.3 動的設定変更例
```python
# パスベース設定変更
config_repo.set_value_by_path(
    "quality.basic_style_threshold",
    85.0,
    context
)

# セクション追加
new_section = ConfigurationSection("analysis", {
    "enabled": ConfigurationValue(True),
    "batch_size": ConfigurationValue(100)
})
config_repo.add_configuration_section(
    ConfigurationScope.PROJECT,
    new_section
)

# 設定リロード
config_repo.reload_configuration(ConfigurationScope.PROJECT, "project-001")
```

### 9.4 設定検証・履歴管理例
```python
# 設定検証
validation_result = config_repo.validate_configuration(project_config)
if not validation_result.is_valid:
    print(f"検証エラー: {validation_result.errors}")

# 設定スナップショット作成
snapshot_id = config_repo.create_configuration_snapshot(
    ConfigurationScope.PROJECT,
    "project-001",
    "品質設定の大幅変更前"
)

# 履歴確認
history = config_repo.get_configuration_history(
    ConfigurationScope.PROJECT,
    "project-001"
)
for change in history[-5:]:
    print(f"{change.timestamp}: {change.description}")

# ロールバック実行
config_repo.rollback_configuration(
    ConfigurationScope.PROJECT,
    "project-001",
    snapshot_id
)
```

## 10. テスト仕様

### 10.1 単体テスト
```python
class TestYamlConfigurationRepository:
    def test_save_and_load_configuration(self):
        """設定保存・読み込みテスト"""

    def test_configuration_inheritance(self):
        """設定継承テスト"""

    def test_configuration_merging(self):
        """設定マージテスト"""

    def test_configuration_validation(self):
        """設定検証テスト"""

    def test_dynamic_configuration_updates(self):
        """動的設定更新テスト"""

    def test_configuration_history(self):
        """設定履歴管理テスト"""

    def test_scope_priority_handling(self):
        """スコープ優先度処理テスト"""

class TestConfigurationValidator:
    def test_schema_validation(self):
        """スキーマ検証テスト"""

    def test_type_validation(self):
        """型検証テスト"""

    def test_range_validation(self):
        """範囲検証テスト"""
```

### 10.2 統合テスト
```python
class TestConfigurationIntegration:
    def test_multi_level_configuration_workflow(self):
        """多層設定ワークフローテスト"""

    def test_concurrent_configuration_access(self):
        """並行設定アクセステスト"""

    def test_configuration_migration(self):
        """設定マイグレーションテスト"""

    def test_environment_switching(self):
        """環境切り替えテスト"""
```

### 10.3 パフォーマンステスト
```python
def test_large_configuration_performance(self):
    """大規模設定のパフォーマンステスト"""

def test_cache_effectiveness(self):
    """キャッシュ効果テスト"""

def test_memory_usage_under_load(self):
    """負荷時メモリ使用量テスト"""
```

## 11. 監視・運用

### 11.1 メトリクス収集
```python
# 設定リポジトリメトリクス
metrics = {
    'configuration_operations': {
        'reads_per_minute': 45,
        'writes_per_minute': 12,
        'cache_hit_rate': 0.89,
        'validation_errors_per_hour': 3
    },
    'storage_metrics': {
        'total_configurations': 156,
        'total_storage_mb': 23.4,
        'history_records': 892,
        'snapshots_count': 45
    },
    'performance_metrics': {
        'average_read_time_ms': 25,
        'average_write_time_ms': 48,
        'merge_time_ms': 87,
        'validation_time_ms': 15
    }
}
```

### 11.2 ログ戦略
```python
# 設定操作ログ
logger.info(f"Configuration loaded: scope={scope}, id={identifier}")
logger.warning(f"Configuration validation failed: {validation_errors}")
logger.error(f"Configuration save failed: {error_message}")

# セキュリティログ
security_logger.info(f"Configuration access: user={user_id}, scope={scope}")
security_logger.warning(f"Unauthorized configuration access attempt: user={user_id}")
```

### 11.3 アラート条件
- 設定検証エラー率 > 5%
- 設定ファイル破損検出
- 設定読み込み時間 > 100ms
- ディスク使用量 > 100MB
- 不正アクセス試行検出

## 12. 実装メモ

### 12.1 実装ファイル
- **メインクラス**: `src/noveler/infrastructure/repositories/yaml_configuration_repository.py`
- **設定エンティティ**: `src/noveler/domain/entities/novel_configuration.py`
- **バリデーター**: （参考）旧構成の記述。現行は `src/noveler/infrastructure/config/config_manager.py` 等に統合。
- **テストファイル**: `tests/unit/infrastructure/repositories/test_yaml_configuration_repository.py`

### 12.2 設計方針
- **階層設定アーキテクチャ**: 継承・オーバーライド機能による柔軟な設定管理
- **型安全設定**: 設定値の型検証と自動変換
- **設定の不変性**: Value Object による設定変更の安全性保証
- **プラグイン対応**: 拡張可能な設定処理機能

### 12.3 今後の改善点
- [ ] 分散設定管理（Redis、etcd）対応
- [ ] 設定変更のリアルタイム通知
- [ ] Web UIによる設定管理機能
- [ ] 設定テンプレート機能
- [ ] A/Bテスト用設定機能
- [ ] 設定パフォーマンス最適化
- [ ] GraphQL設定API
- [ ] 設定ドキュメント自動生成
