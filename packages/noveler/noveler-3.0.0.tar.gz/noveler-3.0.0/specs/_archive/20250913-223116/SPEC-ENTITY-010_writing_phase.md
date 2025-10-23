# WritingPhase 列挙型仕様書

## 1. 目的
執筆フェーズと公開ステータスを管理する列挙型。執筆プロセスの各段階と公開状態を明確に定義。

## 2. 前提条件
- Enumクラスを継承
- 文字列値を使用（JSONシリアライズ可能）

## 3. 主要コンポーネント

### 3.1 WritingPhase（執筆フェーズ）
- **DRAFT**: 下書き ("draft")
- **REVISION**: 推敲 ("revision")
- **FINAL_CHECK**: 最終チェック ("final_check")
- **PUBLISHED**: 公開済み ("published")

### 3.2 PublicationStatus（公開ステータス）
- **UNPUBLISHED**: 未公開 ("unpublished")
- **SCHEDULED**: 公開予定 ("scheduled")
- **PUBLISHED**: 公開済み ("published")
- **WITHDRAWN**: 公開停止 ("withdrawn")

## 4. 使用例
```python
# 執筆フェーズの使用
phase = WritingPhase.DRAFT
print(phase.value)  # "draft"
print(phase.name)   # "DRAFT"

# 公開ステータスの使用
status = PublicationStatus.SCHEDULED
print(status.value)  # "scheduled"

# 値からEnumを取得
phase = WritingPhase("draft")
status = PublicationStatus("published")
```

## 5. 実装チェックリスト
- [x] WritingPhase列挙型の定義
- [x] PublicationStatus列挙型の定義
- [x] 各値の文字列表現
- [ ] テストケース作成
