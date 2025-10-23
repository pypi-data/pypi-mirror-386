# SPEC-GENERAL-003: 双方向対話確認ユースケース仕様書

## 概要
`BidirectionalInteractiveConfirmation`は、重要な操作に対してユーザーとシステム間で双方向の対話的確認を行うユースケースです。プロット変更、批量更新、破壊的操作などの実行前に、影響範囲の提示、詳細確認、段階的承認を提供し、安全で透明性の高い操作を実現します。

## クラス設計

### BidirectionalInteractiveConfirmation

**責務**
- 操作内容と影響範囲の詳細分析
- インタラクティブな確認ダイアログの生成
- 段階的な承認プロセスの管理
- 操作履歴とロールバック情報の記録
- 条件付き実行の制御
- 確認スキップ設定の管理

## データ構造

### ConfirmationType (Enum)
```python
class ConfirmationType(Enum):
    DESTRUCTIVE = "destructive"              # 破壊的操作
    BULK_UPDATE = "bulk_update"              # 一括更新
    PLOT_CHANGE = "plot_change"              # プロット変更
    PUBLISH = "publish"                      # 公開操作
    MIGRATION = "migration"                  # データ移行
    CONFIGURATION = "configuration"          # 設定変更
    QUALITY_OVERRIDE = "quality_override"    # 品質チェック上書き
```

### ConfirmationLevel (Enum)
```python
class ConfirmationLevel(Enum):
    SIMPLE = "simple"                        # 単純確認（Yes/No）
    DETAILED = "detailed"                    # 詳細確認（影響表示）
    STAGED = "staged"                        # 段階確認（複数ステップ）
    CRITICAL = "critical"                    # 重要確認（再入力要求）
```

### InteractiveConfirmationRequest (DataClass)
```python
@dataclass
class InteractiveConfirmationRequest:
    operation_type: ConfirmationType         # 操作タイプ
    operation_description: str               # 操作説明
    target_items: list[str]                  # 対象項目
    confirmation_level: ConfirmationLevel    # 確認レベル
    impact_analysis: dict[str, any] = {}     # 影響分析データ
    allow_skip: bool = False                 # スキップ許可フラグ
    require_reason: bool = False             # 理由入力要求フラグ
    timeout_seconds: int | None = None       # タイムアウト時間
    default_action: str = "cancel"           # デフォルトアクション
```

### InteractiveConfirmationResponse (DataClass)
```python
@dataclass
class InteractiveConfirmationResponse:
    confirmed: bool                          # 確認結果
    confirmation_id: str                     # 確認ID（履歴用）
    user_response: str                       # ユーザー応答
    reason: str | None = None                # 操作理由
    timestamp: datetime = None               # 確認時刻
    skip_future: bool = False                # 今後のスキップフラグ
    detailed_choices: dict[str, bool] = {}   # 詳細選択結果
    confirmation_log: str = ""               # 確認ログ
```

### ConfirmationDialog (DataClass)
```python
@dataclass
class ConfirmationDialog:
    title: str                               # ダイアログタイトル
    message: str                             # メインメッセージ
    impact_summary: str                      # 影響サマリー
    affected_items: list[str]                # 影響項目リスト
    warnings: list[str] = []                 # 警告メッセージ
    options: list[str] = []                  # 選択オプション
    required_input: str | None = None        # 必須入力項目
    help_text: str = ""                      # ヘルプテキスト
```

## パブリックメソッド

### request_confirmation()

**シグネチャ**
```python
def request_confirmation(self, request: InteractiveConfirmationRequest) -> InteractiveConfirmationResponse:
```

**目的**
指定された操作に対して適切なレベルの対話的確認を実行する。

**引数**
- `request`: 確認リクエスト情報

**戻り値**
- `InteractiveConfirmationResponse`: 確認結果

**処理フロー**
1. **影響分析**: 操作の影響範囲を詳細分析
2. **ダイアログ生成**: 確認レベルに応じたダイアログ作成
3. **ユーザー対話**: インタラクティブな確認プロセス
4. **応答検証**: ユーザー入力の妥当性確認
5. **履歴記録**: 確認内容と結果の記録
6. **結果返却**: 確認結果の構築

### create_confirmation_preview()

**シグネチャ**
```python
def create_confirmation_preview(
    self,
    operation_type: ConfirmationType,
    target_items: list[str]
) -> str:
```

**目的**
操作実行前のプレビューを生成する。

### get_confirmation_history()

**シグネチャ**
```python
def get_confirmation_history(
    self,
    operation_type: ConfirmationType | None = None,
    days_back: int = 30
) -> list[ConfirmationRecord]:
```

**目的**
過去の確認履歴を取得する。

### set_confirmation_preference()

**シグネチャ**
```python
def set_confirmation_preference(
    self,
    operation_type: ConfirmationType,
    preference: dict[str, any]
) -> None:
```

**目的**
特定操作タイプの確認設定を更新する。

## プライベートメソッド

### _analyze_operation_impact()

**シグネチャ**
```python
def _analyze_operation_impact(
    self,
    operation_type: ConfirmationType,
    target_items: list[str]
) -> dict[str, any]:
```

**目的**
操作の影響範囲を詳細に分析する。

**分析項目**
```python
impact_analysis = {
    "affected_files": list[str],            # 影響ファイル
    "affected_episodes": list[int],         # 影響エピソード
    "data_size": int,                       # データサイズ
    "reversible": bool,                     # 可逆性
    "backup_available": bool,               # バックアップ有無
    "dependencies": list[str],              # 依存関係
    "risk_level": str,                      # リスクレベル
    "estimated_time": int                   # 推定所要時間
}
```

### _create_dialog_for_level()

**シグネチャ**
```python
def _create_dialog_for_level(
    self,
    level: ConfirmationLevel,
    operation_type: ConfirmationType,
    impact_analysis: dict[str, any]
) -> ConfirmationDialog:
```

**目的**
確認レベルに応じた適切なダイアログを生成する。

**レベル別処理**
- **SIMPLE**: Yes/Noの単純確認
- **DETAILED**: 影響項目を表示した詳細確認
- **STAGED**: 複数ステップの段階的確認
- **CRITICAL**: パスワードや確認文字列の再入力要求

### _execute_interactive_confirmation()

**シグネチャ**
```python
def _execute_interactive_confirmation(
    self,
    dialog: ConfirmationDialog,
    level: ConfirmationLevel
) -> tuple[bool, str, dict[str, any]]:
```

**目的**
実際のユーザー対話を実行し、応答を取得する。

### _validate_user_response()

**シグネチャ**
```python
def _validate_user_response(
    self,
    response: str,
    level: ConfirmationLevel,
    required_input: str | None
) -> bool:
```

**目的**
ユーザー応答の妥当性を検証する。

### _record_confirmation()

**シグネチャ**
```python
def _record_confirmation(
    self,
    request: InteractiveConfirmationRequest,
    response: InteractiveConfirmationResponse
) -> None:
```

**目的**
確認履歴を記録する。

### _should_skip_confirmation()

**シグネチャ**
```python
def _should_skip_confirmation(
    self,
    operation_type: ConfirmationType,
    user_preferences: dict[str, any]
) -> bool:
```

**目的**
ユーザー設定に基づいて確認をスキップすべきか判定する。

## 確認ダイアログ例

### 破壊的操作の確認
```
=== 警告: 破壊的操作の確認 ===

実行しようとしている操作は元に戻せません。

操作: プロジェクトデータの完全削除
対象: fantasy_adventure

影響範囲:
- 原稿ファイル: 25件
- 設定ファイル: 8件
- 管理データ: 15件
- 合計サイズ: 2.3MB

⚠️ この操作は取り消せません
⚠️ バックアップは作成されません

本当に削除しますか？
確認のため「DELETE fantasy_adventure」と入力してください:
> _
```

### 一括更新の段階確認
```
=== ステップ 1/3: 更新対象の確認 ===

以下のエピソードの品質ステータスを更新します:

□ 第001話_冒険の始まり.md (現在: 下書き → 執筆中)
□ 第002話_出会い.md (現在: 下書き → 執筆中)
□ 第003話_最初の試練.md (現在: 下書き → 執筆中)

[Space]で選択/解除 [Enter]で次へ [Esc]でキャンセル

選択: 3/3件
```

### プロット変更の詳細確認
```
=== プロット変更の確認 ===

マスタープロットの変更を検出しました。

変更内容:
- 第3章の主要イベント順序を変更
- 新キャラクター「賢者エルダー」を追加
- クライマックスの展開を修正

影響を受ける要素:
📝 エピソード: 第15-20話の整合性確認が必要
🔗 伏線: F003, F007の配置見直しが必要
👥 キャラクター: 関係性の再検討が推奨

この変更を適用しますか？
[Y] はい、適用する
[N] いいえ、キャンセル
[D] 詳細を表示
[?] ヘルプ

選択: _
```

## 依存関係

### ドメインサービス
- `ImpactAnalyzer`: 操作影響の分析
- `ConfirmationValidator`: 確認応答の検証
- `RiskAssessor`: リスクレベルの評価

### リポジトリ
- `ConfirmationHistoryRepository`: 確認履歴の管理
- `UserPreferenceRepository`: ユーザー設定の管理
- `OperationLogRepository`: 操作ログの記録

### 外部サービス
- `InteractiveConsole`: コンソール対話の制御
- `NotificationService`: 重要操作の通知

## 設計原則遵守

### DDD準拠
- ✅ エンティティ（`ConfirmationRecord`）の適切な使用
- ✅ 値オブジェクト（列挙型）の活用
- ✅ ドメインサービスの適切な活用
- ✅ リポジトリパターンによるデータアクセス抽象化

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的なエラーハンドリング
- ✅ 型安全な実装
- ✅ 列挙型による型安全性

## 使用例

```python
# 依存関係の準備
impact_analyzer = ImpactAnalyzer()
confirmation_validator = ConfirmationValidator()
risk_assessor = RiskAssessor()
history_repo = ConfirmationHistoryRepository()
preference_repo = UserPreferenceRepository()
operation_log_repo = OperationLogRepository()
interactive_console = InteractiveConsole()
notification_service = NotificationService()

# ユースケース作成
use_case = BidirectionalInteractiveConfirmation(
    impact_analyzer=impact_analyzer,
    confirmation_validator=confirmation_validator,
    risk_assessor=risk_assessor,
    confirmation_history_repository=history_repo,
    user_preference_repository=preference_repo,
    operation_log_repository=operation_log_repo,
    interactive_console=interactive_console,
    notification_service=notification_service
)

# 破壊的操作の確認
delete_request = InteractiveConfirmationRequest(
    operation_type=ConfirmationType.DESTRUCTIVE,
    operation_description="プロジェクト 'old_project' の完全削除",
    target_items=["old_project"],
    confirmation_level=ConfirmationLevel.CRITICAL,
    require_reason=True
)

response = use_case.request_confirmation(delete_request)

if response.confirmed:
    print(f"削除が承認されました: {response.confirmation_id}")
    print(f"理由: {response.reason}")
    # 実際の削除処理を実行
else:
    print("削除がキャンセルされました")

# 一括更新の段階確認
bulk_update_request = InteractiveConfirmationRequest(
    operation_type=ConfirmationType.BULK_UPDATE,
    operation_description="複数エピソードの品質ステータス更新",
    target_items=["第001話", "第002話", "第003話"],
    confirmation_level=ConfirmationLevel.STAGED,
    impact_analysis={
        "affected_episodes": 3,
        "current_status": "下書き",
        "new_status": "執筆中",
        "reversible": True
    }
)

bulk_response = use_case.request_confirmation(bulk_update_request)

if bulk_response.confirmed:
    print("選択されたエピソード:")
    for item, selected in bulk_response.detailed_choices.items():
        if selected:
            print(f"  - {item}")

# プロット変更の詳細確認
plot_change_request = InteractiveConfirmationRequest(
    operation_type=ConfirmationType.PLOT_CHANGE,
    operation_description="マスタープロットの構造変更",
    target_items=["20_プロット/全体構成.yaml"],
    confirmation_level=ConfirmationLevel.DETAILED,
    impact_analysis={
        "affected_episodes": [15, 16, 17, 18, 19, 20],
        "affected_foreshadowing": ["F003", "F007"],
        "risk_level": "medium",
        "backup_available": True
    }
)

plot_response = use_case.request_confirmation(plot_change_request)

# 確認履歴の取得
history = use_case.get_confirmation_history(
    operation_type=ConfirmationType.DESTRUCTIVE,
    days_back=7
)

print(f"\n過去7日間の破壊的操作: {len(history)}件")
for record in history:
    print(f"- {record.timestamp}: {record.operation_description}")
    print(f"  確認: {'承認' if record.confirmed else 'キャンセル'}")

# ユーザー設定の更新
use_case.set_confirmation_preference(
    operation_type=ConfirmationType.QUALITY_OVERRIDE,
    preference={
        "skip_for_minor_changes": True,
        "always_show_impact": True,
        "default_timeout": 30
    }
)
```

## 確認レベルの選択基準

### SIMPLE（単純確認）
- 影響範囲が限定的
- 可逆的な操作
- リスクレベルが低い

### DETAILED（詳細確認）
- 複数項目への影響
- 中程度のリスク
- 影響の可視化が重要

### STAGED（段階確認）
- 大量の項目が対象
- 個別選択が必要
- 複数の承認ステップ

### CRITICAL（重要確認）
- 不可逆的な操作
- 高リスク
- 誤操作防止が最重要

## タイムアウト処理

```python
def _handle_timeout(self, default_action: str) -> bool:
    if default_action == "cancel":
        return False
    elif default_action == "confirm":
        # セキュリティ上、重要操作では自動確認しない
        if self.confirmation_level == ConfirmationLevel.CRITICAL:
            return False
        return True
    return False
```

## エラーハンドリング

### ユーザー中断
```python
try:
    user_input = self.interactive_console.get_input(prompt, timeout)
except KeyboardInterrupt:
    logger.info("ユーザーが確認をキャンセルしました")
    return InteractiveConfirmationResponse(
        confirmed=False,
        confirmation_id=generate_confirmation_id(),
        user_response="INTERRUPTED",
        timestamp=datetime.now()
    )
```

### 無効な入力
```python
if not self._validate_user_response(user_input, level, required_input):
    retry_count += 1
    if retry_count > MAX_RETRIES:
        return InteractiveConfirmationResponse(
            confirmed=False,
            confirmation_id=generate_confirmation_id(),
            user_response="INVALID_INPUT_EXCEEDED",
            timestamp=datetime.now()
        )
    # 再入力を要求
```

## テスト観点

### 単体テスト
- 各確認レベルの動作
- 影響分析の正確性
- タイムアウト処理
- 入力検証ロジック
- 履歴記録機能

### 統合テスト
- 実際の対話フローのシミュレーション
- 複数ステップの確認プロセス
- 設定の永続化と読み込み
- 通知サービスとの連携

## 品質基準

- **安全性**: 重要操作の誤実行防止
- **透明性**: 影響範囲の明確な提示
- **使いやすさ**: 直感的な対話インターフェース
- **柔軟性**: 操作タイプに応じた確認レベル
- **追跡可能性**: 全確認操作の履歴記録
