# SPEC-CONFIGURATION-001: 統一設定管理システム

## 概要

小説執筆支援システムにおけるハードコーディングされた設定値の散在問題を解決し、統一された設定管理システムを構築する。

## 仕様ID
- **ID**: SPEC-CONFIGURATION-001
- **ドメイン**: CONFIGURATION (設定管理)
- **作成日**: 2025-01-26
- **ステータス**: 設計中

## 問題分析

### 現在の問題
1. **設定値の散在**: 品質閾値、カバレッジ閾値、タイムアウト値等が複数ファイルにハードコード
2. **重複設定**: 同じ概念の設定値が異なる値で複数箇所に存在
3. **環境依存**: 開発・テスト・本番環境の設定が混在
4. **保守困難**: 設定変更時に複数ファイルを修正する必要

### 特定された散在設定
- `quality_threshold`: 70.0, 80.0, 60.0（複数の値が散在）
- `coverage_threshold`: 60.0（テスト実行コマンド）
- `complexity_threshold`: 10（複雑度チェック）
- `marathon_session_threshold`: 4.0（執筆時間）
- ポート番号、ファイルパス等

## ドメインモデリング（DDD設計）

### エンティティ

#### ConfigurationProfile
```python
class ConfigurationProfile:
    """設定プロファイルエンティティ"""

    def __init__(self,
                 profile_id: ProfileId,
                 name: str,
                 environment: Environment,
                 settings: dict[str, Any],
                 created_at: datetime,
                 is_active: bool = False):
        self.profile_id = profile_id
        self.name = name
        self.environment = environment
        self.settings = settings
        self.created_at = created_at
        self.is_active = is_active

    def update_setting(self, key: SettingKey, value: SettingValue) -> None:
        """設定値を更新"""

    def activate(self) -> None:
        """プロファイルをアクティブ化"""

    def validate_settings(self) -> ValidationResult:
        """設定値を検証"""
```

### 値オブジェクト

#### SettingKey
```python
class SettingKey:
    """設定キー値オブジェクト"""
    def __init__(self, key: str, category: SettingCategory):
        self.key = key
        self.category = category
        self._validate()
```

#### SettingValue
```python
class SettingValue:
    """設定値オブジェクト"""
    def __init__(self, value: Any, value_type: SettingValueType, constraints: dict[str, Any] | None = None):
        self.value = value
        self.value_type = value_type
        self.constraints = constraints
        self._validate()
```

#### Environment
```python
class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
```

#### SettingCategory
```python
class SettingCategory(Enum):
    QUALITY = "quality"
    PERFORMANCE = "performance"
    INFRASTRUCTURE = "infrastructure"
    FEATURE = "feature"
    SECURITY = "security"
```

### ドメインサービス

#### ConfigurationValidationService
```python
class ConfigurationValidationService:
    """設定検証ドメインサービス"""

    def validate_profile(self, profile: ConfigurationProfile) -> ValidationResult:
        """プロファイル全体の整合性を検証"""

    def validate_setting_constraints(self, setting_key: SettingKey, setting_value: SettingValue) -> bool:
        """設定値の制約を検証"""
```

#### ConfigurationMigrationService
```python
class ConfigurationMigrationService:
    """設定移行ドメインサービス"""

    def migrate_legacy_settings(self, legacy_settings: dict[str, Any]) -> ConfigurationProfile:
        """レガシー設定を新形式に移行"""
```

### リポジトリインターフェース

#### ConfigurationRepository
```python
class ConfigurationRepository(ABC):
    """設定リポジトリインターフェース"""

    @abstractmethod
    def find_active_profile(self) -> ConfigurationProfile | None:
        """アクティブなプロファイルを取得"""

    @abstractmethod
    def find_by_environment(self, environment: Environment) -> list[ConfigurationProfile]:
        """環境別プロファイルを取得"""

    @abstractmethod
    def save(self, profile: ConfigurationProfile) -> None:
        """プロファイルを保存"""

    @abstractmethod
    def find_by_id(self, profile_id: ProfileId) -> ConfigurationProfile | None:
        """IDでプロファイルを取得"""
```

## アプリケーション層設計

### ユースケース

#### LoadConfigurationUseCase
```python
class LoadConfigurationUseCase:
    """設定読み込みユースケース"""

    def execute(self, request: LoadConfigurationRequest) -> LoadConfigurationResponse:
        """指定環境の設定を読み込み"""
```

#### UpdateConfigurationUseCase
```python
class UpdateConfigurationUseCase:
    """設定更新ユースケース"""

    def execute(self, request: UpdateConfigurationRequest) -> UpdateConfigurationResponse:
        """設定値を更新"""
```

#### MigrateConfigurationUseCase
```python
class MigrateConfigurationUseCase:
    """設定移行ユースケース"""

    def execute(self, request: MigrateConfigurationRequest) -> MigrateConfigurationResponse:
        """レガシー設定を新形式に移行"""
```

## インフラストラクチャ層設計

### 実装方針
- **YAML設定ファイル**: `settings.yaml`, `settings.development.yaml` 等
- **環境変数サポート**: 環境変数での設定値オーバーライド
- **キャッシュ機能**: 頻繁にアクセスされる設定のメモリキャッシュ
- **ホットリロード**: ファイル変更の自動検知と再読み込み

### YamlConfigurationRepository
```python
class YamlConfigurationRepository(ConfigurationRepository):
    """YAML設定リポジトリ実装"""

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.cache: dict[str, ConfigurationProfile] = {}
```

## 標準設定構造

### settings.yaml
```yaml
# 共通設定
common:
  quality:
    threshold: 70.0
    coverage_threshold: 60.0
    complexity_threshold: 10

  performance:
    marathon_session_threshold_hours: 4.0
    test_timeout_seconds: 30

  infrastructure:
    backup_retention_days: 30
    log_level: "INFO"

# 環境別設定
environments:
  development:
    quality:
      threshold: 60.0  # 開発時は緩い設定
    infrastructure:
      log_level: "DEBUG"

  testing:
    performance:
      test_timeout_seconds: 60  # テスト時は長めのタイムアウト

  production:
    quality:
      threshold: 80.0  # 本番は厳しい設定
    infrastructure:
      log_level: "WARNING"
```

## 実装ステップ

### Phase 1: ドメイン層（TDD RED）
1. **失敗するテスト作成**
   - `test_configuration_profile.py`
   - `test_setting_value_objects.py`
   - `test_configuration_services.py`

### Phase 2: 最小実装（TDD GREEN）
2. **ドメインエンティティ実装**
   - `ConfigurationProfile`
   - `SettingKey`, `SettingValue`
   - バリデーションロジック

### Phase 3: アプリケーション層（TDD GREEN）
3. **ユースケース実装**
   - `LoadConfigurationUseCase`
   - `UpdateConfigurationUseCase`

### Phase 4: インフラ層（TDD GREEN）
4. **リポジトリ実装**
   - `YamlConfigurationRepository`
   - 設定ファイル読み書き

### Phase 5: 移行（TDD REFACTOR）
5. **レガシー設定移行**
   - 既存コードからハードコード除去
   - 統一設定システムに置き換え

## テストケース

### ドメイン層テスト
- ✅ ConfigurationProfileの作成・更新・検証
- ✅ SettingValue制約チェック
- ✅ 環境別設定の整合性検証
- ✅ 設定値型安全性チェック

### 統合テスト
- ✅ YAML設定ファイル読み込み
- ✅ 環境変数オーバーライド
- ✅ 設定変更の永続化
- ✅ 複数環境間の設定切り替え

### E2Eテスト
- ✅ CLI経由での設定変更
- ✅ 設定変更の即座反映
- ✅ 無効設定値の適切なエラー表示

## 成功基準

1. **ハードコード削除**: 既存の散在設定値を95%以上削除
2. **一元管理**: 全設定値を統一形式で管理
3. **型安全性**: 設定値の型チェックを100%実装
4. **環境対応**: 開発・テスト・本番環境の適切な設定分離
5. **パフォーマンス**: 設定読み込み時間10ms以下

## リスク・制約

### リスク
- **破壊的変更**: 既存コードの大幅修正が必要
- **移行コスト**: レガシー設定の変換作業
- **パフォーマンス**: 設定読み込みのオーバーヘッド

### 制約
- **後方互換性**: 段階的移行で既存機能を維持
- **設定ファイル形式**: YAML形式に統一
- **環境変数**: `NOVEL_`プレフィックスで統一

## 関連仕様

- 既存の品質チェックシステム
- テスト実行システム
- CLI設定システム

## 更新履歴

- 2025-01-26: 初版作成（SDD準拠）
