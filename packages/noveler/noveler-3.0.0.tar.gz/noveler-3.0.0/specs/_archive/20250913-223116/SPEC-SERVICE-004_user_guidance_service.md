# UserGuidanceService 仕様書

## SPEC-WORKFLOW-002: ユーザーガイダンス


## 1. 目的

UserGuidanceServiceは、エラー状況や作業段階に応じて、ユーザーに最適なガイダンスとステップを提供するドメインサービスです。技術的なエラーを理解しやすいメッセージに変換し、具体的な解決手順を段階的に提示することで、ユーザーの作業効率を大幅に向上させます。

## 2. 前提条件

### 2.1 依存関係
- `ErrorContext`: エラーの詳細情報を格納するエンティティ
- `UserGuidance`: ガイダンス情報を表すエンティティ
- `GuidanceStep`: 個別のガイダンスステップを表すエンティティ
- `GuidanceType`: ガイダンスタイプを表すEnum
- `WorkflowStageType`: ワークフロー段階を表すEnum
- `TimeEstimation`: 時間見積もりを表す値オブジェクト

### 2.2 環境要件
- Python 3.9以上
- `templates/`ディレクトリにテンプレートファイルが存在すること
- CLI統合システムが利用可能であること

## 3. 主要な振る舞い

### 3.1 前提条件不足時のガイダンス生成
```python
def generate_prerequisite_guidance(error_context: ErrorContext) -> UserGuidance
```
- **目的**: 前提条件が不足している場合に、必要なファイル作成のガイダンスを生成
- **処理フロー**:
  1. エラーコンテキストから不足ファイルリストを取得
  2. 各不足ファイルに対してファイル作成ステップを生成
  3. 適切なテンプレートとCLIコマンドを選択
  4. 統合されたガイダンスオブジェクトを返却

### 3.2 成功時の次ステップガイダンス生成
```python
def generate_success_guidance(context: dict[str, Any]) -> UserGuidance
```
- **目的**: 作業完了後に次に取るべきアクションを提示
- **処理フロー**:
  1. 完了した段階から次の段階を特定
  2. 次段階のメインステップを生成
  3. オプショナルな改善ステップを追加
  4. 全体的なガイダンスを構築

### 3.3 執筆者プロファイル対応ガイダンス
```python
def provide_guidance_for_profile(writer_profile: dict[str, Any]) -> UserGuidance
```
- **目的**: 執筆者の経験レベルに応じたカスタマイズされたガイダンス
- **対応レベル**:
  - **初心者**: 基礎的な手順を詳細に説明
  - **中級者以上**: 効率的な次ステップを提示

### 3.4 エラー解決ガイダンス
```python
def provide_error_guidance(error_context: Any) -> UserGuidance
```
- **目的**: エラーの内容に応じた具体的な解決策を提示
- **特徴**:
  - エラーメッセージの内容分析
  - 具体的な改善例の提示
  - 自動修正コマンドの提供

### 3.5 進捗レポート対応ガイダンス
```python
def provide_progress_guidance(progress_report: Any) -> UserGuidance
```
- **目的**: 現在の進捗状況に基づいた次のアクション提案
- **処理フロー**:
  1. 進捗レポートから未完了段階を特定
  2. 優先度に基づいてアクションを提案
  3. 実行可能なコマンドを提供

## 4. 入出力仕様

### 4.1 入力データ形式

#### ErrorContext
```python
class ErrorContext:
    error_type: str                     # エラータイプ
    missing_files: List[str]           # 不足ファイルリスト
    affected_stage: WorkflowStageType  # 影響を受ける段階
    context_info: Dict[str, Any]       # 追加コンテキスト情報
```

#### 成功コンテキスト
```python
{
    "completed_stage": WorkflowStageType,
    "project_type": str,
    "user_experience": str
}
```

#### 執筆者プロファイル
```python
{
    "experience_level": str,  # "beginner", "intermediate", "advanced"
    "genre_preference": str,
    "writing_goals": List[str]
}
```

### 4.2 出力データ形式

#### UserGuidance
```python
class UserGuidance:
    guidance_type: GuidanceType        # ガイダンスタイプ
    title: str                         # タイトル
    steps: List[GuidanceStep]          # ステップリスト
    target_stage: WorkflowStageType    # 対象段階
    context_info: Dict[str, Any]       # コンテキスト情報
```

#### GuidanceStep
```python
class GuidanceStep:
    step_number: int                   # ステップ番号
    title: str                         # ステップタイトル
    description: str                   # 詳細説明
    command: str                       # 実行コマンド
    time_estimation: TimeEstimation    # 時間見積もり
    prerequisites: List[str]           # 前提条件
```

## 5. エラーハンドリング

### 5.1 入力検証エラー
- **`ValueError`**: 前提条件エラーでない場合
- **対応策**: エラーコンテキストのタイプを事前に検証

### 5.2 データ不整合エラー
- **`ValueError`**: 必須フィールドが不足している場合
- **対応策**: デフォルト値の提供とグレースフルデグラデーション

### 5.3 テンプレート不在エラー
- **処理**: テンプレートが存在しない場合は代替コマンドを提供
- **フォールバック**: 手動作成の指示メッセージを表示

## 6. パフォーマンス要件

### 6.1 応答時間
- **標準処理**: 100ms以内
- **複雑なガイダンス生成**: 500ms以内

### 6.2 メモリ使用量
- **テンプレートマッピング**: 初期化時に1回だけ作成
- **ガイダンス生成**: 一時的なオブジェクトの効率的な管理

### 6.3 同時実行
- **スレッドセーフ**: 読み取り専用の設定データは共有可能
- **リソース競合**: テンプレートマッピングは不変オブジェクトとして扱う

## 7. セキュリティ考慮事項

### 7.1 パス注入攻撃対策
- **ファイルパス検証**: 許可されたディレクトリ内のファイルのみ参照
- **テンプレートパス**: 予め定義されたテンプレートのみ使用

### 7.2 コマンドインジェクション対策
- **コマンド検証**: 予め定義されたコマンドパターンのみ使用
- **パラメータサニタイズ**: ユーザー入力を直接コマンドに含めない

### 7.3 情報漏洩対策
- **エラーメッセージ**: システム内部情報を含まない
- **ログ出力**: 機密情報をログに記録しない

## 8. 実装チェックリスト

### 8.1 コア機能
- [x] 前提条件不足時のガイダンス生成
- [x] 成功時の次ステップガイダンス生成
- [x] 執筆者プロファイル対応ガイダンス
- [x] エラー解決ガイダンス
- [x] 進捗レポート対応ガイダンス

### 8.2 データ管理
- [x] テンプレートマッピングの初期化
- [x] コマンドテンプレートの管理
- [x] ファイル情報の取得・管理
- [x] 段階情報の取得・管理

### 8.3 品質保証
- [x] 入力検証の実装
- [x] エラーハンドリングの実装
- [x] パフォーマンス最適化
- [x] セキュリティ対策の実装

### 8.4 統合テスト
- [x] 各種ガイダンス生成の動作確認
- [x] エラーケースの処理確認
- [x] 異なる執筆者レベルでの動作確認
- [x] CLI統合機能の動作確認

### 8.5 ドキュメント
- [x] 仕様書の作成
- [x] APIドキュメントの更新
- [x] 使用例の提供
- [x] トラブルシューティングガイド

## 実装完了状況（2025年7月22日更新）

### 実装概要
- **ファイル**: `user_guidance_service.py`（402行）
- **完成度**: 完全実装済み
- **DDD準拠**: ドメインサービスとして適切に実装

### 実装された機能

#### コアメソッド
- **`generate_prerequisite_guidance`**: 前提条件不足時のガイダンス生成
- **`generate_success_guidance`**: 成功時の次ステップガイダンス生成
- **`provide_guidance_for_profile`**: 執筆者プロファイル対応ガイダンス
- **`provide_error_guidance`**: エラー解決ガイダンス
- **`provide_progress_guidance`**: 進捗レポート対応ガイダンス

#### 内部ヘルパーメソッド
- **`_create_file_creation_step`**: ファイル作成ステップ生成
- **`_create_next_stage_step`**: 次段階のステップ生成
- **`_create_optional_improvement_step`**: オプショナル改善ステップ生成
- **`_get_file_info`**: ファイル情報マッピング取得
- **`_get_stage_info`**: ワークフロー段階情報取得
- **`_get_cli_command_for_file`**: ファイル別CLIコマンド生成
- **`_get_cli_command_for_stage`**: 段階別CLIコマンド生成
- **`_get_next_stage`**: 次段階の特定
- **`_get_stage_japanese_name`**: 段階名の日本語変換

#### テンプレートマッピング
- **企画書**: 企画書テンプレート.yaml（45分）
- **キャラクター**: キャラクター設定テンプレート.yaml（60分）
- **世界観**: 世界観設定テンプレート.yaml（90分）
- **全体構成**: マスタープロットテンプレート.yaml（120分）

#### CLIコマンドマッピング
- **企画書作成**: `novel init project`
- **キャラクター作成**: `novel create character`
- **世界観作成**: `novel create world`
- **マスタープロット**: `novel plot master`
- **章別プロット**: `novel plot chapter 1`
- **話数別プロット**: `novel plot episode 1`

#### ガイダンスタイプ
- **PREREQUISITE_MISSING**: 前提条件不足
- **SUCCESS_NEXT_STEPS**: 成功後の次ステップ
- **ERROR_RESOLUTION**: エラー解決
- **BEGINNER_FRIENDLY**: 初心者向け
- **PROGRESS_BASED**: 進捗ベース

### 依存関係
- **UserGuidance**: ガイダンス情報エンティティ（188行）
  - 完了率計算、次ステップ取得、表示テキスト生成
- **GuidanceStep**: ガイダンスステップエンティティ
  - 実行可能性判定、前提条件チェック、表示テキスト生成
- **GuidanceType**: ガイダンスタイプEnum（6種類）
- **ErrorContext**: エラーコンテキストエンティティ（144行）
  - 重要度判定、ユーザー経験レベル取得、メッセージ生成
- **WorkflowStageType**: ワークフロー段階Enum（3段階）
- **TimeEstimation**: 時間見積もり値オブジェクト（63行）
- **ProgressStatus**: 進捗ステータスEnum（5状態）

## 9. 使用例

### 9.1 前提条件不足時の使用例
```python
# エラーコンテキストの作成
error_context = ErrorContext(
    error_type="PREREQUISITE_MISSING",
    missing_files=["10_企画/企画書.yaml"],
    affected_stage=WorkflowStageType.MASTER_PLOT
)

# ガイダンスの生成
service = UserGuidanceService()
guidance = service.generate_prerequisite_guidance(error_context)

# 結果の表示
print(f"Title: {guidance.title}")
for step in guidance.steps:
    print(f"Step {step.step_number}: {step.title}")
    print(f"Command: {step.command}")
    print(f"Time: {step.time_estimation.display_text()}")
```

### 9.2 成功時の使用例
```python
# 成功コンテキストの作成
context = {
    "completed_stage": WorkflowStageType.MASTER_PLOT,
    "project_type": "fantasy"
}

# ガイダンスの生成
guidance = service.generate_success_guidance(context)

# 次のステップの表示
for step in guidance.steps:
    print(f"Next: {step.description}")
    print(f"Command: {step.command}")
```

## 10. 運用監視

### 10.1 メトリクス
- **ガイダンス生成回数**: 機能の使用状況
- **エラー発生率**: システムの安定性
- **平均応答時間**: パフォーマンス指標

### 10.2 ログ出力
- **INFO**: 正常なガイダンス生成
- **WARN**: 想定外の入力データ
- **ERROR**: システムエラー

### 10.3 アラート条件
- **応答時間**: 1秒を超えた場合
- **エラー率**: 10%を超えた場合
- **メモリ使用量**: 想定値を大幅に超えた場合
