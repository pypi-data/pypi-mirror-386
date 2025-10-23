# word_count 仕様書

## SPEC-EPISODE-010: 文字数


## 1. 目的
小説の文字数を表現する不変の値オブジェクト。エピソードや作品全体の文字数を管理し、投稿サイトの制限や読者の期待に応える。

## 2. 前提条件
- DDD原則に基づく値オブジェクトとして実装
- 不変性（immutable）を保証
- 小説家になろうの仕様を考慮

## 3. 主要な振る舞い

### 3.1 文字数の制約
- **型**: 整数（int）のみ
- **範囲**: 0以上100,000以下
- **定数**:
  - `MAX_WORD_COUNT`: 100,000（1話の最大文字数）
  - `MIN_WORD_COUNT_FOR_EPISODE`: 1,000（推奨最小文字数）

### 3.2 算術演算
- **加算**: 文字数の合計（上限チェックあり）
- **減算**: 文字数の差（負の値は0に丸める）
- **比較**: 文字数の大小関係

### 3.3 文字数判定
- `is_sufficient_for_episode()`: エピソードとして十分な文字数か（1,000文字以上）
- `calculate_percentage(target)`: 目標文字数に対する達成率

### 3.4 文字列表現
- フォーマット: `{文字数:,}文字`
- 例: 1234 → "1,234文字"

## 4. インターフェース仕様

```python
@dataclass(frozen=True)
class WordCount:
    """文字数を表す値オブジェクト"""

    value: int  # 0-100,000の整数値

    MAX_WORD_COUNT = 100000
    MIN_WORD_COUNT_FOR_EPISODE = 1000

    def __post_init__(self) -> None:
        """バリデーション"""
        # 型チェック：整数のみ許可
        # 範囲チェック：0-100,000

    def is_sufficient_for_episode(self) -> bool:
        """エピソードとして十分な文字数か"""

    def calculate_percentage(self, target: "WordCount") -> float:
        """目標に対する達成率を計算"""

    def __str__(self) -> str:
        """文字列表現: "1,234文字" """
```

## 5. エラーハンドリング

### 5.1 TypeError
- 整数以外の値（float, str等）が渡された場合

### 5.2 ValueError
- 0未満の値が渡された場合
- 100,000を超える値が渡された場合
- 加算結果が100,000を超える場合

## 6. 使用例

```python
# 正常系
wc1 = WordCount(2500)
assert str(wc1) == "2,500文字"
assert wc1.is_sufficient_for_episode() == True

wc2 = WordCount(500)
assert wc2.is_sufficient_for_episode() == False

# 算術演算
wc3 = wc1 + wc2  # 2500 + 500 = 3000
assert wc3.value == 3000

wc4 = wc2 - wc1  # 500 - 2500 = 0（負は0に丸める）
assert wc4.value == 0

# 達成率計算
target = WordCount(5000)
assert wc1.calculate_percentage(target) == 50.0

# エラー系
WordCount(-1)      # ValueError: 0以上である必要があります
WordCount(100001)  # ValueError: 100000以下である必要があります
WordCount("1000")  # TypeError: 整数である必要があります
```

## 7. 実装メモ
- テストファイル: `tests/unit/domain/value_objects/test_word_count.py`
- 実装ファイル: `scripts/domain/value_objects/word_count.py`
- 作成日: 2025-01-21
- 更新日: 2025-07-23 (実装との整合性確認・更新)

## 8. 未決定事項
- [ ] 文字数カウント方法（改行・空白の扱い）
- [ ] なろうAPIとの文字数計算の整合性
- [ ] 作品全体の文字数上限（現在は1話単位）
