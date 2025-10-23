# LearningSession エンティティ仕様書

**作成日**: 2025-01-22
**バージョン**: 1.0
**カテゴリ**: Domain Entity
**依存関係**: LearningMetrics, BusinessRuleViolationError

## 概要

個別の執筆セッションのコンテキストと学習データを管理するエンティティ。品質記録活用システムにおける学習追跡の中核を担い、執筆者の成長パターンと改善プロセスを記録・分析する。

## ドメインコンテキスト

**問題領域**: 執筆者の学習プロセス追跡と改善支援
- 個別執筆セッションの詳細記録
- 執筆時間と生産性の測定
- 学習コンテキストの保持（環境、目標、対象読者）
- 学習メトリクスの生成と分析
- セッション完了の制御と検証

**解決アプローチ**: 時系列学習データの構造化管理
- dataclass基盤の軽量エンティティ設計
- __post_init__による不変条件検証
- LearningMetricsとの協調による詳細分析
- セッション状態の厳格な管理
- 生産性レベルの自動分類

## エンティティ設計

### 1. LearningSession（エンティティ）

執筆セッションの全ライフサイクルを管理する軽量エンティティ。

**責務**:
- セッション基本情報の保持（プロジェクト、エピソード、時間）
- 学習コンテキストの記録（環境、目標、対象読者）
- セッション完了制御と時間計算
- 学習メトリクス生成の協調
- 生産性レベルの判定

**ビジネス不変条件**:
1. **プロジェクト名**: 空文字列・空白文字のみは不可
2. **エピソード番号**: 1以上の正の整数
3. **開始時刻**: 必須（None不可）
4. **時刻整合性**: end_time ≥ start_time（完了時）
5. **完了状態**: 一度完了したセッションは再完了不可
6. **時間計算**: total_writing_time = (end_time - start_time) / 60（分単位）

### 2. ビジネスルール

#### 2.1 初期化と検証
```python
@dataclass
class LearningSession:
    project_name: str
    episode_number: int
    start_time: datetime
    # オプション項目
    writing_environment: str | None = None
    target_audience: str | None = None
    writing_goal: str | None = None

    def __post_init__(self):
        # BR-1: プロジェクト名の妥当性検証
        if not self.project_name or len(self.project_name.strip()) == 0:
            raise BusinessRuleViolationError("プロジェクト名は必須です")

        # BR-2: エピソード番号の妥当性検証
        if self.episode_number <= 0:
            raise BusinessRuleViolationError("エピソード番号は1以上の正の整数である必要があります")

        # BR-3: 開始時刻の妥当性検証
        if self.start_time is None:
            raise BusinessRuleViolationError("開始時刻は必須です")
```

#### 2.2 セッション完了制御
```python
# BR-4: セッション完了の制御
def complete(self, end_time: datetime | None = None) -> None:
    if self.is_completed:
        raise BusinessRuleViolationError("既に完了したセッションです")

    self.end_time = end_time or datetime.now()

    # BR-5: 時刻整合性の検証
    if self.end_time < self.start_time:
        raise BusinessRuleViolationError("終了時刻は開始時刻より後である必要があります")

    # BR-6: 執筆時間の自動計算（分単位）
    duration = self.end_time - self.start_time
    self.total_writing_time = int(duration.total_seconds() / 60)

    self.is_completed = True
```

#### 2.3 学習メトリクス生成
```python
# BR-7: 完了セッションのみメトリクス生成可能
def create_learning_metrics(self, improvement_from_previous: float,
                          revision_count: int, user_feedback: str | None = None) -> LearningMetrics:
    if not self.is_completed:
        raise BusinessRuleViolationError("セッションが完了していません")

    return LearningMetrics(
        improvement_from_previous=improvement_from_previous,
        time_spent_writing=self.total_writing_time,
        revision_count=revision_count,
        user_feedback=user_feedback,
        writing_context=self.writing_environment,
    )
```

#### 2.4 生産性分析
```python
# BR-8: 生産性レベルの判定
def get_productivity_level(self) -> str:
    if self.is_long_session():      # >= 120分
        return "高生産性"
    if self.is_short_session():     # <= 30分
        return "低生産性"
    return "標準生産性"
```

## テスト要求仕様

### 1. 初期化と検証テスト

#### 1.1 正常な初期化
- **TEST-1**: `test_valid_initialization`
  - 必須パラメータでの正常初期化
  - デフォルト値の確認
- **TEST-2**: `test_initialization_with_all_parameters`
  - 全パラメータ指定での初期化

#### 1.2 プロジェクト名検証
- **TEST-3**: `test_empty_project_name_raises_error`
  - 空文字列でBusinessRuleViolationError
- **TEST-4**: `test_whitespace_project_name_raises_error`
  - 空白文字のみでBusinessRuleViolationError
- **TEST-5**: `test_valid_project_name_accepted`
  - 有効なプロジェクト名での成功

#### 1.3 エピソード番号検証
- **TEST-6**: `test_zero_episode_number_raises_error`
  - エピソード番号0でBusinessRuleViolationError
- **TEST-7**: `test_negative_episode_number_raises_error`
  - 負の番号でBusinessRuleViolationError
- **TEST-8**: `test_positive_episode_number_accepted`
  - 正の整数での成功

#### 1.4 開始時刻検証
- **TEST-9**: `test_none_start_time_raises_error`
  - start_time=NoneでBusinessRuleViolationError

### 2. セッション完了テスト

#### 2.1 正常な完了処理
- **TEST-10**: `test_complete_session_with_end_time`
  - 明示的終了時刻での完了
  - 時間計算の正確性
- **TEST-11**: `test_complete_session_without_end_time`
  - 現在時刻での自動完了

#### 2.2 完了状態制御
- **TEST-12**: `test_complete_already_completed_session_raises_error`
  - 既完了セッションの再完了でエラー
- **TEST-13**: `test_completion_flags_set_correctly`
  - is_completed = True の設定確認

#### 2.3 時刻整合性検証
- **TEST-14**: `test_end_time_before_start_time_raises_error`
  - 終了時刻 < 開始時刻でBusinessRuleViolationError
- **TEST-15**: `test_end_time_equals_start_time_accepted`
  - 終了時刻 = 開始時刻での成功（0分セッション）

#### 2.4 時間計算テスト
- **TEST-16**: `test_writing_time_calculation_accuracy`
  - 分単位計算の正確性（秒は切り捨て）
- **TEST-17**: `test_various_duration_calculations`
  - 様々な時間間隔での計算確認

### 3. セッション継続時間テスト

#### 3.1 継続時間取得
- **TEST-18**: `test_get_session_duration_incomplete_session`
  - 未完了セッションで0を返却
- **TEST-19**: `test_get_session_duration_completed_session`
  - 完了セッションで正確な時間を返却

### 4. コンテキスト取得テスト

#### 4.1 セッションコンテキスト
- **TEST-20**: `test_get_session_context_incomplete_session`
  - 未完了セッションのコンテキスト
  - end_time=Noneの確認
- **TEST-21**: `test_get_session_context_completed_session`
  - 完了セッションのコンテキスト
  - ISO形式時刻の確認
- **TEST-22**: `test_session_context_includes_all_fields`
  - 全フィールドの含有確認

### 5. 学習メトリクス生成テスト

#### 5.1 メトリクス生成制御
- **TEST-23**: `test_create_learning_metrics_incomplete_session_raises_error`
  - 未完了セッションでBusinessRuleViolationError
- **TEST-24**: `test_create_learning_metrics_completed_session`
  - 完了セッションでの正常生成
  - LearningMetricsオブジェクトの確認

#### 5.2 メトリクスデータ確認
- **TEST-25**: `test_learning_metrics_data_accuracy`
  - メトリクス内のデータ正確性
  - writing_contextの伝播確認

### 6. 生産性分析テスト

#### 6.1 セッション時間分類
- **TEST-26**: `test_is_long_session_default_threshold`
  - デフォルト閾値（120分）での判定
- **TEST-27**: `test_is_long_session_custom_threshold`
  - カスタム閾値での判定
- **TEST-28**: `test_is_short_session_default_threshold`
  - デフォルト閾値（30分）での判定
- **TEST-29**: `test_is_short_session_custom_threshold`
  - カスタム閾値での判定

#### 6.2 生産性レベル判定
- **TEST-30**: `test_productivity_level_high`
  - 高生産性（≥120分）の判定
- **TEST-31**: `test_productivity_level_low`
  - 低生産性（≤30分）の判定
- **TEST-32**: `test_productivity_level_standard`
  - 標準生産性（31-119分）の判定

### 7. エッジケーステスト

#### 7.1 境界値テスト
- **TEST-33**: `test_boundary_values_for_productivity`
  - 生産性判定の境界値（30分、120分）
- **TEST-34**: `test_zero_duration_session`
  - 0分セッションの処理
- **TEST-35**: `test_very_long_session`
  - 極長時間セッション（24時間超）の処理

#### 7.2 特殊ケース
- **TEST-36**: `test_microsecond_precision_handling`
  - マイクロ秒精度の時刻処理
- **TEST-37**: `test_unicode_project_names`
  - Unicode文字のプロジェクト名

### 8. データ整合性テスト

#### 8.1 オプショナルフィールド
- **TEST-38**: `test_optional_fields_none_values`
  - オプションフィールドのNone値処理
- **TEST-39**: `test_optional_fields_with_values`
  - オプションフィールドの値設定

## 実装上の注意点

### 1. パフォーマンス
- dataclassによる軽量実装
- __post_init__でのリアルタイム検証
- 時間計算の効率化

### 2. 型安全性
- 全メソッドでの型ヒント
- datetime型の適切な処理
- Optional型の明示

### 3. テスト可能性
- 時刻依存性の制御可能設計
- モック可能な外部依存関係
- 境界値テストの網羅

### 4. エラーハンドリング
- 適切な例外型の使用
- 明確なエラーメッセージ
- 不変条件の厳格な保護

## 関連仕様書

- **LearningMetrics値オブジェクト**: `learning_metrics.spec.md`
- **品質記録活用システム**: `quality_record_enhancement.spec.md`
- **BusinessRuleViolationError例外**: `domain_exceptions.spec.md`

---
**更新履歴**:
- 2025-01-22: 初版作成（TDD+DDD原則準拠）
