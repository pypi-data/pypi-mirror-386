# SPEC-QUALITY-018: QualityThreshold 値オブジェクト仕様書

## SPEC-QUALITY-008: 品質閾値


## 1. 目的
品質チェックにおける各種閾値を管理し、値の妥当性を保証する値オブジェクト

## 2. 前提条件
- 名前は空文字列不可
- 値は指定された範囲内
- 値オブジェクトとして不変性を保証（frozen=True）
- 最小値 ≤ 最大値の関係を保証

## 3. 主要な振る舞い

### 3.1 初期化と検証
- **入力**:
  - name: 閾値の名前（文字列）
  - value: 現在の値（float）
  - min_value: 最小値（float）
  - max_value: 最大値（float）
- **処理**:
  - 名前の空文字列チェック
  - 最小値・最大値の関係チェック
  - 値の範囲チェック
- **出力**: QualityThresholdインスタンス
- **例外**:
  - ValueError（名前が空の場合）
  - ValueError（最小値 > 最大値の場合）
  - ValueError（値が範囲外の場合）

### 3.2 値の更新
- **入力**: new_value（float）
- **処理**: 新しい値で新規インスタンスを作成
- **出力**: 新しいQualityThresholdインスタンス
- **例外**: ValueError（新しい値が範囲外の場合）

### 3.3 文字列表現
- **入力**: なし
- **処理**: 人間が読みやすい形式で情報を整形
- **出力**: "名前: 値 (範囲: 最小値-最大値)" 形式の文字列

## 4. 使用例
```python
# 品質スコアの閾値
quality_score = QualityThreshold(
    name="品質スコア",
    value=80.0,
    min_value=0.0,
    max_value=100.0
)

# ひらがな比率の閾値
hiragana_ratio = QualityThreshold(
    name="ひらがな比率",
    value=0.40,
    min_value=0.0,
    max_value=1.0
)

# 値の更新
new_score = quality_score.update_value(85.0)
```

## 5. 実装チェックリスト
- [x] 名前の空文字列検証
- [x] 最小値・最大値の関係検証
- [x] 値の範囲検証
- [x] 不変性の保証（frozen=True）
- [x] 値更新メソッドの実装
- [x] 文字列表現の実装
- [ ] テストケース作成
