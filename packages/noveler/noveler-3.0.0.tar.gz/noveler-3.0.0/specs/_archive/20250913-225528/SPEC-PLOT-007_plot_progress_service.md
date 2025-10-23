---
spec_id: SPEC-PLOT-007
status: canonical
owner: bamboocity
last_reviewed: 2025-09-13
category: PLOT
sources: [REQ]
tags: [plot]
---
# SPEC-PLOT-007: PlotProgressService 仕様書

## SPEC-PLOT-002: プロット進捗管理


## 1. 目的

PlotProgressServiceは、小説プロジェクトにおけるプロット作成の進捗状況を分析し、次に取るべきアクションを提案するドメインサービスです。DDD原則に完全準拠し、リポジトリパターンを使用してファイルI/Oを分離し、純粋なドメインロジックによる進捗管理を実現します。

## 2. 前提条件

### 2.1 依存関係
- `PlotProgressRepository`: プロット情報の永続化を担当するリポジトリ
- `ProgressReport`: 進捗レポートを表すエンティティ
- `ProgressStatus`: 進捗状況を表すEnum
- `NextAction`: 次のアクションを表す値オブジェクト
- `WorkflowStageType`: ワークフロー段階を表すEnum
- `TimeEstimation`: 時間見積もりを表す値オブジェクト

### 2.2 アーキテクチャ要件
- **DDD準拠**: ドメインロジックとインフラストラクチャの完全分離
- **リポジトリパターン**: データアクセスの抽象化
- **依存性逆転**: インフラストラクチャがドメインに依存

### 2.3 環境要件
- Python 3.9以上
- プロジェクトディレクトリ構造が標準フォーマットに準拠

## 3. 主要な振る舞い

### 3.1 プロジェクト進捗分析
```python
def analyze_project_progress(project_id: str) -> ProgressReport
```
- **目的**: プロジェクト全体の進捗状況を包括的に分析
- **処理フロー**:
  1. リポジトリからマスタープロット情報を取得
  2. 章別プロット情報を取得・分析
  3. 話別プロット情報を取得・分析
  4. 各段階の完成度を計算
  5. 全体完了率を重み付きで算出
  6. 次のアクションを提案
  7. 統合されたProgressReportを生成

### 3.2 マスタープロット状況判定
```python
def _determine_master_status(master_data: dict | None) -> ProgressStatus
```
- **目的**: マスタープロットの完成度を評価
- **判定基準**:
  - **COMPLETED**: 完成度80%以上
  - **IN_PROGRESS**: 完成度30%以上
  - **NEEDS_REVIEW**: 完成度30%未満
  - **NOT_STARTED**: データなし

### 3.3 章別プロット状況判定
```python
def _determine_chapters_status(chapters: list[dict]) -> ProgressStatus
```
- **目的**: 章別プロットの総合的な完成度を評価
- **処理フロー**:
  1. 各章の完成度を個別に計算
  2. 平均完成度を算出
  3. 統合ステータスを決定

### 3.4 全体完了率計算
```python
def _calculate_overall_completion(stage_statuses: dict[WorkflowStageType, ProgressStatus]) -> int
```
- **目的**: 重み付きによる全体完了率の精密計算
- **重み配分**:
  - **マスタープロット**: 30%
  - **章別プロット**: 40%
  - **話別プロット**: 30%
- **ステータス変換**:
  - **NOT_STARTED**: 0%
  - **NEEDS_REVIEW**: 30%
  - **IN_PROGRESS**: 50%
  - **COMPLETED**: 100%

### 3.5 次のアクション提案
```python
def _suggest_next_actions(stage_statuses: dict[WorkflowStageType, ProgressStatus], project_id: str) -> list[NextAction]
```
- **目的**: 進捗状況に基づいた具体的なアクション提案
- **提案ロジック**:
  1. マスタープロット未完成 → 完成優先
  2. 章別プロット進行中 → 未完了章の特定・完成支援
  3. 章別プロット未着手 → 第1章から開始提案
  4. 話別プロット未着手 → 第1話詳細作成提案
  5. 全て完了 → 執筆開始提案

### 3.6 進捗サマリー生成
```python
def get_completion_summary(project_id: str) -> str
```
- **目的**: 人間が読みやすい進捗サマリーの生成
- **出力形式**:
  - 全体完了率の表示
  - 段階別状況の視覚化
  - 推奨アクションの具体的提示

## 4. 入出力仕様

### 4.1 入力データ形式

#### プロジェクトID
```python
project_id: str  # プロジェクトの一意識別子
```

#### リポジトリから取得するデータ
```python
# マスタープロットデータ
master_data: dict | None = {
    "title": str,
    "overall_structure": dict,
    "characters": list,
    "world_setting": dict,
    "completion_score": float  # リポジトリで計算
}

# 章別プロットデータ
chapters: list[dict] = [
    {
        "chapter_number": int,
        "title": str,
        "plot_summary": str,
        "key_events": list,
        "completion_score": float
    }
]

# 話別プロットデータ
episodes: list[dict] = [
    {
        "episode_number": int,
        "title": str,
        "plot_details": str,
        "scene_breakdown": list,
        "completion_score": float
    }
]
```

### 4.2 出力データ形式

#### ProgressReport（エンティティ）
```python
class ProgressReport:
    project_root: str                                       # プロジェクトルート（リファクタリング版）
    overall_completion: int                                 # 全体完了率(0-100)
    stage_statuses: dict[WorkflowStageType, ProgressStatus] # 段階別状況
    next_actions: list[NextAction]                          # 次のアクション
    created_at: str                                         # 作成日時（リファクタリング版）
    metadata: dict[str, Any]                                # メタデータ

    # ビジネスロジックメソッド
    def is_completed() -> bool                              # プロジェクト完了判定
    def get_completed_stages() -> list[WorkflowStageType]   # 完了段階の取得
    def recommend_next_action() -> NextAction | None        # 推奨アクション
    def calculate_estimated_remaining_time() -> TimeEstimation  # 残作業時間見積もり
    def generate_display() -> str                           # 表示用テキスト生成
```

#### NextAction（値オブジェクト）
```python
@dataclass(frozen=True)
class NextAction:
    title: str                      # アクションタイトル
    command: str                    # 実行コマンド
    time_estimation: str            # 見積もり時間（例: "60分"）
    priority: int = 1               # 優先度（1-5、デフォルト1）

    # 検証メソッド
    def __post_init__():            # タイトルとコマンドの必須チェック、優先度範囲検証
```

#### 進捗サマリー（文字列）
```
📊 プロット作成進捗: 67%

📋 段階別状況:
  ✅ 全体構成: COMPLETED
  🔄 章別プロット: IN_PROGRESS
  ⚪ 話数別プロット: NOT_STARTED

🔄 推奨される次のステップ:
  1. 第2章のプロットを完成させましょう (所要時間: 60分)
     コマンド: novel plot chapter 2
```

## 5. エラーハンドリング

### 5.1 リポジトリアクセスエラー
- **対象**: プロジェクトデータの取得失敗
- **対応**: デフォルト値の提供とエラーログ出力
- **復旧**: 部分的なデータでも分析を継続

### 5.2 データ不整合エラー
- **対象**: 期待される形式でないデータ
- **対応**: データの正規化と警告出力
- **復旧**: 利用可能なデータのみで分析

### 5.3 完成度計算エラー
- **対象**: 無効なスコア値
- **対応**: スコアの範囲チェックと補正
- **復旧**: デフォルトスコアによる継続処理

## 6. パフォーマンス要件

### 6.1 応答時間
- **標準分析**: 200ms以内
- **大規模プロジェクト**: 1秒以内
- **キャッシュ活用**: 繰り返し分析で50%短縮

### 6.2 メモリ使用量
- **基本動作**: 10MB以内
- **大規模プロジェクト**: 50MB以内
- **リポジトリキャッシュ**: 効率的なデータ管理

### 6.3 同時実行
- **スレッドセーフ**: 複数プロジェクトの並行分析をサポート
- **リソース競合**: リポジトリレベルでの排他制御

## 7. セキュリティ考慮事項

### 7.1 プロジェクトアクセス制御
- **アクセス範囲**: 指定されたプロジェクトディレクトリのみ
- **パス検証**: ディレクトリトラバーサル攻撃の防止

### 7.2 データ整合性
- **入力検証**: プロジェクトIDの形式チェック
- **データ検証**: 取得データの構造チェック

### 7.3 機密情報保護
- **ログ制限**: プロジェクト内容をログに記録しない
- **エラーメッセージ**: システム内部情報の漏洩防止

## 8. 実装チェックリスト

### 8.1 コア機能
- [x] プロジェクト進捗分析
- [x] マスタープロット状況判定
- [x] 章別プロット状況判定
- [x] 話別プロット状況判定
- [x] 全体完了率計算
- [x] 次のアクション提案
- [x] 進捗サマリー生成

### 8.2 DDD準拠
- [x] リポジトリパターンの実装
- [x] ドメインロジックの純粋性
- [x] 依存性逆転の実現
- [x] インフラストラクチャ分離

### 8.3 品質保証
- [x] 入力検証の実装
- [x] エラーハンドリングの実装
- [x] パフォーマンス最適化
- [x] セキュリティ対策の実装

### 8.4 統合テスト
- [x] 各種進捗パターンの動作確認
- [x] エラーケースの処理確認
- [x] 大規模プロジェクトでの動作確認
- [x] リポジトリとの統合動作確認

### 8.5 ドキュメント
- [x] 仕様書の作成
- [x] APIドキュメントの更新
- [x] 使用例の提供
- [x] DDD設計ドキュメント

## 実装完了状況（2025年7月22日更新）

### オリジナル版
- **完成度**: TDD GREEN段階完了
- **ファイル**: `plot_progress_service.py`
- **特徴**: Pathとdatetimeを使用した実装

### リファクタリング版
- **完成度**: DDD完全準拠版
- **ファイル**: `plot_progress_service_refactored.py`
- **改善点**:
  - Path型からstr型への変更（ドメイン層の技術的依存削減）
  - datetimeからstrへの変更（シンプル化）
  - より純粋なドメインロジック実装

### 関連エンティティ・値オブジェクト
- **ProgressStatus（Enum）**: 状態管理と絵文字マッピング、状態遷移検証
- **WorkflowStageType（Enum）**: ワークフロー段階定義、実行順序管理
- **TimeEstimation**: 作業時間見積もり、ファクトリメソッド、演算サポート
- **ProgressReport**: ビジネスロジックを含む進捗レポートエンティティ

## 9. 使用例

### 9.1 基本的な進捗分析
```python
# リポジトリの初期化
repository = YamlPlotProgressRepository(project_root)

# サービスの初期化
service = PlotProgressService(repository)

# 進捗分析の実行
report = service.analyze_project_progress("my-novel-project")

# 結果の表示
print(f"全体完了率: {report.overall_completion}%")
for stage, status in report.stage_statuses.items():
    print(f"{stage.value}: {status.value}")
```

### 9.2 進捗サマリーの取得
```python
# 人間が読みやすいサマリーの生成
summary = service.get_completion_summary("my-novel-project")
print(summary)
```

### 9.3 次のアクションの取得
```python
# 進捗分析の実行
report = service.analyze_project_progress("my-novel-project")

# 次のアクションの表示
for action in report.next_actions:
    print(f"優先度 {action.priority}: {action.description}")
    print(f"実行コマンド: {action.command}")
    print(f"見積もり時間: {action.estimated_time.display_text()}")
```

## 10. 運用監視

### 10.1 メトリクス
- **分析実行回数**: 機能の使用状況
- **平均応答時間**: パフォーマンス指標
- **エラー発生率**: システムの安定性
- **プロジェクト完了率分布**: 利用パターン

### 10.2 ログ出力
- **INFO**: 正常な進捗分析の実行
- **WARN**: データ不整合の検出
- **ERROR**: リポジトリアクセスエラー

### 10.3 アラート条件
- **応答時間**: 2秒を超えた場合
- **エラー率**: 15%を超えた場合
- **メモリ使用量**: 100MBを超えた場合

## 11. 拡張性

### 11.1 新しいプロット段階の追加
- **WorkflowStageType**: 新しい段階の定義
- **重み配分**: `_calculate_overall_completion`の更新
- **アクション提案**: `_suggest_next_actions`の拡張

### 11.2 カスタム完成度計算
- **完成度アルゴリズム**: リポジトリレベルでの実装
- **プロジェクト固有ルール**: 設定による調整
- **AI支援評価**: 将来的な拡張ポイント

### 11.3 リアルタイム進捗追跡
- **ファイル監視**: 変更検知による自動更新
- **キャッシュ無効化**: 効率的なデータ更新
- **通知システム**: 進捗変化の通知
