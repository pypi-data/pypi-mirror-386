# YAML品質設定リポジトリ仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、品質チェック設定のYAMLファイルベース永続化を提供する。

### 1.2 スコープ
- 品質チェック設定の作成・保存・検索・更新の完全な永続化機能
- プロジェクト固有とグローバル設定の階層管理
- 品質基準とチェックルールの柔軟な設定
- レガシー設定との互換性確保

### 1.3 アーキテクチャ位置
```
Domain Layer
├── QualityConfigRepository (Interface) ← Infrastructure Layer
└── QualityConfig (Entity)              └── YamlQualityConfigRepository (Implementation)
```

## 2. 機能仕様

### 2.1 基本CRUD操作
```python
# 保存
def save(quality_config: QualityConfig, project_id: str | None = None) -> None

# 検索
def find_by_project(project_id: str) -> QualityConfig | None
def find_global_config() -> QualityConfig | None
def find_merged_config(project_id: str) -> QualityConfig

# 存在確認
def exists_project_config(project_id: str) -> bool
def exists_global_config() -> bool

# 更新
def update_check_rule(project_id: str, rule_name: str, rule_config: dict) -> bool
def update_quality_standard(project_id: str, standard_config: dict) -> bool

# 削除
def delete_project_config(project_id: str) -> bool
def delete_check_rule(project_id: str, rule_name: str) -> bool
```

### 2.2 階層設定管理
```python
# 設定の継承・マージ
def get_effective_config(project_id: str) -> QualityConfig
def get_config_inheritance_chain(project_id: str) -> list[QualityConfig]

# グローバル設定管理
def update_global_config(config_updates: dict) -> bool
def reset_global_config() -> bool

# プロジェクト設定オーバーライド
def override_global_setting(
    project_id: str,
    setting_path: str,
    new_value: Any
) -> bool
```

### 2.3 設定テンプレート機能
```python
# テンプレート管理
def create_config_template(
    template_name: str,
    base_config: QualityConfig
) -> bool

def apply_config_template(
    project_id: str,
    template_name: str
) -> bool

def list_available_templates() -> list[str]

# プリセット設定
def apply_preset_config(
    project_id: str,
    preset_type: str  # "beginner", "intermediate", "advanced", "custom"
) -> bool
```

### 2.4 設定検証・検査機能
```python
# 設定の妥当性検証
def validate_config(config: QualityConfig) -> tuple[bool, list[str]]

# 設定の整合性チェック
def check_config_consistency(project_id: str) -> dict[str, Any]

# 設定の依存関係検証
def validate_dependencies(config: QualityConfig) -> list[str]
```

### 2.5 設定インポート・エクスポート
```python
# 設定のエクスポート
def export_config(
    project_id: str | None,
    export_path: Path,
    include_templates: bool = False
) -> bool

# 設定のインポート
def import_config(
    import_path: Path,
    project_id: str | None = None,
    merge_strategy: str = "override"
) -> bool

# 設定の比較
def compare_configs(
    config_a: QualityConfig,
    config_b: QualityConfig
) -> dict[str, Any]
```

## 3. データ構造仕様

### 3.1 ファイル配置
```
# グローバル設定
00_ガイド/
├── src/noveler/config/
│   ├── quality_global_config.yaml     # グローバル品質設定
│   └── quality_templates/             # 設定テンプレート
│       ├── beginner.yaml
│       ├── intermediate.yaml
│       └── advanced.yaml

# プロジェクト固有設定
プロジェクトルート/
├── 50_管理資料/
│   └── 品質チェック設定.yaml          # プロジェクト固有設定
└── backup/                           # バックアップ（任意）
    └── 20250721_143022/
        └── 品質チェック設定.yaml
```

### 3.2 品質チェック設定YAML構造
```yaml
metadata:
  config_version: "1.2"
  project_name: "転生したら最強の魔法使いだった件"
  created_at: "2025-07-21T10:00:00"
  updated_at: "2025-07-21T14:30:22"
  inherits_from: "global"              # 継承設定

# 品質基準設定
quality_standards:
  minimum_pass_score: 70.0
  target_score: 85.0
  excellence_threshold: 95.0

  # レベル別基準
  beginner:
    minimum_pass_score: 60.0
    target_score: 75.0
  intermediate:
    minimum_pass_score: 70.0
    target_score: 85.0
  advanced:
    minimum_pass_score: 80.0
    target_score: 90.0

# チェックルール設定
check_rules:
  basic_style:
    enabled: true
    weight: 0.3
    rules:
      文体統一性:
        enabled: true
        threshold: 80.0
        severity: "warning"
      誤字脱字:
        enabled: true
        threshold: 90.0
        severity: "error"
      句読点使用:
        enabled: true
        threshold: 85.0
        severity: "info"

  story_structure:
    enabled: true
    weight: 0.4
    rules:
      導入部分:
        enabled: true
        threshold: 75.0
        min_word_ratio: 0.1
        max_word_ratio: 0.3
      展開部分:
        enabled: true
        threshold: 80.0
        min_word_ratio: 0.4
        max_word_ratio: 0.7
      結末部分:
        enabled: true
        threshold: 75.0
        min_word_ratio: 0.1
        max_word_ratio: 0.3

  character_consistency:
    enabled: true
    weight: 0.3
    rules:
      名前統一性:
        enabled: true
        threshold: 95.0
        severity: "error"
      性格一貫性:
        enabled: true
        threshold: 80.0
        severity: "warning"
      口調統一性:
        enabled: true
        threshold: 85.0
        severity: "info"

# 実行設定
execution_settings:
  parallel_execution: true
  max_workers: 4
  timeout_seconds: 300
  retry_attempts: 2

  # チェック実行順序
  check_order:
    - "basic_style"
    - "story_structure"
    - "character_consistency"

  # スキップ条件
  skip_conditions:
    - condition: "word_count < 500"
      affected_checks: ["story_structure"]
    - condition: "episode_status == 'DRAFT'"
      affected_checks: ["character_consistency"]

# 通知設定
notification_settings:
  enabled: true
  channels:
    - type: "console"
      level: "warning"
    - type: "file"
      level: "info"
      path: "logs/quality_check.log"

  # アラート条件
  alerts:
    score_drop:
      enabled: true
      threshold: 10.0
      consecutive_failures: 3
    critical_issues:
      enabled: true
      severity_levels: ["error", "critical"]

# カスタムルール
custom_rules:
  - name: "専門用語統一チェック"
    type: "terminology"
    enabled: true
    config:
      terminology_file: "専門用語辞書.yaml"
      threshold: 90.0
    weight: 0.1

  - name: "シーン転換チェック"
    type: "scene_transition"
    enabled: false
    config:
      min_transition_words: 10
      transition_markers: ["***", "◇", "　◇　◇　◇"]
    weight: 0.05

# 出力設定
output_settings:
  format: "detailed"              # "summary", "detailed", "json"
  include_suggestions: true
  include_examples: true
  language: "ja"

  # レポート生成
  reports:
    html_report: true
    markdown_report: true
    json_export: true

# デバッグ設定
debug_settings:
  verbose_logging: false
  save_intermediate_results: false
  performance_profiling: false
```

### 3.3 グローバル設定構造
```yaml
# quality_global_config.yaml
metadata:
  config_version: "1.2"
  created_at: "2025-07-21T10:00:00"
  updated_at: "2025-07-21T14:30:22"

# デフォルト品質基準
default_quality_standards:
  minimum_pass_score: 70.0
  target_score: 85.0
  excellence_threshold: 95.0

# デフォルトチェックルール
default_check_rules:
  # 基本的なチェックルール定義（上記と同じ構造）

# システム設定
system_settings:
  default_language: "ja"
  max_file_size_mb: 100
  cache_enabled: true
  cache_ttl_hours: 24

# 機能フラグ
feature_flags:
  experimental_ai_checks: false
  advanced_analytics: true
  custom_rule_engine: true
```

## 4. 技術仕様

### 4.1 依存関係
```python
# 外部ライブラリ
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict, List

# ドメイン層
from domain.entities.quality_config import QualityConfig, CheckRule, QualityStandard
from domain.repositories.quality_config_repository import QualityConfigRepository
from domain.value_objects.quality_threshold import QualityThreshold
```

### 4.2 エラーハンドリング
```python
# カスタム例外
class QualityConfigRepositoryError(Exception):
    pass

class QualityConfigNotFoundError(QualityConfigRepositoryError):
    pass

class InvalidQualityConfigError(QualityConfigRepositoryError):
    pass

class ConfigValidationError(QualityConfigRepositoryError):
    pass

class ConfigMergeConflictError(QualityConfigRepositoryError):
    pass
```

## 5. パフォーマンス要件

### 5.1 応答時間
- 設定読み込み: 50ms以内
- 設定保存: 100ms以内
- 設定マージ: 30ms以内
- 設定検証: 200ms以内

### 5.2 メモリ使用量
- 単一設定: 5MB以内
- マージ済み設定: 10MB以内
- テンプレート全体: 50MB以内

### 5.3 同時実行性
- 読み取り操作: 並行実行可能
- 書き込み操作: ファイルロック機構で排他制御
- 設定検証: 並行実行可能

## 6. 品質保証

### 6.1 データ整合性
- 設定スキーマの妥当性検証
- 継承関係の循環参照検出
- 数値範囲の妥当性チェック
- 必須フィールドの存在確認

### 6.2 エラー回復
- 破損した設定ファイルの自動修復
- デフォルト設定への自動フォールバック
- バックアップからの自動復元
- 部分的な設定適用

### 6.3 バージョン管理
- 設定スキーマバージョン管理
- 後方互換性の保証
- マイグレーション機能
- 設定変更履歴の記録

## 7. セキュリティ

### 7.1 アクセス制御
- ファイルシステム権限に基づくアクセス制御
- プロジェクト固有設定の分離
- グローバル設定への制限アクセス

### 7.2 データ保護
- エンコーディング: UTF-8統一
- 機密情報の除去・暗号化
- 設定の不正改変検出
- 安全なデフォルト値の設定

## 8. 互換性

### 8.1 レガシーシステム
- 既存設定ファイルとの完全互換
- 段階的移行サポート
- 旧設定の自動変換
- 互換性モードの提供

### 8.2 将来拡張性
- 新しいチェックタイプの動的追加
- プラグインベースのルール拡張
- 外部設定ソースとの連携
- 設定のバージョニング強化

## 9. 使用例

### 9.1 基本的な使用パターン
```python
# リポジトリ初期化
config_repo = YamlQualityConfigRepository()

# プロジェクト設定の作成
quality_config = QualityConfig(
    quality_standards=QualityStandard(
        minimum_pass_score=70.0,
        target_score=85.0
    ),
    check_rules={
        "basic_style": CheckRule(
            enabled=True,
            weight=0.3,
            threshold=80.0
        )
    }
)

# 設定保存
config_repo.save(quality_config, "project-001")

# 効果的な設定取得（継承込み）
effective_config = config_repo.get_effective_config("project-001")
```

### 9.2 テンプレート・プリセット活用例
```python
# 初心者向けプリセット適用
config_repo.apply_preset_config("project-001", "beginner")

# カスタムテンプレート作成
custom_config = QualityConfig(...)
config_repo.create_config_template("my_template", custom_config)

# テンプレート適用
config_repo.apply_config_template("project-002", "my_template")
```

### 9.3 設定検証・管理例
```python
# 設定の妥当性検証
is_valid, errors = config_repo.validate_config(quality_config)
if not is_valid:
    for error in errors:
        print(f"設定エラー: {error}")

# 設定の比較
differences = config_repo.compare_configs(config_a, config_b)
print(f"設定差異: {differences}")

# 設定のエクスポート・インポート
export_path = Path("config_backup.yaml")
config_repo.export_config("project-001", export_path)
config_repo.import_config(export_path, "project-002")
```

## 10. テスト仕様

### 10.1 単体テスト
- 設定CRUD操作の動作確認
- 設定マージロジックのテスト
- 設定検証機能のテスト
- エラーケースの処理確認

### 10.2 統合テスト
- 実際のファイルシステムでの動作確認
- 設定継承の統合テスト
- テンプレート機能の統合テスト
- パフォーマンステスト

### 10.3 エラーシナリオ
- 破損した設定ファイル
- 循環継承の検出
- 不正な設定値
- ファイル権限エラー
- ディスク容量不足

## 11. 運用・監視

### 11.1 ログ出力
- 設定変更のログ記録
- エラー発生時の詳細ログ
- 設定検証結果のログ
- パフォーマンス測定ログ

### 11.2 メトリクス
- 設定読み込み・保存回数
- 設定検証の成功・失敗率
- エラー発生率の監視
- 設定ファイルサイズの監視

### 11.3 アラート
- 設定検証エラー
- ファイルアクセスエラー
- データ整合性エラー
- パフォーマンス劣化

## 12. 実装メモ

### 12.1 実装ファイル
- **メインクラス**: `src/noveler/infrastructure/repositories/yaml_quality_config_repository.py`
- **テストファイル**: `tests/unit/infrastructure/repositories/test_yaml_quality_config_repository.py`

### 12.2 設計方針
- DDD原則の厳格な遵守
- 設定の階層化と継承の明確な実装
- 拡張性を重視した設計
- 設定検証の自動化

### 12.3 今後の改善点
- [ ] GUI設定エディタとの連携
- [ ] 設定変更の実時間反映
- [ ] 機械学習による最適設定提案
- [ ] クラウド設定同期機能
- [ ] 設定のA/Bテスト機能
