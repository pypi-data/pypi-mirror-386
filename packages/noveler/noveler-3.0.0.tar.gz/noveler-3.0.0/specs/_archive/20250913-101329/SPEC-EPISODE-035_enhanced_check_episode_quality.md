# 拡張エピソード品質チェックユースケース仕様書

## 概要
`EnhancedCheckEpisodeQualityUseCase`は、基本品質チェックに品質記録活用システムを統合し、学習データの蓄積と個人化された改善提案を提供するユースケースです。執筆者の傾向分析とトレンド把握による継続的な品質向上を支援します。

## クラス設計

### EnhancedCheckEpisodeQualityUseCase

**責務**
- 基本品質チェックとの統合
- 品質記録活用システムとの連携
- 学習データの蓄積・分析
- 個人化された改善提案の生成
- 執筆トレンドの分析

## データ構造

### EnhancedQualityCheckResult (DataClass)
```python
@dataclass(frozen=True)
class EnhancedQualityCheckResult:
    base_result: CheckEpisodeQualityResult              # 基本品質チェック結果
    improvement_suggestions: list[ImprovementSuggestion] | None = None  # 改善提案
    trend_analysis: dict[str, Any] | None = None        # トレンド分析
    learning_summary: dict[str, Any] | None = None      # 学習データ要約
```

**拡張データ内容**
- `improvement_suggestions`: 個人の執筆傾向に基づく具体的改善提案
- `trend_analysis`: 品質向上トレンド、カテゴリ別推移データ
- `learning_summary`: 蓄積された学習データの要約情報

## パブリックメソッド

### execute()

**シグネチャ**
```python
def execute(
    self,
    command: CheckEpisodeQualityCommand,
    episode_number: int,
    writing_time_minutes: int | None = None,
    revision_count: int | None = None,
    user_feedback: str | None = None,
    writing_environment: str | None = None,
    target_audience: str | None = None,
    writing_goal: str | None = None,
) -> EnhancedQualityCheckResult:
```

**目的**
基本品質チェックを実行し、結果を学習データとして蓄積・分析して、個人化された改善提案を生成する。

**引数**
- `command`: 基本品質チェックコマンド
- `episode_number`: エピソード番号
- `writing_time_minutes`: 執筆時間（分）※推定可能
- `revision_count`: 修正回数※推定可能
- `user_feedback`: ユーザーフィードバック
- `writing_environment`: 執筆環境（自宅、カフェ等）
- `target_audience`: ターゲット読者層
- `writing_goal`: 執筆目標

**戻り値**
- `EnhancedQualityCheckResult`: 拡張品質チェック結果

**処理フロー**
1. **基本品質チェック実行**: 標準的な品質検証
2. **カテゴリ別スコア抽出**: 品質レポートの分析
3. **問題分類**: エラー・警告・自動修正の分類
4. **改善率計算**: 前回エピソードからの品質向上度
5. **推定データ生成**: 未提供パラメータの推定
6. **学習データ蓄積**: 品質記録活用システムへの登録
7. **拡張結果生成**: 改善提案とトレンド分析

**成功パターン**
- 基本チェック成功 + 学習データ蓄積完了
- 改善提案の生成成功
- トレンド分析データの提供

**フォールバック**
- 基本チェック失敗時は拡張機能をスキップ
- 学習データ不足時は基本結果のみ提供

## プライベートメソッド

### _extract_category_scores()

**シグネチャ**
```python
def _extract_category_scores(self, report: QualityReport) -> dict[str, float]:
```

**目的**
品質レポートからカテゴリ別スコアを抽出・計算する。

**処理内容**
- 違反データのカテゴリ別集計
- スコア計算（100点満点 - 違反数×5点）
- 標準カテゴリでの正規化

**対象カテゴリ**
- `basic_writing_style`: 基本文章作法
- `story_structure`: 物語構造
- `character_description`: キャラクター描写
- `reader_experience`: 読者体験
- `technical_completion`: 技術的完成度

### _extract_issues()

**シグネチャ**
```python
def _extract_issues(self, report: QualityReport) -> tuple[list[str], list[str], list[str]]:
```

**目的**
品質レポートから問題を重要度別に分類する。

**戻り値**
- `tuple[エラー一覧, 警告一覧, 自動修正一覧]`

**分類基準**
- **エラー**: 重要度が"error"の違反
- **警告**: 重要度が"warning"の違反
- **自動修正**: `auto_fixable`フラグがTrueの違反

### _calculate_improvement()

**シグネチャ**
```python
def _calculate_improvement(
    self,
    current_scores: dict[str, float],
    previous_record: dict[str, Any] | None
) -> float:
```

**目的**
前回エピソードからの品質改善率を計算する。

**計算方法**
- カテゴリ別改善率の算出
- 改善率の平均値を返却
- 前回データがない場合は0.0

**改善率計算式**
```
改善率 = (今回スコア - 前回スコア) / 前回スコア × 100
```

### _estimate_writing_time()

**シグネチャ**
```python
def _estimate_writing_time(self, content: str) -> int:
```

**目的**
コンテンツから執筆時間を推定する（分単位）。

**推定方法**
- 1000文字あたり30分として計算
- 最低30分を保証
- 文字数ベースの線形推定

### _estimate_revision_count()

**シグネチャ**
```python
def _estimate_revision_count(self, report: QualityReport) -> int:
```

**目的**
品質レポートから修正回数を推定する。

**推定方法**
- 自動修正可能な違反：1回
- 手動修正が必要な違反：2回
- 合計値を修正回数として推定

## 依存関係

### アプリケーション層
- `CheckEpisodeQualityUseCase`: 基本品質チェックユースケース
- `QualityRecordEnhancementUseCase`: 品質記録活用ユースケース

### ドメイン層
- `QualityReport`: 品質レポートエンティティ
- `ImprovementSuggestion`: 改善提案値オブジェクト

### リポジトリ
- `QualityRecordEnhancementRepository`: 品質記録リポジトリ
- `EpisodeRepository`: エピソードリポジトリ（オプション）
- `WritingRecordRepository`: 執筆記録リポジトリ（オプション）

## 設計原則遵守

### DDD準拠
- ✅ ドメインロジックの適切な委譲
- ✅ 値オブジェクト（`ImprovementSuggestion`）の使用
- ✅ リポジトリパターンによるデータアクセス抽象化
- ✅ アプリケーションサービス間の適切な調整

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的なフォールバック処理
- ✅ 型安全な実装
- ✅ 不変オブジェクトの使用

## 使用例

```python
# 依存関係の準備
base_quality_check = CheckEpisodeQualityUseCase(...)
quality_enhancement = QualityRecordEnhancementUseCase(...)
quality_record_repo = YamlQualityRecordEnhancementRepository()

# ユースケース作成
enhanced_use_case = EnhancedCheckEpisodeQualityUseCase(
    base_quality_check_use_case=base_quality_check,
    quality_record_enhancement_use_case=quality_enhancement,
    quality_record_repository=quality_record_repo
)

# 基本的な拡張品質チェック
command = CheckEpisodeQualityCommand(
    project_id="sample_novel",
    content="エピソードの本文...",
    episode_file_path="/path/to/episode.md"
)

result = enhanced_use_case.execute(
    command=command,
    episode_number=5,
    writing_time_minutes=90,
    revision_count=3,
    user_feedback="キャラクターの感情表現を重視したい",
    writing_environment="自宅",
    target_audience="ライトノベル読者",
    writing_goal="日常シーンの魅力向上"
)

# 結果の活用
if result.base_result.success:
    print(f"基本品質スコア: {result.base_result.report.total_score}")

    if result.improvement_suggestions:
        print("個人化された改善提案:")
        for suggestion in result.improvement_suggestions:
            print(f"- {suggestion.category}: {suggestion.description}")

    if result.trend_analysis:
        trend_data = result.trend_analysis["trend_data"]
        print(f"品質トレンド: {trend_data}")

    if result.learning_summary:
        print(f"学習データ要約: {result.learning_summary}")

# 最小限の実行（推定パラメータ使用）
minimal_result = enhanced_use_case.execute(
    command=command,
    episode_number=6
)
```

## 学習データ活用

### 蓄積されるデータ
```python
quality_input = QualityCheckInput(
    project_name=str,                    # プロジェクト名
    episode_number=int,                  # エピソード番号
    category_scores=dict[str, float],    # カテゴリ別スコア
    errors=list[str],                    # エラー一覧
    warnings=list[str],                  # 警告一覧
    auto_fixes=list[str],                # 自動修正一覧
    improvement_from_previous=float,     # 前回からの改善率
    time_spent_writing=int,              # 執筆時間
    revision_count=int,                  # 修正回数
    user_feedback=str,                   # ユーザーフィードバック
    writing_environment=str,             # 執筆環境
    target_audience=str,                 # ターゲット読者層
    writing_goal=str,                    # 執筆目標
)
```

### 生成される分析結果
- **個人傾向分析**: よく発生する問題パターン
- **品質向上トレンド**: 時系列での品質変化
- **環境依存分析**: 執筆環境と品質の相関
- **目標達成度**: 設定した執筆目標の進捗

## エラーハンドリング

### 基本チェック失敗時
- 拡張機能をスキップして基本結果のみ返却
- エラー情報は基本結果に含まれる

### 学習データ不足時
- 改善提案なしで基本結果を提供
- 最低限の推定値を使用

### リポジトリアクセスエラー
- フォールバック処理で基本機能を継続
- エラーログの記録

## テスト観点

### 単体テスト
- 基本品質チェックとの統合
- カテゴリ別スコア抽出の正確性
- 改善率計算の妥当性
- 推定機能の動作
- フォールバック処理

### 統合テスト
- 品質記録活用システムとの連携
- 学習データの蓄積・取得
- 複数エピソードでのトレンド分析

## 品質基準

- **学習効果**: 継続使用による改善提案の精度向上
- **個人化**: ユーザー固有の執筆傾向に基づく提案
- **信頼性**: 基本機能の確実な動作保証
- **拡張性**: 新しい分析軸・メトリクスへの対応
- **ユーザビリティ**: 分かりやすい改善提案とトレンド表示
