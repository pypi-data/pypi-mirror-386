# Phase 2.2 完了報告: Configuration Service Strict Mode 実装

**実装日**: 2025-10-11
**実装者**: Claude Code
**ステータス**: ✅ 完了

---

## 概要

Configuration Service にstrict mode（OFF → WARNING → ERROR）を実装し、設定値のフォールバック動作を段階的に制御可能にしました。これにより、設定値が欠落している場合に「サンプルデータか実データか分からない」問題を解決します。

---

## 実装内容

### 1. StrictModeConfig 拡張

**ファイル**: `src/noveler/infrastructure/config/strict_mode_config.py`

- `config_service: StrictLevel` 属性を追加
- `NOVELER_STRICT_CONFIG` 環境変数サポート
- `is_config_strict()` および `should_warn_on_config_fallback()` ヘルパーメソッド追加

### 2. MissingConfigurationError 例外クラス追加

**ファイル**: `src/noveler/domain/exceptions/base.py`

```python
class MissingConfigurationError(DomainError):
    """必須の設定値が見つからない場合のエラー.

    Strict mode でのフォールバック削除後、設定が必須になった際に使用される。
    """
    def __init__(self, key: str, message: str | None = None) -> None:
        msg = message or (
            f"Required configuration '{key}' is missing. "
            f"Please set it via environment variable or configuration file."
        )
        super().__init__(msg, {"key": key})
        self.key = key
```

**エクスポート**: `src/noveler/domain/exceptions/__init__.py` に追加済み

### 3. ConfigurationServiceAdapter 更新

**ファイル**: `src/noveler/infrastructure/adapters/configuration_service_adapter.py`

#### 変更された全メソッド:

1. **`get(key, default=None)`**
   - ERROR mode: `default=None` の場合に `MissingConfigurationError` 送出
   - WARNING mode: fallback時に警告ログ出力
   - OFF mode: 従来通りの動作（警告なし）

2. **`get_project_root()`**
   - ERROR mode: `MissingConfigurationError("project_root")` 送出
   - WARNING mode: `"."` へのfallback時に警告
   - OFF mode: 従来通り `"."` を返す

3. **`get_environment()`**
   - ERROR mode: `MissingConfigurationError("environment")` 送出
   - WARNING mode: `"development"` へのfallback時に警告
   - OFF mode: 従来通り `"development"` を返す

4. **`get_api_config(service_name)`**
   - ERROR mode: `MissingConfigurationError(f"api.{service_name}")` 送出
   - WARNING mode: 空辞書 `{}` へのfallback時に警告
   - OFF mode: 従来通り `{}` を返す

5. **`get_database_config()`, `get_logging_config()`, `get_feature_flags()`**
   - 同様のパターンで各設定に対応

#### 実装パターン:

```python
# Fallback handling with strict mode
if self._strict_config.is_config_strict():
    raise MissingConfigurationError(
        key,
        f"Configuration key '{key}' not found in strict mode. "
        f"Please set it via environment variable or configuration file."
    )
elif self._strict_config.should_warn_on_config_fallback():
    self._logger.warning(
        "[config] Configuration key '%s' not found, using fallback default: %s",
        key, default
    )

return self._fallback_config.get(key, default)
```

### 4. 環境変数設定ドキュメント

**ファイル**: `.env.example`

```bash
# =============================================================================
# Configuration Service Strict Mode
# =============================================================================

# Controls fallback behavior for configuration value resolution
# Values: off | warning | error
#   - off:     Fallback allowed without warnings (default, legacy behavior)
#   - warning: Fallback allowed but logged as warning (migration phase)
#   - error:   Fallback forbidden, raises exceptions (target state)
#
# Migration path: off → warning → error
# Recommended for development: warning
# Recommended for CI/production: error
NOVELER_STRICT_CONFIG=warning
```

### 5. テスト検証

**ファイル**: `scripts/diagnostics/test_config_strict_mode.py`

#### テスト結果:

```
================================================================================
✓ All tests passed successfully!
================================================================================

Test 1: OFF mode - silent fallback to defaults
✓ get_project_root() returned: '.'
✓ get_environment() returned: 'development'
✓ get_database_config() returned: {}
✓ is_feature_enabled('nonexistent_feature') returned: False

Test 2: WARNING mode - fallback with warning logs
✓ get_project_root() returned: '.'
✓ get_environment() returned: 'development'
✓ get_database_config() returned: {}
✓ is_feature_enabled('nonexistent_feature') returned: False
[WARNING logs confirmed: 4 warnings logged]

Test 3: ERROR mode - raise MissingConfigurationError
✓ get_project_root() raised MissingConfigurationError
✓ get_environment() raised MissingConfigurationError
✓ get_database_config() raised MissingConfigurationError
✓ is_feature_enabled() raised MissingConfigurationError
✓ get() with default=None raised MissingConfigurationError
✓ get() with explicit default returned: 'fallback_value' (no exception, as expected)
```

### 6. ドキュメント更新

**ファイル**: `CLAUDE.md`

- Configuration Service strict mode セクション追加
- 環境変数 `NOVELER_STRICT_CONFIG` の説明
- フォールバック削除対象の詳細リスト
- エラー対処ガイド（`MissingConfigurationError` の解決方法）

---

## 動作確認

### 環境変数別の動作:

#### OFF mode (`NOVELER_STRICT_CONFIG=off`)
- 全てのfallbackが警告なしで動作
- 既存コードとの完全な後方互換性

#### WARNING mode (`NOVELER_STRICT_CONFIG=warning`) ← **推奨（移行フェーズ）**
- Fallback発動時に警告ログを出力
- ログ例:
  ```
  WARNING  [config] project_root not found, using fallback default: '.'
  WARNING  [config] environment not found, using fallback default: 'development'
  WARNING  [config] database config not found, using fallback default: {}
  ```
- フォールバック箇所の特定が容易

#### ERROR mode (`NOVELER_STRICT_CONFIG=error`) ← **目標（CI/本番）**
- 設定値が見つからない場合に即座に `MissingConfigurationError` 送出
- 設定不足を早期検出
- **注意**: `get(key, default=value)` で明示的なデフォルト値を指定すれば例外なし

---

## 移行ガイドライン

### Step 1: WARNING modeで影響範囲確認
```bash
NOVELER_STRICT_CONFIG=warning python -m pytest tests/
# 警告ログから設定不足箇所を特定
```

### Step 2: 設定値を明示的に指定
```python
# 環境変数で設定
export PROJECT_ROOT=/path/to/project
export ENVIRONMENT=development

# またはコード内で明示的なデフォルト値を指定
config.get("api.timeout", default=30)  # これはERROR modeでも例外なし
```

### Step 3: ERROR modeで最終検証
```bash
NOVELER_STRICT_CONFIG=error python -m pytest tests/
# 全テスト通過を確認
```

---

## 既知の制限事項

1. **`_wrapped_manager` が None の場合のみstrict mode適用**
   - `get_configuration_manager()` が成功すれば、そちらの動作に従う
   - strict modeは「fallback実装」にのみ適用

2. **`get(key, default=value)` は例外なし**
   - 明示的なデフォルト値が指定されている場合、ERROR modeでも例外を送出しない
   - これは意図的な設計（「デフォルト値を明示する」ことを推奨）

---

## 次のステップ

Phase 2.2 完了により、以下が達成されました:

✅ Configuration Service にstrict mode実装
✅ `NOVELER_STRICT_CONFIG` 環境変数サポート
✅ 全3モード（OFF/WARNING/ERROR）の動作確認
✅ テストスクリプトによる検証完了
✅ ドキュメント更新完了

### Phase 2.3 候補（今後の展開）:

1. **Repository層のfallback削除**
   - `YamlProjectInfoRepository` などのfallback処理
   - ファイル読み込み失敗時の空データ返却

2. **完全strict mode化（Phase 3）**
   - 全領域を ERROR mode にロック
   - CI環境でのstrict mode強制

3. **Fallback検出の自動化**
   - 静的解析でfallback箇所を自動検出
   - pre-commit hookでの検証

---

## 参考資料

- 初期棚卸し: `docs/migration/fallback_inventory.md`
- Phase 2.1 報告: `docs/migration/phase_2.1_completion_report.md`
- Strict Mode設計: `src/noveler/infrastructure/config/strict_mode_config.py`
- 例外定義: `src/noveler/domain/exceptions/base.py`
- 契約文書: `CLAUDE.md` § Strict Mode
