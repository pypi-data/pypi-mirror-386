# SPEC-CONFIG-002: コンフィグローダーアダプター仕様書

## 要件トレーサビリティ

**要件ID**: REQ-CONFIG-004, REQ-CONFIG-005, REQ-CONFIG-006 (動的設定管理)

**主要要件**:
- REQ-CONFIG-004: project_config.yaml設計
- REQ-CONFIG-005: 動的設定変更システム
- REQ-CONFIG-006: 設定値検証システム

**実装状況**: ✅実装済み
**テストカバレッジ**: tests/unit/test_config_loader_adapter.py
**関連仕様書**: SPEC-CONFIG-001_configuration_repository.md

## 概要
コンフィグローダーアダプターは、外部設定システム（YAML、JSON、環境変数等）とドメイン設定オブジェクトを接続するアダプターです。異なる設定ソースからの統一的な設定読み込みと、ドメインオブジェクトへの変換を担当します。

## クラス設計

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class ConfigSourceType(Enum):
    """設定ソースタイプ"""
    YAML = "yaml"
    JSON = "json"
    ENV = "env"
    INI = "ini"
    TOML = "toml"

@dataclass
class ConfigSource:
    """設定ソース"""
    source_type: ConfigSourceType
    location: Union[Path, str]
    priority: int = 0
    required: bool = True

T = TypeVar('T')

class IConfigLoader(ABC, Generic[T]):
    """設定ローダーインターフェース"""

    @abstractmethod
    def load(self, source: ConfigSource) -> Dict[str, Any]:
        """設定を読み込み"""
        pass

    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> bool:
        """設定の妥当性を検証"""
        pass

    @abstractmethod
    def convert_to_domain_object(self, config: Dict[str, Any]) -> T:
        """ドメインオブジェクトに変換"""
        pass

@dataclass
class LoaderContext:
    """ローダーコンテキスト"""
    sources: List[ConfigSource]
    merge_strategy: str = "override"
    validation_mode: str = "strict"
    default_values: Optional[Dict[str, Any]] = None

class ConfigLoaderAdapter(Generic[T]):
    """設定ローダーアダプター"""

    def __init__(
        self,
        loaders: Dict[ConfigSourceType, IConfigLoader[T]],
        merger: IConfigMerger,
        validator: IConfigValidator,
        converter: IConfigConverter[T]
    ):
        self._loaders = loaders
        self._merger = merger
        self._validator = validator
        self._converter = converter
```

## データ構造

### インターフェース定義

```python
class IConfigMerger(ABC):
    """設定マージャーインターフェース"""

    @abstractmethod
    def merge(
        self,
        configs: List[Dict[str, Any]],
        strategy: str = "override"
    ) -> Dict[str, Any]:
        """複数の設定をマージ"""
        pass

class IConfigValidator(ABC):
    """設定バリデーターインターフェース"""

    @abstractmethod
    def validate(
        self,
        config: Dict[str, Any],
        schema: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """設定を検証"""
        pass

class IConfigConverter(ABC, Generic[T]):
    """設定コンバーターインターフェース"""

    @abstractmethod
    def convert(self, config: Dict[str, Any]) -> T:
        """ドメインオブジェクトに変換"""
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """スキーマを取得"""
        pass

@dataclass
class ValidationResult:
    """検証結果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

@dataclass
class LoadResult(Generic[T]):
    """読み込み結果"""
    success: bool
    config_object: Optional[T]
    raw_config: Dict[str, Any]
    validation_result: ValidationResult
    sources_used: List[ConfigSource]
```

### アダプター実装

```python
class YamlConfigLoader(IConfigLoader[T]):
    """YAMLコンフィグローダー"""

    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        self._schema = schema

    def load(self, source: ConfigSource) -> Dict[str, Any]:
        import yaml

        try:
            with open(source.location, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            if source.required:
                raise ConfigLoadError(f"Required config file not found: {source.location}")
            return {}
        except yaml.YAMLError as e:
            raise ConfigParseError(f"YAML parse error in {source.location}: {e}")

class EnvConfigLoader(IConfigLoader[T]):
    """環境変数コンフィグローダー"""

    def __init__(self, prefix: str = "", mapping: Optional[Dict[str, str]] = None):
        self._prefix = prefix
        self._mapping = mapping or {}

    def load(self, source: ConfigSource) -> Dict[str, Any]:
        import os

        config = {}
        prefix = f"{self._prefix}_" if self._prefix else ""

        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                if config_key in self._mapping:
                    config_key = self._mapping[config_key]
                config[config_key] = self._parse_env_value(value)

        return config

    def _parse_env_value(self, value: str) -> Any:
        """環境変数値を適切な型に変換"""
        if value.lower() in ('true', 'yes', '1'):
            return True
        elif value.lower() in ('false', 'no', '0'):
            return False
        elif value.isdigit():
            return int(value)
        elif '.' in value and value.replace('.', '').isdigit():
            return float(value)
        else:
            return value

class JsonConfigLoader(IConfigLoader[T]):
    """JSONコンフィグローダー"""

    def load(self, source: ConfigSource) -> Dict[str, Any]:
        import json

        try:
            with open(source.location, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            if source.required:
                raise ConfigLoadError(f"Required config file not found: {source.location}")
            return {}
        except json.JSONDecodeError as e:
            raise ConfigParseError(f"JSON parse error in {source.location}: {e}")
```

## パブリックメソッド

### ConfigLoaderAdapter

```python
def load_config(self, context: LoaderContext) -> LoadResult[T]:
    """
    設定を読み込み、ドメインオブジェクトに変換

    Args:
        context: ローダーコンテキスト

    Returns:
        LoadResult[T]: 読み込み結果
    """
    try:
        # 各ソースから設定を読み込み
        configs = []
        used_sources = []

        for source in sorted(context.sources, key=lambda s: s.priority):
            if source.source_type not in self._loaders:
                continue

            loader = self._loaders[source.source_type]
            config = loader.load(source)

            if config:  # 空でない設定のみ使用
                configs.append(config)
                used_sources.append(source)

        # デフォルト値を最初に追加
        if context.default_values:
            configs.insert(0, context.default_values)

        # 設定をマージ
        merged_config = self._merger.merge(configs, context.merge_strategy)

        # 検証
        schema = self._converter.get_schema()
        validation_result = self._validator.validate(merged_config, schema)

        if not validation_result.is_valid and context.validation_mode == "strict":
            return LoadResult(
                success=False,
                config_object=None,
                raw_config=merged_config,
                validation_result=validation_result,
                sources_used=used_sources
            )

        # ドメインオブジェクトに変換
        config_object = self._converter.convert(merged_config)

        return LoadResult(
            success=True,
            config_object=config_object,
            raw_config=merged_config,
            validation_result=validation_result,
            sources_used=used_sources
        )

    except Exception as e:
        return LoadResult(
            success=False,
            config_object=None,
            raw_config={},
            validation_result=ValidationResult(
                is_valid=False,
                errors=[str(e)],
                warnings=[]
            ),
            sources_used=[]
        )

def register_loader(
    self,
    source_type: ConfigSourceType,
    loader: IConfigLoader[T]
) -> None:
    """
    設定ローダーを登録

    Args:
        source_type: ソースタイプ
        loader: ローダー実装
    """
    self._loaders[source_type] = loader

def create_context(
    self,
    sources: List[Union[ConfigSource, str, Path]],
    **kwargs
) -> LoaderContext:
    """
    ローダーコンテキストを生成

    Args:
        sources: 設定ソースのリスト
        **kwargs: その他のオプション

    Returns:
        LoaderContext: 生成されたコンテキスト
    """
    normalized_sources = []

    for i, source in enumerate(sources):
        if isinstance(source, ConfigSource):
            normalized_sources.append(source)
        else:
            path = Path(source)
            source_type = self._detect_source_type(path)
            normalized_sources.append(ConfigSource(
                source_type=source_type,
                location=path,
                priority=i
            ))

    return LoaderContext(
        sources=normalized_sources,
        merge_strategy=kwargs.get("merge_strategy", "override"),
        validation_mode=kwargs.get("validation_mode", "strict"),
        default_values=kwargs.get("default_values")
    )
```

## プライベートメソッド

```python
def _detect_source_type(self, path: Path) -> ConfigSourceType:
    """ファイル拡張子からソースタイプを検出"""
    suffix = path.suffix.lower()

    if suffix in ['.yaml', '.yml']:
        return ConfigSourceType.YAML
    elif suffix == '.json':
        return ConfigSourceType.JSON
    elif suffix == '.ini':
        return ConfigSourceType.INI
    elif suffix == '.toml':
        return ConfigSourceType.TOML
    else:
        raise ConfigError(f"Unsupported config file type: {suffix}")

def _apply_defaults(
    self,
    config: Dict[str, Any],
    defaults: Dict[str, Any]
) -> Dict[str, Any]:
    """デフォルト値を適用"""
    result = defaults.copy()
    result.update(config)
    return result

def _normalize_config_keys(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """設定キーを正規化"""
    normalized = {}

    for key, value in config.items():
        normalized_key = key.lower().replace('-', '_')
        if isinstance(value, dict):
            normalized[normalized_key] = self._normalize_config_keys(value)
        else:
            normalized[normalized_key] = value

    return normalized
```

## アダプターパターン実装

### ドメイン設定オブジェクト変換

```python
class ProjectConfigConverter(IConfigConverter[ProjectConfig]):
    """プロジェクト設定コンバーター"""

    def convert(self, config: Dict[str, Any]) -> ProjectConfig:
        """設定辞書をProjectConfigに変換"""
        try:
            return ProjectConfig(
                name=config["name"],
                author=config["author"],
                description=config.get("description", ""),
                genre=Genre(config.get("genre", "unknown")),
                target_audience=TargetAudience(config.get("target_audience", "general")),
                writing_style=WritingStyle.from_dict(config.get("writing_style", {})),
                quality_settings=QualitySettings.from_dict(config.get("quality", {})),
                publication_settings=PublicationSettings.from_dict(config.get("publication", {}))
            )
        except KeyError as e:
            raise ConfigConversionError(f"Required config key missing: {e}")
        except ValueError as e:
            raise ConfigConversionError(f"Invalid config value: {e}")

    def get_schema(self) -> Dict[str, Any]:
        """設定スキーマを返す"""
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "author": {"type": "string", "minLength": 1},
                "description": {"type": "string"},
                "genre": {
                    "type": "string",
                    "enum": ["fantasy", "romance", "mystery", "sci-fi", "unknown"]
                },
                "target_audience": {
                    "type": "string",
                    "enum": ["children", "young_adult", "adult", "general"]
                },
                "writing_style": {"type": "object"},
                "quality": {"type": "object"},
                "publication": {"type": "object"}
            },
            "required": ["name", "author"]
        }

class QualityConfigConverter(IConfigConverter[QualityConfig]):
    """品質設定コンバーター"""

    def convert(self, config: Dict[str, Any]) -> QualityConfig:
        return QualityConfig(
            enabled_checks=config.get("enabled_checks", []),
            min_word_count=config.get("min_word_count", 800),
            max_word_count=config.get("max_word_count", 8000),
            target_reading_time=config.get("target_reading_time", 5),
            quality_threshold=config.get("quality_threshold", 70.0),
            auto_fix=config.get("auto_fix", False),
            strict_mode=config.get("strict_mode", True)
        )
```

### 設定マージ戦略

```python
class ConfigMerger(IConfigMerger):
    """設定マージャー"""

    STRATEGIES = {
        "override": "_merge_override",
        "deep_merge": "_merge_deep",
        "append": "_merge_append",
        "priority": "_merge_priority"
    }

    def merge(
        self,
        configs: List[Dict[str, Any]],
        strategy: str = "override"
    ) -> Dict[str, Any]:
        if not configs:
            return {}
        if len(configs) == 1:
            return configs[0]

        merge_func = getattr(self, self.STRATEGIES.get(strategy, "_merge_override"))

        result = configs[0].copy()
        for config in configs[1:]:
            result = merge_func(result, config)

        return result

    def _merge_override(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """後勝ちでマージ"""
        result = base.copy()
        result.update(override)
        return result

    def _merge_deep(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深いマージ（ネストした辞書も統合）"""
        result = base.copy()

        for key, value in override.items():
            if (key in result and
                isinstance(result[key], dict) and
                isinstance(value, dict)):
                result[key] = self._merge_deep(result[key], value)
            else:
                result[key] = value

        return result
```

## 依存関係

```python
from domain.entities import ProjectConfig, QualityConfig
from domain.value_objects import Genre, TargetAudience, WritingStyle
from domain.services import IValidationService
from infrastructure.validation import JsonSchemaValidator
```

## 設計原則遵守

### アダプターパターン
- **外部システム分離**: 各設定形式は独立したローダーで処理
- **統一インターフェース**: IConfigLoaderで統一的なアクセス
- **拡張性**: 新しい設定形式の追加が容易

### 依存性逆転原則
- **抽象化への依存**: 実装ではなくインターフェースに依存
- **注入可能な依存**: 全ての依存関係は外部から注入
- **テスタビリティ**: モック化が容易

## 使用例

### 基本的な使用

```python
# アダプター設定
loaders = {
    ConfigSourceType.YAML: YamlConfigLoader(),
    ConfigSourceType.JSON: JsonConfigLoader(),
    ConfigSourceType.ENV: EnvConfigLoader(prefix="NOVEL")
}

merger = ConfigMerger()
validator = JsonSchemaValidator()
converter = ProjectConfigConverter()

config_adapter = ConfigLoaderAdapter(loaders, merger, validator, converter)

# 設定読み込み
context = config_adapter.create_context([
    "config/default.yaml",
    "config/local.yaml",
    ConfigSource(ConfigSourceType.ENV, "", priority=2, required=False)
])

result = config_adapter.load_config(context)

if result.success:
    project_config = result.config_object
    print(f"プロジェクト: {project_config.name}")
else:
    print("設定読み込み失敗:")
    for error in result.validation_result.errors:
        print(f"  - {error}")
```

### カスタム変換の実装

```python
class CustomConfigConverter(IConfigConverter[CustomConfig]):
    """カスタム設定コンバーター"""

    def convert(self, config: Dict[str, Any]) -> CustomConfig:
        # カスタム変換ロジック
        return CustomConfig(
            custom_field=config.get("custom_field", "default"),
            advanced_settings=self._convert_advanced_settings(config.get("advanced", {}))
        )

    def _convert_advanced_settings(self, settings: Dict[str, Any]) -> AdvancedSettings:
        return AdvancedSettings(
            feature_flags=settings.get("features", []),
            optimization_level=settings.get("optimization", 1)
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "custom_field": {"type": "string"},
                "advanced": {
                    "type": "object",
                    "properties": {
                        "features": {"type": "array", "items": {"type": "string"}},
                        "optimization": {"type": "integer", "minimum": 1, "maximum": 3}
                    }
                }
            }
        }
```

## エラーハンドリング

```python
class ConfigError(Exception):
    """設定関連のベースエラー"""
    pass

class ConfigLoadError(ConfigError):
    """設定読み込みエラー"""
    pass

class ConfigParseError(ConfigError):
    """設定解析エラー"""
    pass

class ConfigConversionError(ConfigError):
    """設定変換エラー"""
    pass

class ConfigValidationError(ConfigError):
    """設定検証エラー"""

    def __init__(self, message: str, errors: List[str]):
        super().__init__(message)
        self.errors = errors

def handle_config_error(error: ConfigError, context: LoaderContext) -> LoadResult:
    """設定エラーを適切にハンドリング"""
    if isinstance(error, ConfigValidationError):
        return LoadResult(
            success=False,
            config_object=None,
            raw_config={},
            validation_result=ValidationResult(
                is_valid=False,
                errors=error.errors,
                warnings=[]
            ),
            sources_used=[]
        )
    else:
        return LoadResult(
            success=False,
            config_object=None,
            raw_config={},
            validation_result=ValidationResult(
                is_valid=False,
                errors=[str(error)],
                warnings=[]
            ),
            sources_used=[]
        )
```

## テスト観点

### ユニットテスト
- 各ローダーの動作確認
- マージ戦略の検証
- 変換ロジックの正確性
- バリデーション結果

### 統合テスト
- 複数ソースからの読み込み
- 設定階層の適用
- エラーハンドリング
- パフォーマンス

### エッジケーステスト
- 空ファイル処理
- 不正な形式のファイル
- 循環参照の検出
- 巨大設定ファイル

## 品質基準

### コード品質
- 循環的複雑度: 8以下
- テストカバレッジ: 95%以上
- 型安全性: 100%

### パフォーマンス
- 設定読み込み: 100ms以下
- メモリ使用量: 最小化
- キャッシュ効率: 最適化

### 信頼性
- エラー復旧機能
- 部分的な設定読み込み
- Graceful degradation
