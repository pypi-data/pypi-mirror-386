---
spec_id: SPEC-CONFIG-002
status: draft
owner: bamboocity
last_reviewed: 2025-09-18
category: CONFIG
tags: [configuration, templates, internationalization]
requirements:
  - REQ-CONFIG-TEMPLATE-001
---
# SPEC-CONFIG-002: ファイル名テンプレート管理機能仕様書

## 1. 概要

### 1.1 目的
現在ハードコードされているファイル名（`プロジェクト設定.yaml`等）を、`.novelerrc.yaml`での設定ベース管理に変更し、国際化とカスタマイズを可能にする。

### 1.2 対象コンポーネント
- `.novelerrc.yaml`: ファイル名テンプレート設定
- `ConfigurationManager`: ファイル名取得機能追加
- 全リポジトリクラス: 設定ベースファイル名参照

### 1.3 要件紐付け
| 要件ID | 説明 | 対応セクション |
| --- | --- | --- |
| REQ-CONFIG-TEMPLATE-001 | ファイル名の設定ベース管理 | §2, §3 |

## 2. アーキテクチャ設計

### 2.1 レイヤー構成
```yaml
domain:
  - FileTemplateRepository: ファイル名テンプレート取得インターフェース
  - FileTemplate: ファイル名テンプレートの値オブジェクト

application:
  - FileTemplateService: ファイル名解決サービス

infrastructure:
  - YamlFileTemplateRepository: .novelerrc.yamlからテンプレート読み込み
  - ConfigurationManager: ファイル名取得API追加
```

### 2.2 設定形式
```yaml
# .novelerrc.yaml
file_templates:
  project_config: "プロジェクト設定.yaml"
  episode_management: "話数管理.yaml"
  quality_rules: "執筆品質ルール.yaml"
  project_fallback: "project.yaml"

# 国際化対応（将来実装）
locales:
  ja:
    project_config: "プロジェクト設定.yaml"
  en:
    project_config: "project_config.yaml"
```

## 3. 機能仕様

### 3.1 FileTemplateService
```python
class FileTemplateService:
    """ファイル名テンプレート解決サービス"""

    def get_filename(self, template_key: str) -> str:
        """テンプレートキーからファイル名を取得"""

    def get_project_config_filename(self) -> str:
        """プロジェクト設定ファイル名を取得"""

    def get_episode_management_filename(self) -> str:
        """話数管理ファイル名を取得"""
```

### 3.2 設定キー定義
| キー | デフォルト値 | 説明 |
| --- | --- | --- |
| `project_config` | `プロジェクト設定.yaml` | プロジェクト設定ファイル |
| `episode_management` | `話数管理.yaml` | 話数管理ファイル |
| `quality_rules` | `執筆品質ルール.yaml` | 品質ルールファイル |
| `project_fallback` | `project.yaml` | 代替プロジェクトファイル |

### 3.3 フォールバック動作
1. `.novelerrc.yaml`から読み込み試行
2. 失敗時はデフォルト値を使用
3. エラーログ出力（1回のみ）

## 4. 実装仕様

### 4.1 段階的移行戦略
**Phase 1**: `YamlProjectConfigRepository`の設定ベース化
```python
# 修正前
self.config_filename = "プロジェクト設定.yaml"

# 修正後
self.config_filename = self._get_filename("project_config")
```

**Phase 2**: 各リポジトリクラスの順次移行
- 影響度の高いクラスから優先実装
- 1クラスずつテスト・コミット

### 4.2 ConfigurationManager拡張
```python
class ConfigurationManager:
    def get_file_template(self, template_key: str) -> str:
        """ファイル名テンプレート取得"""

    def get_project_config_filename(self) -> str:
        """プロジェクト設定ファイル名取得"""
```

## 5. エラー処理

### 5.1 エラーコード定義
| コード | 条件 | 対応 |
| --- | --- | --- |
| FT-001 | .novelerrc.yaml読み込み失敗 | デフォルト値で継続、警告ログ |
| FT-002 | 無効なテンプレートキー | デフォルト値で継続、エラーログ |
| FT-003 | テンプレート設定不正 | デフォルト値で継続、エラーログ |

### 5.2 フォールバック戦略
- 設定読み込み失敗時はデフォルト値を使用
- アプリケーション動作への影響を最小化
- エラー情報は適切にログ出力

## 6. テスト仕様

### 6.1 単体テスト
```python
class TestFileTemplateService:
    def test_get_filename_with_valid_key(self):
        """有効なキーでファイル名取得"""

    def test_get_filename_with_invalid_key(self):
        """無効なキー時のフォールバック"""

    def test_configuration_fallback(self):
        """設定ファイル不正時のフォールバック"""
```

### 6.2 統合テスト
- 実際の`.novelerrc.yaml`での動作確認
- 既存機能への影響確認
- エラーケースでの安定性確認

## 7. 移行計画

### 7.1 後方互換性
- 既存の`.novelerrc.yaml`はそのまま動作
- 新しい設定がない場合はデフォルト値で動作
- 段階的移行により影響を最小化

### 7.2 移行順序
1. `FileTemplateService`基盤実装
2. `YamlProjectConfigRepository`移行
3. その他リポジトリクラス移行
4. 統合テスト・品質確認

## 8. 非機能要件

### 8.1 性能要件
- ファイル名取得処理は既存性能を維持
- 設定読み込みはキャッシュ化で高速化

### 8.2 保守性要件
- 新しいファイルタイプの追加が容易
- 設定キーの命名規則を統一

---

本仕様書は REQ-CONFIG-TEMPLATE-001 の準拠を保証する。実装完了時は関連する全ドキュメントを同期更新すること。


## 9. Project-level Settings (writing)

本仕様では、各プロジェクトの話単位ターゲット文字数（下限/上限）を「プロジェクト設定.yaml」から取得し、共通基盤で一元解決する。

### 9.1 設定ファイルと探索順
- 正式名: `プロジェクト設定.yaml`（プロジェクトルート直下）
- 規定ファイルが見つからない/不正な場合はエラー（致命）。実行は中断し、QC-009/QC-010 を返す。

### 9.2 スキーマ（抜粋・YAML）
```yaml
writing:
  episode:
    target_length:
      min: 6000   # 下限（chars）
      max: 10000  # 上限（chars）
```

- 単位は「文字数（chars）」であり語数ではない。
- バリデーション: `min >= 1000`, `max <= 20000`, `min < max`。

### 9.3 解決レイヤ（ConfigResolver）
- API: `get_target_length(project_root) -> {min:int, max:int, source:str}`
- 参照優先度: (1) プロジェクト設定のみ（`プロジェクト設定.yaml`）。その他の経路は禁止。
- ログ: 欠落・不正時は WARN を 1回発行（code: `CFG-001`/`CFG-002`）。
- キャッシュ: 5分 or ファイル更新で無効化。

### 9.4 テンプレートへの注入
- 変数名: `{target_min_chars}`, `{target_max_chars}`
- 対象テンプレート（例）:
  - `templates/quality/checks/check_step11_rhythm_tempo.yaml`
  - `templates/quality/checks/check_step12_final_quality_approval.yaml`
- 値が未設定/不正でフォールバックした場合、`execution_result.metadata.config_snapshot.source` に `default` を記録し、WARN を残す。
