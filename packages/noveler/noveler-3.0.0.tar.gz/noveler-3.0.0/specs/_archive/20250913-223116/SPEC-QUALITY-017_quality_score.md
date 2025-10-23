# SPEC-QUALITY-017: quality_score 仕様書

## SPEC-QUALITY-007: 品質スコア


## 1. 目的
品質スコアを表現する不変の値オブジェクト。エピソードや文章の品質を0-100の整数値で表現し、グレード判定や比較を可能にする。

## 2. 前提条件
- DDD原則に基づく値オブジェクトとして実装
- 不変性（immutable）を保証
- 型安全性を確保

## 3. 主要な振る舞い

### 3.1 スコア値の制約
- **型**: 整数（int）のみ
- **範囲**: 0以上100以下
- **理由**: 品質評価は整数パーセンテージで十分な精度

### 3.2 グレード判定
| スコア範囲 | グレード | 説明 |
|-----------|---------|------|
| 90-100 | S | 優秀 |
| 80-89 | A | 良好 |
| 70-79 | B | 標準 |
| 60-69 | C | 要改善 |
| 0-59 | D | 不十分 |

### 3.3 比較演算
- 大小比較（<, >, <=, >=）をサポート
- 等価比較（==, !=）をサポート
- ハッシュ可能（セットや辞書のキーとして使用可能）

## 4. インターフェース仕様

```python
@dataclass(frozen=True)
class QualityScore:
    """品質スコアを表す値オブジェクト"""

    value: int  # 0-100の整数値

    def __post_init__(self) -> None:
        """バリデーション"""
        # 型チェック：整数のみ許可
        # 範囲チェック：0-100

    def get_grade(self) -> str:
        """グレード（S/A/B/C/D）を取得"""

    def is_passing(self, threshold: int = 70) -> bool:
        """閾値を超えているかチェック"""

    def __str__(self) -> str:
        """文字列表現: "85点" """
```

## 5. エラーハンドリング

### 5.1 DomainException
- 整数以外の値（float, str等）が渡された場合
- 0未満の値が渡された場合
- 100を超える値が渡された場合

## 6. 使用例

```python
# 正常系
score = QualityScore(85)  # OK
assert score.value == 85
assert score.get_grade() == "A"
assert str(score) == "85点"

# エラー系
QualityScore(85.5)  # DomainException: 整数である必要があります
QualityScore(-1)    # DomainException: 0以上である必要があります
QualityScore(101)   # DomainException: 100以下である必要があります
```

## 7. 実装メモ
- テストファイル: `tests/unit/domain/value_objects/test_quality_score.py`
- 実装ファイル: `scripts/domain/value_objects/quality_score.py`
- 作成日: 2025-01-21（仕様書後付け作成）

## 8. 未決定事項
- [ ] 小数点対応の必要性（現在は整数のみ）
- [ ] グレード境界値の妥当性
- [ ] 国際化対応（"点" → "points"）
