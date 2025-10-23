# YAML自動整形・検証機能仕様書

## 1. 概要

### 1.1 目的
- YAMLファイルの保存時に自動的に整形・検証を実行
- 一貫性のあるYAMLフォーマットを維持
- 構文エラーや品質問題を事前に防止
- 既存コードへの影響を最小限に抑える

### 1.2 スコープ
- 対象: すべてのYAML保存処理（話数管理、品質記録、設定ファイルなど）
- ライブラリ: ruamel.yaml（整形）+ yamllint（検証）
- 実装範囲: インフラストラクチャ層のリポジトリ実装

## 2. 技術仕様

### 2.1 既存実装の活用
すでに以下のモジュールが実装済みのため、これらを最大限活用する：

```python
# src/noveler/infrastructure/utils/yaml_formatter.py
- YAMLFormatter クラス（整形・検証機能実装済み）
- format_and_save_yaml() 関数（簡易インターフェース）

# src/noveler/infrastructure/utils/yaml_utils.py
- YAMLHandler クラス（use_formatter パラメータ対応済み）
```

### 2.2 整形・検証ルール

#### 2.2.1 yamllint設定（プロジェクト標準）
```yaml
extends: default
rules:
  line-length:
    max: 120
    level: warning
  indentation:
    spaces: 2
    indent-sequences: true
  comments:
    min-spaces-from-content: 2
  document-start: disable
  document-end: disable
  truthy:
    allowed-values: ['true', 'false', 'on', 'off']
  key-duplicates: enable
  empty-lines:
    max: 2
    max-start: 0
    max-end: 1
```

#### 2.2.2 ruamel.yaml設定
```python
yaml.preserve_quotes = True      # 引用符を保持
yaml.map_indent = 2             # マッピングのインデント
yaml.sequence_indent = 2        # シーケンスのインデント
yaml.width = 120               # 行幅制限
yaml.allow_unicode = True      # Unicode文字許可
yaml.encoding = 'utf-8'        # エンコーディング
```

## 3. 実装設計

### 3.1 段階的導入戦略

#### Phase 1: オプトイン方式（推奨）
```python
# 新規実装や更新時に明示的に有効化
YAMLHandler.save_yaml(
    file_path,
    data,
    use_formatter=True  # 明示的に有効化
)
```

#### Phase 2: 環境変数による制御
```python
# 環境変数で一括制御
NOVEL_YAML_AUTO_FORMAT=true  # デフォルト: false
```

#### Phase 3: デフォルト有効化（将来）
```python
# 十分な検証後、デフォルトで有効化
use_formatter=True  # デフォルト値として設定
```

### 3.2 既存コードの更新方針

#### 3.2.1 最小限の変更で対応
```python
# 既存: yaml.dump()を直接使用
yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

# 更新後: YAMLHandler経由に統一
from infrastructure.utils.yaml_utils import YAMLHandler

YAMLHandler.save_yaml(file_path, data, use_formatter=True)
```

#### 3.2.2 リポジトリクラスの更新例
```python
# YamlEpisodeRepository._save_episode_management()
def _save_episode_management(self, data: dict) -> None:
    """話数管理YAMLを保存"""
    path = self.management_dir / "話数管理.yaml"

    # 更新前
    # with open(path, "w", encoding="utf-8") as f:
    #     yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    # 更新後
    YAMLHandler.save_yaml(path, data, use_formatter=True)
```

### 3.3 エラーハンドリング

#### 3.3.1 グレースフルフォールバック
```python
def save_with_fallback(file_path: Path, data: dict) -> None:
    """整形に失敗した場合は通常の保存にフォールバック"""
    try:
        # まず整形付き保存を試行
        YAMLHandler.save_yaml(file_path, data, use_formatter=True)
    except Exception as e:
        # 失敗した場合は通常の保存
        logger.warning(f"YAML整形失敗、通常保存にフォールバック: {e}")
        YAMLHandler.save_yaml(file_path, data, use_formatter=False)
```

#### 3.3.2 検証エラーの通知
```python
def save_with_validation(file_path: Path, data: dict) -> tuple[bool, list[str]]:
    """保存と検証結果を返す"""
    success, messages = YAMLFormatter().save_yaml(
        file_path,
        data,
        validate=True,
        fix_style=True
    )

    if not success:
        # エラーをログに記録（保存は継続）
        for msg in messages:
            logger.error(f"YAML検証エラー: {msg}")

    return success, messages
```

## 4. 対象ファイルと優先度

### 4.1 高優先度（Phase 1で実装）
1. **品質記録系**
   - `YamlQualityRecordRepository`
   - `YamlEpisodeManagementRepository`
   - `YamlRevisionHistoryRepository`

2. **話数管理系**
   - `YamlEpisodeRepository`
   - `SimpleYamlEpisodeRepository`

### 4.2 中優先度（Phase 2で実装）
3. **設定ファイル系**
   - `QualityConfig`
   - `YamlQualityConfigRepository`
   - プロジェクト設定ファイル

### 4.3 低優先度（Phase 3で実装）
4. **その他のYAMLファイル**
   - テンプレートファイル
   - 分析結果ファイル
   - AIプロンプト設定

## 5. パフォーマンス考慮事項

### 5.1 キャッシング戦略
```python
class YAMLFormatterCache:
    """フォーマッターインスタンスのキャッシュ"""
    _formatters = {}

    @classmethod
    def get_formatter(cls, formatter_type: str = 'default') -> YAMLFormatter:
        if formatter_type not in cls._formatters:
            if formatter_type == 'episode':
                cls._formatters[formatter_type] = YAMLFormatter.create_episode_formatter()
            elif formatter_type == 'quality':
                cls._formatters[formatter_type] = YAMLFormatter.create_quality_formatter()
            else:
                cls._formatters[formatter_type] = YAMLFormatter()

        return cls._formatters[formatter_type]
```

### 5.2 大量処理時の最適化
```python
def bulk_save_yaml_files(files: list[tuple[Path, dict]]) -> dict[Path, tuple[bool, list[str]]]:
    """複数ファイルの一括保存"""
    formatter = YAMLFormatterCache.get_formatter()
    results = {}

    for file_path, data in files:
        # 検証は最初の1回のみ（パフォーマンス向上）
        validate = (len(results) == 0)
        success, messages = formatter.save_yaml(
            file_path,
            data,
            validate=validate,
            backup=False  # 大量処理時はバックアップ無効
        )
        results[file_path] = (success, messages)

    return results
```

## 6. 移行計画

### 6.1 実装手順
1. **Week 1**: YAMLHandlerの`use_formatter`パラメータ活用確認
2. **Week 2**: 高優先度リポジトリの更新（オプトイン）
3. **Week 3**: テスト実行と問題修正
4. **Week 4**: 中優先度リポジトリの更新
5. **Week 5**: 環境変数による制御追加
6. **Week 6**: ドキュメント更新と周知

### 6.2 後方互換性の保証
- 既存のYAMLファイルは読み込み可能
- `use_formatter=False`で従来の動作を維持
- 段階的な移行で影響を最小化

## 7. テスト計画

### 7.1 ユニットテスト
```python
def test_yaml_formatter_integration():
    """YAMLFormatter統合テスト"""
    # 1. 不正な形式のYAMLを作成
    bad_yaml = {
        'episodes': [
            {'number': 1, 'title': 'テスト',   'status': 'draft'},  # 余分なスペース
        ]
    }

    # 2. 整形付き保存
    path = Path('test.yaml')
    YAMLHandler.save_yaml(path, bad_yaml, use_formatter=True)

    # 3. 整形されたことを確認
    with open(path) as f:
        content = f.read()
    assert '  status: draft' in content  # 正しいインデント
```

### 7.2 統合テスト
- 各リポジトリクラスでの動作確認
- エラー時のフォールバック動作
- パフォーマンステスト（大量ファイル処理）

## 8. 監視とメトリクス

### 8.1 ログ出力
```python
# 整形実行時のログ
logger.info(f"YAML整形実行: {file_path}")
logger.debug(f"整形前サイズ: {before_size}, 整形後サイズ: {after_size}")

# エラー時のログ
logger.error(f"YAML整形エラー: {file_path}, エラー: {error}")
```

### 8.2 メトリクス収集
- 整形成功率
- 平均処理時間
- エラー発生頻度
- フォールバック発生回数

## 9. FAQ

### Q1: ruamel.yamlがインストールされていない環境では？
A: 自動的に通常のyaml.dump()にフォールバックします。

### Q2: 既存のコメントは保持されますか？
A: はい、ruamel.yamlはコメントを保持します。

### Q3: パフォーマンスへの影響は？
A: 単一ファイルで約10-20ms増加。大量処理時は最適化オプションを使用。

### Q4: カスタム整形ルールを追加できますか？
A: YAMLFormatter._fix_common_style_issues()をオーバーライドして対応可能。

## 10. 実装チェックリスト

- [ ] YAMLHandlerの既存実装確認
- [ ] 高優先度リポジトリの更新
- [ ] エラーハンドリングの実装
- [ ] ユニットテストの作成
- [ ] 統合テストの実行
- [ ] パフォーマンステスト
- [ ] ドキュメント更新
- [ ] チーム周知
