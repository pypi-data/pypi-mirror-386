# SPEC-GENERAL-030: ProgressStatus 値オブジェクト群仕様書

## SPEC-WORKFLOW-001: 進捗ステータス


## 1. 目的
タスクやプロセスの進捗状況と次のアクションを管理する値オブジェクト群。状態遷移の妥当性検証と次のアクションの定義を提供。

## 2. 前提条件
- ProgressStatusは列挙型として定義
- NextActionは不変値オブジェクト（frozen=True）
- 状態遷移ルールを厳格に管理
- TimeEstimation値オブジェクトとの連携

## 3. 主要コンポーネント

### 3.1 ProgressStatus（列挙型）
- **状態**:
  - NOT_STARTED: 未開始
  - IN_PROGRESS: 進行中
  - COMPLETED: 完了
  - NEEDS_REVIEW: 要確認
  - BLOCKED: 阻害
- **メソッド**:
  - emoji(): 各状態に対応する絵文字を返す
  - can_transition_to(target_status): 状態遷移の妥当性をチェック

### 3.2 許可される状態遷移
- NOT_STARTED → IN_PROGRESS, BLOCKED
- IN_PROGRESS → COMPLETED, NEEDS_REVIEW, BLOCKED
- COMPLETED → NEEDS_REVIEW
- NEEDS_REVIEW → IN_PROGRESS, COMPLETED
- BLOCKED → IN_PROGRESS, NOT_STARTED

### 3.3 NextAction（値オブジェクト）
- **必須フィールド**: title, command, time_estimation
- **オプションフィールド**: priority（デフォルト: "medium"）
- **検証**:
  - titleは空でない文字列
  - commandは空でない文字列
  - priorityは["high", "medium", "low"]のいずれか
- **メソッド**:
  - display_text(): 表示用テキスト生成

## 4. 使用例
```python
# 進捗ステータスの使用
status = ProgressStatus.NOT_STARTED
print(status.emoji())  # ⚪
print(status.can_transition_to(ProgressStatus.IN_PROGRESS))  # True
print(status.can_transition_to(ProgressStatus.COMPLETED))    # False

# 次のアクションの定義
from domain.value_objects.time_estimation import TimeEstimation

next_action = NextAction(
    title="プロット作成",
    command="novel plot master",
    time_estimation=TimeEstimation(hours=2, minutes=30),
    priority="high"
)
print(next_action.display_text())  # プロット作成 (所要時間: 2時間30分)
```

## 5. 実装チェックリスト
- [x] ProgressStatus列挙型の定義
- [x] emoji()メソッドの実装
- [x] can_transition_to()メソッドの実装
- [x] NextAction値オブジェクトの定義
- [x] 必須フィールドの検証
- [x] display_text()メソッドの実装
- [ ] テストケース作成
