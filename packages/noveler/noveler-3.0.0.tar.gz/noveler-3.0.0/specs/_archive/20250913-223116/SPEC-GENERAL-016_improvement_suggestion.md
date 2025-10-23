# SPEC-GENERAL-016: ImprovementSuggestion 値オブジェクト仕様書

## SPEC-QUALITY-009: 改善提案


## 1. 目的
品質記録活用システムにおける個人化された改善提案を表現する値オブジェクト。執筆者の傾向に基づいた具体的な改善アクションを提供。

## 2. 前提条件
- 値オブジェクトとして不変性を保証（frozen=True）
- 全フィールドの厳格な検証を実施
- 優先度・インパクト・信頼度の評価基準を明確化

## 3. 主要な振る舞い

### 3.1 初期化と検証
- **必須フィールド**:
  - category: 改善カテゴリ（任意文字列）
  - priority: 優先度（'high', 'medium', 'low'のいずれか）
  - title: タイトル（1-100文字）
  - description: 説明（1-500文字）
  - specific_actions: 具体的アクションリスト（最低1つ、各200文字以内）
  - estimated_impact: 推定インパクト（0.0-10.0）
  - confidence: 信頼度（0.0-1.0）

### 3.2 検証ルール
- **priority**: 'high', 'medium', 'low'のみ許可
- **title**: 空白不可、100文字以内
- **description**: 空白不可、500文字以内
- **specific_actions**:
  - 最低1つ必要
  - 各アクションは空白不可、200文字以内
- **estimated_impact**: 0.0 ≤ value ≤ 10.0
- **confidence**: 0.0 ≤ value ≤ 1.0

### 3.3 ビジネスメソッド
- **優先度判定**:
  - is_high_priority(): priority == 'high'
  - is_medium_priority(): priority == 'medium'
  - is_low_priority(): priority == 'low'
- **評価メソッド**:
  - is_high_impact(threshold=7.0): estimated_impact >= threshold
  - is_reliable(threshold=0.7): confidence >= threshold
- **集計メソッド**:
  - get_priority_score(): high=3, medium=2, low=1
  - get_action_count(): len(specific_actions)
  - get_suggestion_summary(): 提案の要約辞書を返す

## 4. 使用例
```python
suggestion = ImprovementSuggestion(
    category="basic_writing_style",
    priority="high",
    title="句読点の使い方を改善",
    description="句読点の使用頻度が低く、文章が読みにくくなっています",
    specific_actions=[
        "長い文章は適切な位置で句点で区切る",
        "読点を使って文の構造を明確にする"
    ],
    estimated_impact=8.5,
    confidence=0.85
)

# 評価
print(suggestion.is_high_priority())  # True
print(suggestion.is_high_impact())    # True
print(suggestion.is_reliable())       # True
print(suggestion.get_priority_score())  # 3
```

## 5. 実装チェックリスト
- [x] 不変性の保証（frozen=True）
- [x] 全フィールドの検証メソッド実装
- [x] 優先度判定メソッド
- [x] インパクト・信頼度評価メソッド
- [x] 集計・要約メソッド
- [ ] テストケース作成
