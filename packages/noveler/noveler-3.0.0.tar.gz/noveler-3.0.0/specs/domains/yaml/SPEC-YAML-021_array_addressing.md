---
spec_id: SPEC-YAML-021
status: draft
owner: quality-engineering
last_reviewed: 2025-10-01
category: YAML
tags: [validator, path_resolution, array_addressing, aggregation]
---
# SPEC-YAML-021: YAML配列アドレッシング機能仕様

## 1. 目的
- YAML検証器でドット区切りパスに配列ワイルドカード (`sections[*].hook`) をサポートする。
- 配列要素に対する数値集約 (min/max/avg) を提供し、ビジネスルール検証を強化する。
- パス解決を統一インターフェースで提供し、各種validator/adapterで再利用可能にする。

## 2. 前提条件
- 対象データはYAML/JSONでパース済みの辞書・配列構造である。
- パス文字列は UTF-8 で提供され、`.` で階層区切り、`[*]` で配列全要素を指す。
- 配列インデックスは 0-based で、負のインデックス (Python式) はサポートしない。

## 3. 主要な振る舞い

### 3.1 パス解決
- **ドット区切りパス**: `metadata.title` → `data["metadata"]["title"]`
- **配列インデックス**: `episodes[0].title` → `data["episodes"][0]["title"]`
- **配列ワイルドカード**: `episodes[*].word_count` → 全エピソードの word_count を配列で返却
- **ネストされた配列**: `chapters[*].sections[*].hook` → 多次元配列を平坦化して返却

### 3.2 数値集約
- `PathResolver.aggregate(path, "min")` → パスで取得した数値配列の最小値
- `PathResolver.aggregate(path, "max")` → 最大値
- `PathResolver.aggregate(path, "avg")` → 平均値 (小数第2位で丸め)
- 非数値要素は警告を出力し、スキップする。

### 3.3 エラーハンドリング
- パスが存在しない場合は `None` を返却し、エラーログを出力。
- 配列ワイルドカード適用時に配列でない要素があれば `PathResolutionError` を発行。
- 集約関数適用時に空配列の場合は `None` を返却。

## 4. インターフェース仕様

### 4.1 PathResolver クラス

```python
@dataclass(frozen=True)
class PathSegment:
    """パスセグメント"""
    key: str
    is_wildcard: bool = False
    index: int | None = None

class PathResolver:
    """YAML/JSON構造のパス解決器"""

    @staticmethod
    def parse_path(path: str) -> list[PathSegment]:
        """パス文字列をセグメントにパース

        Args:
            path: "sections[*].hook" 形式のパス

        Returns:
            PathSegment のリスト

        Raises:
            ValueError: パース不可能な構文
        """

    @staticmethod
    def resolve(data: dict | list, path: str) -> Any:
        """パスを解決して値を取得

        Args:
            data: 対象データ構造
            path: ドット区切りパス

        Returns:
            解決された値 (ワイルドカード使用時は配列)

        Raises:
            PathResolutionError: 解決失敗
        """

    @staticmethod
    def aggregate(data: dict | list, path: str, func: Literal["min", "max", "avg"]) -> float | None:
        """数値配列を集約

        Args:
            data: 対象データ構造
            path: ドット区切りパス
            func: 集約関数名

        Returns:
            集約結果 (該当要素なしの場合 None)

        Raises:
            PathResolutionError: 解決失敗
            AggregationError: 非数値要素を含む
        """
```

### 4.2 使用例

```python
data = {
    "episodes": [
        {"title": "第1話", "word_count": 4500, "sections": [{"hook": True}, {"hook": False}]},
        {"title": "第2話", "word_count": 5200, "sections": [{"hook": True}]},
        {"title": "第3話", "word_count": 3800, "sections": [{"hook": False}]}
    ]
}

resolver = PathResolver()

# 単一値
title = resolver.resolve(data, "episodes[0].title")  # → "第1話"

# ワイルドカード
word_counts = resolver.resolve(data, "episodes[*].word_count")  # → [4500, 5200, 3800]

# ネストワイルドカード
hooks = resolver.resolve(data, "episodes[*].sections[*].hook")  # → [True, False, True, False]

# 集約
min_wc = resolver.aggregate(data, "episodes[*].word_count", "min")  # → 3800
max_wc = resolver.aggregate(data, "episodes[*].word_count", "max")  # → 5200
avg_wc = resolver.aggregate(data, "episodes[*].word_count", "avg")  # → 4500.0
```

## 5. 実装方針

### 5.1 パーサー
- 正規表現で `key[index]` または `key[*]` をパース
- セグメントリストに変換し、再帰的にトラバース

### 5.2 トラバーサル
- `is_wildcard=True` のセグメントで配列を展開
- ネストされたワイルドカードは `itertools.chain.from_iterable` で平坦化

### 5.3 集約
- `statistics` モジュールの `mean`, `min`, `max` を使用
- 非数値は警告ログを出力してスキップ

## 6. テスト観点

### 6.1 ユニットテスト
- 単一階層のワイルドカード解決
- ネストされたワイルドカード解決
- 存在しないパスのエラーハンドリング
- 集約関数の正確性 (空配列/非数値含む)

### 6.2 統合テスト
- YAMLValidatorAdapter との連携
- ビジネスルール検証での使用
- 大規模データでのパフォーマンス

## 7. 品質基準

### 7.1 パフォーマンス
- 10階層ネストまで 100ms 以内で解決
- 1000要素配列のワイルドカード解決を 500ms 以内で完了

### 7.2 エラーメッセージ
- パス解決失敗時に失敗箇所を明示 (例: `episodes[*].invalid_field`)
- 集約時の非数値要素を警告ログに記録

### 7.3 後方互換性
- 既存のドット区切りパス解決に影響しない
- ワイルドカード未使用時のオーバーヘッドは 5% 以内

## 8. 依存関係

```python
from dataclasses import dataclass
from typing import Any, Literal
from statistics import mean
from itertools import chain
import re
import logging
```

## 9. 将来の拡張

- [ ] フィルタ構文: `episodes[*:word_count>4000].title` (条件付きワイルドカード)
- [ ] スライス構文: `episodes[0:5].title` (範囲指定)
- [ ] 関数合成: `episodes[*].sections[*].hook | count(true)` (パイプライン)
- [ ] JSONPath/XPath 互換モード (設定で切り替え)

## 10. 参照

- TODO.md line 17-21: Arrays addressing in validator (v2.1)
- SPEC-YAML-020: YAML検証アダプター仕様書 (line 352-363 パス解決の記述)
