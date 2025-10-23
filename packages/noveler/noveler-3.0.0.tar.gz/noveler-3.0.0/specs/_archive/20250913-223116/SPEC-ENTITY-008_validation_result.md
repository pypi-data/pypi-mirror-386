# ValidationResult 値オブジェクト仕様書

## SPEC-QUALITY-010: 検証結果


## 1. 目的
ファイルやコンテンツの検証結果を表現する値オブジェクト。検証で発見された問題をレベル別に管理し、複数の検証結果のマージをサポート。

## 2. 前提条件
- すべての値オブジェクトは不変（frozen=True）
- dataclassのfieldを使用してデフォルト値を設定
- エラー、警告、情報の3段階で問題を分類

## 3. 主要コンポーネント

### 3.1 列挙型（Enum）

#### ValidationLevel（検証レベル）
- ERROR: エラー（必須項目の不足など）
- WARNING: 警告（推奨項目の不足など）
- INFO: 情報（改善提案など）

### 3.2 値オブジェクト

#### ValidationIssue
- **必須フィールド**: level, message
- **オプションフィールド**: field_path="", suggestion=""
- **説明**:
  - level: 問題の重要度レベル
  - message: 問題の説明
  - field_path: 問題のあるフィールドのパス（例: "chapters[0].title"）
  - suggestion: 修正方法の提案

#### ValidationResult
- **必須フィールド**: is_valid
- **デフォルトフィールド**: issues=[], validated_fields={}
- **プロパティ**:
  - has_errors: エラーの有無
  - has_warnings: 警告の有無
  - error_count: エラー数
  - warning_count: 警告数
- **メソッド**:
  - get_errors(): エラーレベルの問題のみ取得
  - get_warnings(): 警告レベルの問題のみ取得
  - merge(other): 他の検証結果とマージ

### 3.3 マージ動作
- is_validは両方がTrueの場合のみTrue
- issuesは両方のリストを結合
- validated_fieldsは両方の辞書をマージ（後勝ち）

## 4. 使用例
```python
# 検証問題の作成
error = ValidationIssue(
    level=ValidationLevel.ERROR,
    message="タイトルが未設定です",
    field_path="title",
    suggestion="タイトルを設定してください"
)

warning = ValidationIssue(
    level=ValidationLevel.WARNING,
    message="説明が短すぎます",
    field_path="description",
    suggestion="100文字以上の説明を推奨します"
)

# 検証結果の作成
result = ValidationResult(
    is_valid=False,
    issues=[error, warning],
    validated_fields={"author": "作者名"}
)

# プロパティの確認
print(result.has_errors)      # True
print(result.error_count)     # 1
print(result.warning_count)   # 1

# 検証結果のマージ
other_result = ValidationResult(is_valid=True, issues=[])
merged = result.merge(other_result)
print(merged.is_valid)        # False（片方がFalseのため）
```

## 5. 実装チェックリスト
- [x] ValidationLevel列挙型の定義
- [x] ValidationIssue値オブジェクトの定義
- [x] ValidationResult値オブジェクトの定義
- [x] プロパティメソッドの実装
- [x] フィルタリングメソッドの実装
- [x] マージメソッドの実装
- [ ] テストケース作成
