# SPEC-CONFIG-001: ConfigurationRepository 仕様書

## 要件トレーサビリティ

**要件ID**: REQ-CONFIG-001, REQ-CONFIG-002, REQ-CONFIG-003 (階層化設定管理システム)

**主要要件**:
- REQ-CONFIG-001: 階層化ディレクトリ構造管理
- REQ-CONFIG-002: 設定優先度システム
- REQ-CONFIG-003: system_config.yaml設計

**実装状況**: ✅実装済み
**テストカバレッジ**: tests/unit/test_configuration_repository.py
**関連仕様書**: SPEC-CONFIG-102_統合設定管理システム仕様書.md

## 概要

`ConfigurationRepository`は、システム全体の設定情報を管理するリポジトリです。プロジェクト固有の設定、グローバル設定、品質チェック設定などを統合的に管理し、YAMLファイルベースで永続化します。

## クラス設計

```python
class ConfigurationRepository:
    """システム設定管理リポジトリ"""

    def __init__(self, config_base_path: Path):
        """
        Args:
            config_base_path: 設定ファイルのベースパス
        """
        self._config_base_path = config_base_path
        self._cache: Dict[str, Configuration] = {}
```

## データ構造

### インターフェース

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

class ConfigurationRepositoryInterface(ABC):
    """設定リポジトリインターフェース"""

    @abstractmethod
    def find_global_config(self) -> Optional[GlobalConfiguration]:
        """グローバル設定を取得"""
        pass

    @abstractmethod
    def find_project_config(self, project_name: str) -> Optional[ProjectConfiguration]:
        """プロジェクト固有設定を取得"""
        pass

    @abstractmethod
    def find_quality_config(self, project_name: str) -> Optional[QualityConfiguration]:
        """品質チェック設定を取得"""
        pass

    @abstractmethod
    def save_global_config(self, config: GlobalConfiguration) -> None:
        """グローバル設定を保存"""
        pass

    @abstractmethod
    def save_project_config(self, project_name: str, config: ProjectConfiguration) -> None:
        """プロジェクト固有設定を保存"""
        pass

    @abstractmethod
    def save_quality_config(self, project_name: str, config: QualityConfiguration) -> None:
        """品質チェック設定を保存"""
        pass

    @abstractmethod
    def merge_configs(self, base: Configuration, override: Configuration) -> Configuration:
        """設定をマージ（オーバーライド優先）"""
        pass
```

### データモデル

```python
from dataclasses import dataclass, field
from enum import Enum

class ConfigurationType(Enum):
    """設定タイプ"""
    GLOBAL = "global"
    PROJECT = "project"
    QUALITY = "quality"

@dataclass
class Configuration:
    """設定基底クラス"""
    version: str
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GlobalConfiguration(Configuration):
    """グローバル設定"""
    default_author: str
    default_project_template: str
    quality_check_defaults: Dict[str, Any]
    ai_assistance_settings: Dict[str, Any]
    output_formats: List[str]
    backup_settings: Dict[str, Any]

@dataclass
class ProjectConfiguration(Configuration):
    """プロジェクト固有設定"""
    project_name: str
    author_name: str
    target_audience: str
    writing_style: Dict[str, Any]
    publication_settings: Dict[str, Any]
    custom_templates: Dict[str, str]
    workflow_settings: Dict[str, Any]

@dataclass
class QualityConfiguration(Configuration):
    """品質チェック設定"""
    enabled_checks: List[str]
    thresholds: Dict[str, float]
    custom_rules: List[Dict[str, Any]]
    ignore_patterns: List[str]
    auto_fix_settings: Dict[str, bool]
    report_formats: List[str]
```

## パブリックメソッド

### 設定取得

```python
def find_global_config(self) -> Optional[GlobalConfiguration]:
    """グローバル設定を取得"""
    config_path = self._config_base_path / "global_config.yaml"
    if not config_path.exists():
        return None

    if "global" in self._cache:
        return self._cache["global"]

    data = self._load_yaml(config_path)
    config = self._create_global_config(data)
    self._cache["global"] = config
    return config

def find_project_config(self, project_name: str) -> Optional[ProjectConfiguration]:
    """プロジェクト固有設定を取得"""
    config_path = self._get_project_config_path(project_name)
    if not config_path.exists():
        return None

    cache_key = f"project_{project_name}"
    if cache_key in self._cache:
        return self._cache[cache_key]

    data = self._load_yaml(config_path)
    config = self._create_project_config(data)
    self._cache[cache_key] = config
    return config

def find_quality_config(self, project_name: str) -> Optional[QualityConfiguration]:
    """品質チェック設定を取得"""
    config_path = self._get_quality_config_path(project_name)
    if not config_path.exists():
        return None

    cache_key = f"quality_{project_name}"
    if cache_key in self._cache:
        return self._cache[cache_key]

    data = self._load_yaml(config_path)
    config = self._create_quality_config(data)
    self._cache[cache_key] = config
    return config
```

### 設定保存

```python
def save_global_config(self, config: GlobalConfiguration) -> None:
    """グローバル設定を保存"""
    config_path = self._config_base_path / "global_config.yaml"
    config.updated_at = datetime.now()

    data = self._config_to_dict(config)
    self._save_yaml(config_path, data)
    self._cache["global"] = config

def save_project_config(self, project_name: str, config: ProjectConfiguration) -> None:
    """プロジェクト固有設定を保存"""
    config_path = self._get_project_config_path(project_name)
    config.updated_at = datetime.now()

    data = self._config_to_dict(config)
    self._save_yaml(config_path, data)
    self._cache[f"project_{project_name}"] = config

def save_quality_config(self, project_name: str, config: QualityConfiguration) -> None:
    """品質チェック設定を保存"""
    config_path = self._get_quality_config_path(project_name)
    config.updated_at = datetime.now()

    data = self._config_to_dict(config)
    self._save_yaml(config_path, data)
    self._cache[f"quality_{project_name}"] = config
```

### 設定マージ

```python
def merge_configs(self, base: Configuration, override: Configuration) -> Configuration:
    """設定をマージ（オーバーライド優先）"""
    base_dict = self._config_to_dict(base)
    override_dict = self._config_to_dict(override)

    merged = self._deep_merge(base_dict, override_dict)

    # 設定タイプに応じて適切なクラスを返す
    if isinstance(base, GlobalConfiguration):
        return self._create_global_config(merged)
    elif isinstance(base, ProjectConfiguration):
        return self._create_project_config(merged)
    elif isinstance(base, QualityConfiguration):
        return self._create_quality_config(merged)
    else:
        raise ValueError(f"Unknown configuration type: {type(base)}")
```

### 設定の検証と初期化

```python
def initialize_default_configs(self, project_name: Optional[str] = None) -> None:
    """デフォルト設定を初期化"""
    # グローバル設定の初期化
    if not self.find_global_config():
        default_global = self._create_default_global_config()
        self.save_global_config(default_global)

    # プロジェクト設定の初期化
    if project_name and not self.find_project_config(project_name):
        default_project = self._create_default_project_config(project_name)
        self.save_project_config(project_name, default_project)

def validate_config(self, config: Configuration) -> List[str]:
    """設定の妥当性を検証"""
    errors = []

    if isinstance(config, QualityConfiguration):
        # 閾値の範囲チェック
        for key, value in config.thresholds.items():
            if not 0 <= value <= 100:
                errors.append(f"閾値 {key} が無効な範囲です: {value}")

    elif isinstance(config, ProjectConfiguration):
        # 必須フィールドチェック
        if not config.author_name:
            errors.append("著者名が設定されていません")

    return errors
```

## プライベートメソッド

### ファイル操作

```python
def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
    """YAMLファイルを読み込み"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        raise ConfigurationLoadError(f"設定ファイルの読み込みに失敗: {file_path}") from e

def _save_yaml(self, file_path: Path, data: Dict[str, Any]) -> None:
    """YAMLファイルに保存"""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    except Exception as e:
        raise ConfigurationSaveError(f"設定ファイルの保存に失敗: {file_path}") from e
```

### データ変換

```python
def _create_global_config(self, data: Dict[str, Any]) -> GlobalConfiguration:
    """辞書からグローバル設定を作成"""
    return GlobalConfiguration(
        version=data.get('version', '1.0'),
        updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat())),
        metadata=data.get('metadata', {}),
        default_author=data.get('default_author', ''),
        default_project_template=data.get('default_project_template', 'standard'),
        quality_check_defaults=data.get('quality_check_defaults', {}),
        ai_assistance_settings=data.get('ai_assistance_settings', {}),
        output_formats=data.get('output_formats', ['markdown']),
        backup_settings=data.get('backup_settings', {})
    )

def _config_to_dict(self, config: Configuration) -> Dict[str, Any]:
    """設定オブジェクトを辞書に変換"""
    result = {}
    for field_name, field_value in config.__dict__.items():
        if field_name.startswith('_'):
            continue

        if isinstance(field_value, datetime):
            result[field_name] = field_value.isoformat()
        elif isinstance(field_value, Enum):
            result[field_name] = field_value.value
        else:
            result[field_name] = field_value

    return result
```

### ユーティリティ

```python
def _get_project_config_path(self, project_name: str) -> Path:
    """プロジェクト設定ファイルパスを取得"""
    return Path(f"/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/{project_name}/プロジェクト設定.yaml")

def _get_quality_config_path(self, project_name: str) -> Path:
    """品質チェック設定ファイルパスを取得"""
    return Path(f"/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/{project_name}/50_管理資料/品質チェック設定.yaml")

def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """辞書を深くマージ"""
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = self._deep_merge(result[key], value)
        else:
            result[key] = value

    return result
```

## 永続化仕様

### ファイル構造

```
9_小説/
├── 00_ガイド/
│   └── config/
│       └── global_config.yaml      # グローバル設定
└── [プロジェクト名]/
    ├── プロジェクト設定.yaml        # プロジェクト固有設定
    └── 50_管理資料/
        └── 品質チェック設定.yaml    # 品質チェック設定
```

### YAMLフォーマット

#### グローバル設定
```yaml
version: "1.0"
updated_at: "2025-01-21T10:00:00"
metadata:
  description: "システム全体のデフォルト設定"

default_author: "デフォルト著者名"
default_project_template: "standard"

quality_check_defaults:
  enable_auto_fix: true
  min_quality_score: 70
  check_on_save: true

ai_assistance_settings:
  model: "claude-3"
  temperature: 0.7
  max_tokens: 4000

output_formats:
  - markdown
  - html
  - pdf

backup_settings:
  auto_backup: true
  backup_interval_minutes: 30
  max_backups: 10
```

#### プロジェクト設定
```yaml
version: "1.0"
updated_at: "2025-01-21T10:00:00"
metadata:
  created_at: "2025-01-01T10:00:00"

project_name: "転生したら最強の魔法使いだった件"
author_name: "山田太郎"
target_audience: "なろう系ファンタジー好きの10-30代"

writing_style:
  viewpoint: "一人称"
  tense: "過去形"
  tone: "軽快でユーモラス"

publication_settings:
  platform: "小説家になろう"
  update_schedule: "毎日更新"
  target_word_count: 3000

custom_templates:
  episode: "custom_episode_template.md"
  character: "custom_character_template.yaml"

workflow_settings:
  require_review: true
  auto_publish: false
  quality_threshold: 80
```

## 依存関係

- `pathlib.Path`: ファイルパス操作
- `yaml`: YAML形式の読み書き
- `datetime`: タイムスタンプ管理
- `dataclasses`: データモデル定義
- `typing`: 型ヒント
- Domain層のエラークラス（ConfigurationError等）

## 設計原則遵守

### DDDの原則
- **レポジトリパターン**: 設定の永続化詳細をドメイン層から隠蔽
- **集約**: 設定タイプごとに一貫性を保証
- **値オブジェクト**: 設定値を不変オブジェクトとして扱う

### リポジトリパターンの実装
- インターフェースと実装の分離
- ドメインオブジェクトの永続化透過性
- キャッシュによるパフォーマンス最適化

## 使用例

```python
# リポジトリの初期化
config_repo = ConfigurationRepository(Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/config"))

# グローバル設定の取得と更新
global_config = config_repo.find_global_config()
if global_config:
    global_config.default_author = "新しいデフォルト著者"
    global_config.quality_check_defaults['min_quality_score'] = 75
    config_repo.save_global_config(global_config)

# プロジェクト設定の取得
project_config = config_repo.find_project_config("転生したら最強の魔法使いだった件")
if project_config:
    print(f"著者: {project_config.author_name}")
    print(f"更新スケジュール: {project_config.publication_settings['update_schedule']}")

# 品質チェック設定の作成
quality_config = QualityConfiguration(
    version="1.0",
    updated_at=datetime.now(),
    enabled_checks=["basic_style", "composition", "consistency"],
    thresholds={
        "readability": 80,
        "sentence_variety": 70,
        "dialogue_balance": 60
    },
    custom_rules=[
        {"rule": "no_excessive_exclamation", "max_count": 3}
    ],
    ignore_patterns=["TODO:", "FIXME:"],
    auto_fix_settings={
        "punctuation": True,
        "spacing": True,
        "line_breaks": False
    },
    report_formats=["console", "markdown"]
)
config_repo.save_quality_config("転生したら最強の魔法使いだった件", quality_config)

# 設定のマージ（プロジェクト設定でグローバル設定をオーバーライド）
base_config = config_repo.find_global_config()
project_override = config_repo.find_project_config("転生したら最強の魔法使いだった件")
merged_config = config_repo.merge_configs(base_config, project_override)

# デフォルト設定の初期化
config_repo.initialize_default_configs("新規プロジェクト")

# 設定の検証
errors = config_repo.validate_config(quality_config)
if errors:
    print(f"設定エラー: {errors}")
```

## エラーハンドリング

```python
class ConfigurationError(Exception):
    """設定エラーの基底クラス"""
    pass

class ConfigurationLoadError(ConfigurationError):
    """設定読み込みエラー"""
    pass

class ConfigurationSaveError(ConfigurationError):
    """設定保存エラー"""
    pass

class ConfigurationValidationError(ConfigurationError):
    """設定検証エラー"""
    pass

# 使用例
try:
    config = config_repo.find_project_config("存在しないプロジェクト")
    if not config:
        # デフォルト設定を作成
        config_repo.initialize_default_configs("存在しないプロジェクト")
except ConfigurationLoadError as e:
    logger.error(f"設定ファイルの読み込みに失敗: {e}")
    # フォールバック処理
except ConfigurationValidationError as e:
    logger.error(f"設定が無効です: {e}")
    # 修正を促す
```

## テスト観点

### ユニットテスト
- 各設定タイプの作成・読み込み・保存
- 設定のマージロジック
- バリデーションロジック
- キャッシュの動作

### 統合テスト
- ファイルシステムとの連携
- 複数設定ファイルの統合的な管理
- 設定の継承とオーバーライド

### E2Eテスト
```gherkin
Feature: システム設定管理
  Scenario: プロジェクト設定のカスタマイズ
    Given デフォルトのグローバル設定が存在する
    When プロジェクト固有の品質基準を設定する
    Then プロジェクトの品質チェックで新しい基準が適用される
```

## 品質基準

- コードカバレッジ: 90%以上
- サイクロマティック複雑度: 10以下
- 設定ファイルのスキーマ検証
- 後方互換性の維持（バージョン管理）
- エラーメッセージの具体性と対処法の明示
