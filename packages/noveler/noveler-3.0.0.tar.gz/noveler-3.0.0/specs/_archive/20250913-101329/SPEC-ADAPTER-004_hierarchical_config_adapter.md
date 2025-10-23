# 階層設定アダプター仕様書

## 概要
階層設定アダプターは、複数のレベルの設定ファイル（グローバル、プロジェクト、ローカル等）を階層的に管理し、優先度に基づく設定値の解決を提供するアダプターです。設定の継承、オーバーライド、動的更新機能を担当します。

## クラス設計

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from pathlib import Path
import copy

class ConfigLevel(IntEnum):
    """設定レベル（数値が高いほど優先度高）"""
    SYSTEM = 10      # システム全体設定
    GLOBAL = 20      # ユーザーグローバル設定
    PROJECT = 30     # プロジェクト設定
    LOCAL = 40       # ローカル設定
    RUNTIME = 50     # ランタイム設定
    OVERRIDE = 60    # 一時オーバーライド

class ConfigScope(Enum):
    """設定スコープ"""
    SYSTEM_WIDE = "system_wide"
    USER = "user"
    PROJECT = "project"
    DIRECTORY = "directory"
    TEMPORARY = "temporary"

@dataclass
class ConfigSource:
    """設定ソース"""
    level: ConfigLevel
    scope: ConfigScope
    path: Optional[Path] = None
    name: str = ""
    readonly: bool = False
    dynamic: bool = False
    priority: int = 0

@dataclass
class ConfigValue:
    """設定値"""
    value: Any
    source: ConfigSource
    key_path: str
    inherited: bool = False
    overridden: bool = False

T = TypeVar('T')

class IConfigResolver(ABC, Generic[T]):
    """設定解決インターフェース"""

    @abstractmethod
    def resolve(self, key_path: str, config_type: type = None) -> Optional[ConfigValue]:
        """設定値を解決"""
        pass

    @abstractmethod
    def resolve_all(self, key_path: str) -> List[ConfigValue]:
        """全レベルの設定値を取得"""
        pass

    @abstractmethod
    def has_config(self, key_path: str, level: Optional[ConfigLevel] = None) -> bool:
        """設定の存在確認"""
        pass

class IConfigHierarchy(ABC):
    """設定階層インターフェース"""

    @abstractmethod
    def add_source(self, source: ConfigSource, config: Dict[str, Any]) -> None:
        """設定ソースを追加"""
        pass

    @abstractmethod
    def remove_source(self, source: ConfigSource) -> None:
        """設定ソースを削除"""
        pass

    @abstractmethod
    def get_effective_config(self) -> Dict[str, Any]:
        """有効な設定を取得"""
        pass

    @abstractmethod
    def reload_source(self, source: ConfigSource) -> bool:
        """設定ソースを再読み込み"""
        pass

@dataclass
class ConfigChangeEvent:
    """設定変更イベント"""
    key_path: str
    old_value: Any
    new_value: Any
    source: ConfigSource
    change_type: str  # add, modify, delete

class HierarchicalConfigAdapter(IConfigResolver, IConfigHierarchy):
    """階層設定アダプター"""

    def __init__(
        self,
        loader_adapter: IConfigLoaderAdapter,
        merger: IConfigMerger,
        validator: IConfigValidator,
        change_notifier: Optional[IConfigChangeNotifier] = None
    ):
        self._loader = loader_adapter
        self._merger = merger
        self._validator = validator
        self._notifier = change_notifier
        self._sources: Dict[ConfigSource, Dict[str, Any]] = {}
        self._cache: Dict[str, ConfigValue] = {}
        self._watchers: List[Callable[[ConfigChangeEvent], None]] = []
```

## データ構造

### インターフェース定義

```python
class IConfigLoaderAdapter(ABC):
    """設定ローダーアダプターインターフェース"""

    @abstractmethod
    def load_from_source(self, source: ConfigSource) -> Optional[Dict[str, Any]]:
        """ソースから設定を読み込み"""
        pass

    @abstractmethod
    def save_to_source(self, source: ConfigSource, config: Dict[str, Any]) -> bool:
        """ソースに設定を保存"""
        pass

class IConfigMerger(ABC):
    """設定マージャーインターフェース"""

    @abstractmethod
    def merge_hierarchical(
        self,
        configs: List[tuple[ConfigSource, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """階層設定をマージ"""
        pass

    @abstractmethod
    def resolve_inheritance(
        self,
        key_path: str,
        configs: List[tuple[ConfigSource, Dict[str, Any]]]
    ) -> Optional[ConfigValue]:
        """継承を解決"""
        pass

class IConfigValidator(ABC):
    """設定バリデーターインターフェース"""

    @abstractmethod
    def validate_hierarchy(self, config: Dict[str, Any]) -> ValidationResult:
        """階層設定の妥当性を検証"""
        pass

    @abstractmethod
    def validate_level_constraints(
        self,
        source: ConfigSource,
        config: Dict[str, Any]
    ) -> ValidationResult:
        """レベル制約を検証"""
        pass

class IConfigChangeNotifier(ABC):
    """設定変更通知インターフェース"""

    @abstractmethod
    def notify_change(self, event: ConfigChangeEvent) -> None:
        """変更を通知"""
        pass

    @abstractmethod
    def add_watcher(self, watcher: Callable[[ConfigChangeEvent], None]) -> None:
        """ウォッチャーを追加"""
        pass
```

### データ型定義

```python
@dataclass
class ConfigMetadata:
    """設定メタデータ"""
    created_at: datetime
    updated_at: datetime
    version: str
    schema_version: str
    checksum: Optional[str] = None

@dataclass
class InheritanceRule:
    """継承ルール"""
    source_level: ConfigLevel
    target_level: ConfigLevel
    key_patterns: List[str]
    strategy: str  # override, merge, ignore
    conditions: Optional[Dict[str, Any]] = None

@dataclass
class ConfigTemplate:
    """設定テンプレート"""
    name: str
    level: ConfigLevel
    template: Dict[str, Any]
    required_keys: List[str]
    optional_keys: List[str]

@dataclass
class ResolutionContext:
    """解決コンテキスト"""
    current_level: ConfigLevel
    requested_key: str
    inheritance_chain: List[ConfigSource]
    variables: Dict[str, Any]
```

## パブリックメソッド

### HierarchicalConfigAdapter

```python
def resolve(self, key_path: str, config_type: type = None) -> Optional[ConfigValue]:
    """
    設定値を階層的に解決

    Args:
        key_path: 設定キーパス（例: "quality.checks.enabled"）
        config_type: 期待する設定値の型

    Returns:
        Optional[ConfigValue]: 解決された設定値
    """
    # キャッシュ確認
    cache_key = f"{key_path}:{config_type.__name__ if config_type else 'Any'}"
    if cache_key in self._cache:
        cached_value = self._cache[cache_key]
        if self._is_cache_valid(cached_value):
            return cached_value

    try:
        # 優先度順にソースを並び替え
        sorted_sources = self._get_sorted_sources()

        # 階層的に設定値を検索
        for source, config in sorted_sources:
            value = self._extract_value(config, key_path)

            if value is not None:
                # 型チェック
                if config_type and not self._validate_type(value, config_type):
                    continue

                # 継承チェック
                inherited_value = self._check_inheritance(key_path, source, value)

                config_value = ConfigValue(
                    value=inherited_value or value,
                    source=source,
                    key_path=key_path,
                    inherited=inherited_value is not None,
                    overridden=self._is_overridden(key_path, source)
                )

                # キャッシュに保存
                self._cache[cache_key] = config_value

                return config_value

        # デフォルト値の確認
        default_value = self._get_default_value(key_path, config_type)
        if default_value is not None:
            return default_value

        return None

    except Exception as e:
        self._handle_resolution_error(key_path, e)
        return None

def resolve_all(self, key_path: str) -> List[ConfigValue]:
    """
    全階層の設定値を取得

    Args:
        key_path: 設定キーパス

    Returns:
        List[ConfigValue]: 全レベルの設定値リスト
    """
    values = []

    for source, config in self._get_sorted_sources():
        value = self._extract_value(config, key_path)

        if value is not None:
            config_value = ConfigValue(
                value=value,
                source=source,
                key_path=key_path,
                inherited=False,
                overridden=False
            )
            values.append(config_value)

    # オーバーライド情報を更新
    for i, value in enumerate(values):
        value.overridden = i < len(values) - 1

    return values

def add_source(self, source: ConfigSource, config: Dict[str, Any]) -> None:
    """
    設定ソースを追加

    Args:
        source: 設定ソース
        config: 設定データ
    """
    try:
        # バリデーション
        validation_result = self._validator.validate_level_constraints(source, config)

        if not validation_result.is_valid:
            raise ConfigValidationError(f"Invalid config for level {source.level}: {validation_result.errors}")

        # 既存ソースの確認
        if source in self._sources:
            old_config = self._sources[source]
            self._notify_config_changes(source, old_config, config)

        # ソース追加
        self._sources[source] = copy.deepcopy(config)

        # キャッシュクリア
        self._clear_affected_cache(source)

        # 有効性検証
        effective_config = self.get_effective_config()
        hierarchy_result = self._validator.validate_hierarchy(effective_config)

        if not hierarchy_result.is_valid:
            # ロールバック
            if source in self._sources:
                del self._sources[source]
            raise ConfigValidationError(f"Hierarchy validation failed: {hierarchy_result.errors}")

    except Exception as e:
        raise ConfigError(f"Failed to add config source: {str(e)}")

def get_effective_config(self) -> Dict[str, Any]:
    """
    有効な設定を取得（全階層をマージ）

    Returns:
        Dict[str, Any]: マージ済み設定
    """
    if not self._sources:
        return {}

    try:
        # ソースを優先度順にソート
        sorted_configs = [(source, config) for source, config in self._get_sorted_sources()]

        # 階層マージ実行
        merged_config = self._merger.merge_hierarchical(sorted_configs)

        # 変数展開
        resolved_config = self._resolve_variables(merged_config)

        return resolved_config

    except Exception as e:
        raise ConfigError(f"Failed to get effective config: {str(e)}")

def reload_source(self, source: ConfigSource) -> bool:
    """
    設定ソースを再読み込み

    Args:
        source: 再読み込み対象のソース

    Returns:
        bool: 再読み込み成功可否
    """
    try:
        # 新しい設定を読み込み
        new_config = self._loader.load_from_source(source)

        if new_config is None:
            if source.readonly:
                # 読み取り専用ソースが見つからない場合は削除
                if source in self._sources:
                    del self._sources[source]
                    self._clear_affected_cache(source)
                return True
            else:
                return False

        # 変更検出
        old_config = self._sources.get(source, {})
        if old_config != new_config:
            # 変更通知
            self._notify_config_changes(source, old_config, new_config)

            # ソース更新
            self._sources[source] = new_config

            # キャッシュクリア
            self._clear_affected_cache(source)

        return True

    except Exception as e:
        print(f"Failed to reload config source {source.name}: {str(e)}")
        return False

def set_value(
    self,
    key_path: str,
    value: Any,
    level: ConfigLevel = ConfigLevel.RUNTIME
) -> bool:
    """
    設定値を動的に設定

    Args:
        key_path: 設定キーパス
        value: 設定値
        level: 設定レベル

    Returns:
        bool: 設定成功可否
    """
    try:
        # 該当レベルのソースを検索
        target_source = self._find_writable_source(level)

        if not target_source:
            # 新しい一時ソースを作成
            target_source = ConfigSource(
                level=level,
                scope=ConfigScope.TEMPORARY,
                name=f"runtime_{level.name}",
                dynamic=True
            )
            self._sources[target_source] = {}

        # 値を設定
        old_value = self._extract_value(self._sources[target_source], key_path)
        self._set_nested_value(self._sources[target_source], key_path, value)

        # キャッシュクリア
        self._clear_key_cache(key_path)

        # 変更通知
        if self._notifier:
            change_event = ConfigChangeEvent(
                key_path=key_path,
                old_value=old_value,
                new_value=value,
                source=target_source,
                change_type="modify" if old_value is not None else "add"
            )
            self._notifier.notify_change(change_event)

        return True

    except Exception as e:
        print(f"Failed to set config value {key_path}: {str(e)}")
        return False
```

## プライベートメソッド

```python
def _get_sorted_sources(self) -> List[tuple[ConfigSource, Dict[str, Any]]]:
    """ソースを優先度順にソート"""
    items = list(self._sources.items())

    # 優先度でソート（レベル優先、次にpriority）
    return sorted(items, key=lambda x: (x[0].level.value, x[0].priority), reverse=True)

def _extract_value(self, config: Dict[str, Any], key_path: str) -> Any:
    """ネストした設定から値を抽出"""
    keys = key_path.split('.')
    current = config

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None

    return current

def _set_nested_value(self, config: Dict[str, Any], key_path: str, value: Any) -> None:
    """ネストした設定に値を設定"""
    keys = key_path.split('.')
    current = config

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        elif not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value

def _check_inheritance(self, key_path: str, source: ConfigSource, value: Any) -> Optional[Any]:
    """継承ルールをチェック"""
    for rule in self._get_inheritance_rules():
        if (rule.source_level == source.level and
            self._matches_pattern(key_path, rule.key_patterns)):

            # 上位レベルから値を継承
            parent_value = self._find_parent_value(key_path, rule.target_level)

            if parent_value and rule.strategy == "merge":
                return self._merge_values(parent_value, value)
            elif parent_value and rule.strategy == "override":
                return value
            elif parent_value and rule.strategy == "ignore":
                return parent_value

    return None

def _resolve_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """変数を展開"""
    resolved = copy.deepcopy(config)
    variables = self._extract_variables(resolved)

    return self._substitute_variables(resolved, variables)

def _substitute_variables(self, obj: Any, variables: Dict[str, Any]) -> Any:
    """変数置換を実行"""
    if isinstance(obj, str):
        # ${variable} 形式の変数を置換
        import re
        def replace_var(match):
            var_name = match.group(1)
            return str(variables.get(var_name, match.group(0)))

        return re.sub(r'\$\{([^}]+)\}', replace_var, obj)

    elif isinstance(obj, dict):
        return {key: self._substitute_variables(value, variables) for key, value in obj.items()}

    elif isinstance(obj, list):
        return [self._substitute_variables(item, variables) for item in obj]

    else:
        return obj

def _extract_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """設定から変数を抽出"""
    variables = {}

    # 環境変数
    import os
    variables.update(os.environ)

    # 設定内の variables セクション
    if 'variables' in config:
        variables.update(config['variables'])

    # システム情報
    import platform
    variables.update({
        'system': platform.system(),
        'platform': platform.platform(),
        'user': os.getenv('USER', 'unknown')
    })

    return variables

def _is_cache_valid(self, cached_value: ConfigValue) -> bool:
    """キャッシュの有効性を確認"""
    # 動的ソースの場合は常に無効
    if cached_value.source.dynamic:
        return False

    # ソースが削除されている場合は無効
    if cached_value.source not in self._sources:
        return False

    # TODO: ファイルの更新時刻チェック等
    return True

def _clear_affected_cache(self, source: ConfigSource) -> None:
    """影響を受けるキャッシュをクリア"""
    keys_to_remove = []

    for cache_key, cached_value in self._cache.items():
        if cached_value.source == source:
            keys_to_remove.append(cache_key)

    for key in keys_to_remove:
        del self._cache[key]

def _notify_config_changes(
    self,
    source: ConfigSource,
    old_config: Dict[str, Any],
    new_config: Dict[str, Any]
) -> None:
    """設定変更を通知"""
    if not self._notifier:
        return

    # 変更されたキーを検出
    changes = self._detect_changes(old_config, new_config, "")

    for change in changes:
        event = ConfigChangeEvent(
            key_path=change['key_path'],
            old_value=change['old_value'],
            new_value=change['new_value'],
            source=source,
            change_type=change['type']
        )
        self._notifier.notify_change(event)

def _detect_changes(
    self,
    old_dict: Dict[str, Any],
    new_dict: Dict[str, Any],
    prefix: str
) -> List[Dict[str, Any]]:
    """辞書の変更を再帰的に検出"""
    changes = []

    # 削除された項目
    for key, old_value in old_dict.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if key not in new_dict:
            changes.append({
                'key_path': full_key,
                'old_value': old_value,
                'new_value': None,
                'type': 'delete'
            })
        elif isinstance(old_value, dict) and isinstance(new_dict[key], dict):
            # 再帰的に変更をチェック
            changes.extend(self._detect_changes(old_value, new_dict[key], full_key))
        elif old_value != new_dict[key]:
            changes.append({
                'key_path': full_key,
                'old_value': old_value,
                'new_value': new_dict[key],
                'type': 'modify'
            })

    # 追加された項目
    for key, new_value in new_dict.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if key not in old_dict:
            changes.append({
                'key_path': full_key,
                'old_value': None,
                'new_value': new_value,
                'type': 'add'
            })

    return changes
```

## アダプターパターン実装

### ファイルシステム設定アダプター

```python
class FileSystemConfigAdapter(IConfigLoaderAdapter):
    """ファイルシステム設定アダプター"""

    def __init__(self, supported_formats: Dict[str, IConfigParser]):
        self._parsers = supported_formats

    def load_from_source(self, source: ConfigSource) -> Optional[Dict[str, Any]]:
        """ファイルから設定を読み込み"""
        if not source.path or not source.path.exists():
            return None

        try:
            # ファイル形式を検出
            file_format = self._detect_format(source.path)
            parser = self._parsers.get(file_format)

            if not parser:
                raise ConfigError(f"Unsupported file format: {file_format}")

            # パース実行
            with open(source.path, 'r', encoding='utf-8') as f:
                content = f.read()

            config = parser.parse(content)

            # メタデータ追加
            if isinstance(config, dict):
                config['_metadata'] = self._create_file_metadata(source.path)

            return config

        except Exception as e:
            print(f"Failed to load config from {source.path}: {str(e)}")
            return None

    def save_to_source(self, source: ConfigSource, config: Dict[str, Any]) -> bool:
        """ファイルに設定を保存"""
        if not source.path or source.readonly:
            return False

        try:
            # ファイル形式を検出
            file_format = self._detect_format(source.path)
            parser = self._parsers.get(file_format)

            if not parser:
                return False

            # メタデータを除去
            clean_config = copy.deepcopy(config)
            clean_config.pop('_metadata', None)

            # シリアライズ
            content = parser.serialize(clean_config)

            # ファイル保存
            source.path.parent.mkdir(parents=True, exist_ok=True)

            with open(source.path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"Failed to save config to {source.path}: {str(e)}")
            return False

    def _detect_format(self, path: Path) -> str:
        """ファイル形式を検出"""
        suffix = path.suffix.lower()

        format_map = {
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.toml': 'toml',
            '.ini': 'ini'
        }

        return format_map.get(suffix, 'yaml')

    def _create_file_metadata(self, path: Path) -> ConfigMetadata:
        """ファイルメタデータを作成"""
        stat = path.stat()

        return ConfigMetadata(
            created_at=datetime.fromtimestamp(stat.st_ctime),
            updated_at=datetime.fromtimestamp(stat.st_mtime),
            version="1.0",
            schema_version="1.0"
        )

class EnvironmentConfigAdapter(IConfigLoaderAdapter):
    """環境変数設定アダプター"""

    def __init__(self, prefix: str = "", mapping: Dict[str, str] = None):
        self._prefix = prefix
        self._mapping = mapping or {}

    def load_from_source(self, source: ConfigSource) -> Optional[Dict[str, Any]]:
        """環境変数から設定を読み込み"""
        import os

        config = {}
        prefix = f"{self._prefix}_" if self._prefix else ""

        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()

                # マッピング適用
                if config_key in self._mapping:
                    config_key = self._mapping[config_key]

                # ネストしたキーに変換
                nested_keys = config_key.split('_')
                self._set_nested_env_value(config, nested_keys, self._parse_env_value(value))

        return config if config else None

    def save_to_source(self, source: ConfigSource, config: Dict[str, Any]) -> bool:
        """環境変数への保存は未サポート"""
        return False

    def _set_nested_env_value(self, config: Dict[str, Any], keys: List[str], value: Any) -> None:
        """ネストした環境変数値を設定"""
        current = config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def _parse_env_value(self, value: str) -> Any:
        """環境変数値を適切な型に変換"""
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False
        elif value.isdigit():
            return int(value)
        elif '.' in value and value.replace('.', '').replace('-', '').isdigit():
            return float(value)
        elif value.startswith('[') and value.endswith(']'):
            # 簡単なリスト解析
            return [item.strip() for item in value[1:-1].split(',') if item.strip()]
        else:
            return value
```

### 階層マージ戦略

```python
class HierarchicalMerger(IConfigMerger):
    """階層設定マージャー"""

    def __init__(self, default_strategy: str = "deep_merge"):
        self._default_strategy = default_strategy
        self._strategies = {
            "override": self._merge_override,
            "deep_merge": self._merge_deep,
            "array_append": self._merge_array_append,
            "smart": self._merge_smart
        }

    def merge_hierarchical(
        self,
        configs: List[tuple[ConfigSource, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """階層設定をマージ"""
        if not configs:
            return {}

        # 最下位レベルから開始
        result = copy.deepcopy(configs[0][1])

        for source, config in configs[1:]:
            strategy = self._determine_strategy(source, config)
            merge_func = self._strategies.get(strategy, self._merge_deep)
            result = merge_func(result, config)

        return result

    def _merge_deep(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深いマージ"""
        result = copy.deepcopy(base)

        for key, value in override.items():
            if (key in result and
                isinstance(result[key], dict) and
                isinstance(value, dict)):
                result[key] = self._merge_deep(result[key], value)
            else:
                result[key] = copy.deepcopy(value)

        return result

    def _merge_smart(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """スマートマージ（データ型に応じて戦略を選択）"""
        result = copy.deepcopy(base)

        for key, value in override.items():
            if key not in result:
                result[key] = copy.deepcopy(value)
            elif isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_smart(result[key], value)
            elif isinstance(result[key], list) and isinstance(value, list):
                # 配列は特別なマージルールを適用
                result[key] = self._merge_arrays(result[key], value)
            else:
                result[key] = copy.deepcopy(value)

        return result

    def _merge_arrays(self, base: List[Any], override: List[Any]) -> List[Any]:
        """配列のマージ戦略"""
        # 設定によってappend, prepend, replace等を選択
        return base + override  # デフォルトはappend
```

## 依存関係

```python
from domain.entities import ProjectConfig, QualityConfig
from domain.services import IConfigurationService
from infrastructure.persistence import IFileSystemService
from application.use_cases import UpdateConfigUseCase
```

## 設計原則遵守

### アダプターパターン
- **多様な設定ソース**: ファイル、環境変数、データベース等を統一インターフェースで扱う
- **階層解決戦略**: 複数の解決戦略を動的に選択可能
- **変更通知メカニズム**: 設定変更の監視と通知を抽象化

### 開放閉鎖原則
- **新しい設定ソースの追加**: インターフェース実装で容易に拡張
- **新しいマージ戦略の追加**: 戦略パターンで新戦略を追加可能
- **既存機能の変更なし**: 新機能追加が既存コードに影響しない

## 使用例

### 基本的な使用

```python
# アダプター設定
parsers = {
    'yaml': YamlConfigParser(),
    'json': JsonConfigParser(),
    'toml': TomlConfigParser()
}

file_adapter = FileSystemConfigAdapter(parsers)
env_adapter = EnvironmentConfigAdapter(prefix="NOVEL")
merger = HierarchicalMerger()
validator = JsonSchemaValidator()

config_hierarchy = HierarchicalConfigAdapter(file_adapter, merger, validator)

# 階層設定の構築
sources = [
    (ConfigSource(ConfigLevel.SYSTEM, ConfigScope.SYSTEM_WIDE, Path("/etc/novel/config.yaml")), {}),
    (ConfigSource(ConfigLevel.GLOBAL, ConfigScope.USER, Path("~/.novel/config.yaml")), {}),
    (ConfigSource(ConfigLevel.PROJECT, ConfigScope.PROJECT, Path("./novel.yaml")), {}),
    (ConfigSource(ConfigLevel.LOCAL, ConfigScope.DIRECTORY, Path("./.novel.yaml")), {}),
]

# ソース追加
for source, _ in sources:
    config = file_adapter.load_from_source(source)
    if config:
        config_hierarchy.add_source(source, config)

# 設定値の解決
quality_enabled = config_hierarchy.resolve("quality.checks.enabled", bool)
if quality_enabled:
    print(f"Quality checks enabled: {quality_enabled.value}")
    print(f"Source: {quality_enabled.source.name}")
```

### 動的設定更新

```python
# 設定変更の監視
def on_config_change(event: ConfigChangeEvent):
    print(f"Config changed: {event.key_path}")
    print(f"  Old: {event.old_value}")
    print(f"  New: {event.new_value}")
    print(f"  Source: {event.source.name}")

config_hierarchy.add_watcher(on_config_change)

# 実行時設定変更
config_hierarchy.set_value("quality.threshold", 85.0, ConfigLevel.RUNTIME)

# ソース再読み込み
for source in sources:
    config_hierarchy.reload_source(source[0])
```

### 継承ルールの活用

```python
# 継承ルール定義
rules = [
    InheritanceRule(
        source_level=ConfigLevel.PROJECT,
        target_level=ConfigLevel.GLOBAL,
        key_patterns=["quality.*"],
        strategy="merge"
    ),
    InheritanceRule(
        source_level=ConfigLevel.LOCAL,
        target_level=ConfigLevel.PROJECT,
        key_patterns=["author.*"],
        strategy="override"
    )
]

# 継承を考慮した設定解決
inherited_config = config_hierarchy.get_effective_config()
```

## エラーハンドリング

```python
class ConfigError(Exception):
    """設定関連エラーのベースクラス"""
    pass

class ConfigValidationError(ConfigError):
    """設定検証エラー"""
    pass

class ConfigResolutionError(ConfigError):
    """設定解決エラー"""
    pass

class ConfigHierarchyError(ConfigError):
    """階層構造エラー"""
    pass

def handle_config_hierarchy_error(error: ConfigError, context: ResolutionContext) -> Optional[ConfigValue]:
    """階層設定エラーのハンドリング"""
    if isinstance(error, ConfigValidationError):
        # 検証エラーの場合はデフォルト値を返す
        return ConfigValue(
            value=None,
            source=ConfigSource(ConfigLevel.SYSTEM, ConfigScope.SYSTEM_WIDE, name="default"),
            key_path=context.requested_key,
            inherited=False,
            overridden=False
        )
    elif isinstance(error, ConfigResolutionError):
        # 解決エラーの場合は上位階層を試行
        return None
    else:
        # その他のエラーは再発生
        raise error
```

## テスト観点

### ユニットテスト
- 各階層レベルでの設定解決
- マージ戦略の正確性
- 継承ルールの適用
- 変数展開機能

### 統合テスト
- 複数ソースの統合動作
- ファイルシステムとの連携
- 動的更新の動作
- エラー状況での復旧

### E2Eテスト
- 実際の設定ファイル階層での動作
- 設定変更の伝播
- パフォーマンス測定
- メモリ使用量の監視

## 品質基準

### コード品質
- 循環的複雑度: 15以下
- テストカバレッジ: 88%以上
- 型安全性: 100%

### パフォーマンス
- 設定解決: 10ms以内
- 階層マージ: 50ms以内
- キャッシュ効率: 90%以上

### メモリ効率
- キャッシュサイズ制限
- 不要なキャッシュの自動削除
- メモリリーク防止
