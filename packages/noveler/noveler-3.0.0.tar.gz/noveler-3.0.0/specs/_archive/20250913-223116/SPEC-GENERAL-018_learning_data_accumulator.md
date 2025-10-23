# SPEC-GENERAL-018: 学習データ蓄積ユースケース仕様書

## 概要
`LearningDataAccumulator`は、AI協創執筆システムの学習データを蓄積、管理、分析するユースケースです。ユーザーの執筆パターン、品質チェック結果、フィードバックデータ、改善提案の効果測定などを継続的に収集し、ユーザー固有の学習モデルを構築してパーソナライズされたAI支援を実現します。

## クラス設計

### LearningDataAccumulator

**責務**
- 執筆行動データのリアルタイム収集
- 品質チェック結果とフィードバックの結びつけ
- ユーザーパターンの特徴抽出と分類
- 改善提案の効果測定とA/Bテスト
- ユーザー固有の学習モデルの構築
- プライバシー保護とデータの匿名化
- 学習サイクル管理とモデル更新

## データ構造

### LearningDataType (Enum)
```python
class LearningDataType(Enum):
    WRITING_BEHAVIOR = "writing_behavior"        # 執筆行動
    QUALITY_FEEDBACK = "quality_feedback"        # 品質フィードバック
    USER_PREFERENCE = "user_preference"          # ユーザー好み
    IMPROVEMENT_EFFECT = "improvement_effect"    # 改善効果
    ERROR_PATTERN = "error_pattern"              # エラーパターン
    SUCCESS_PATTERN = "success_pattern"          # 成功パターン
    CONTEXT_DATA = "context_data"                # コンテキストデータ
```

### AccumulationRequest (DataClass)
```python
@dataclass
class AccumulationRequest:
    user_id: str                               # ユーザーID（匿名化済み）
    project_name: str                          # プロジェクト名
    data_types: list[LearningDataType] = []    # 収集対象データタイプ
    session_id: str | None = None              # セッションID
    episode_number: int | None = None          # エピソード番号
    real_time: bool = True                     # リアルタイム収集フラグ
    privacy_level: str = "strict"               # プライバシーレベル
    retention_days: int = 365                  # データ保存期間（日）
```

### AccumulationResponse (DataClass)
```python
@dataclass
class AccumulationResponse:
    success: bool                              # 蓄積成功フラグ
    message: str                               # 結果メッセージ
    accumulated_count: int = 0                 # 蓄積データ件数
    processed_data_types: list[LearningDataType] = []  # 処理されたデータタイプ
    model_update_triggered: bool = False       # モデル更新トリガー
    insights_generated: list[str] = []         # 生成された洞察
    privacy_compliance: bool = True            # プライバシー遵守状態
```

### LearningDataPoint (DataClass)
```python
@dataclass
class LearningDataPoint:
    data_id: str                               # データ一意識別子
    data_type: LearningDataType                # データタイプ
    timestamp: datetime                        # タイムスタンプ
    user_id_hash: str                          # ユーザーIDハッシュ
    project_hash: str                          # プロジェクトハッシュ
    content: dict[str, any]                    # データ内容（匿名化済み）
    context_metadata: dict[str, str] = {}      # コンテキストメタデータ
    sensitivity_level: str = "medium"          # 機密レベル
    expiry_date: datetime | None = None        # 有効期限
```

### UserLearningProfile (DataClass)
```python
@dataclass
class UserLearningProfile:
    user_hash: str                             # ユーザーハッシュ
    writing_patterns: dict[str, float]         # 執筆パターン特徴
    quality_trends: dict[str, list[float]]     # 品質トレンド
    common_errors: list[str]                   # 頻出エラー
    improvement_effectiveness: dict[str, float] # 改善効果率
    preferences: dict[str, any]                # ユーザー好み
    model_version: str = "1.0"                 # モデルバージョン
    last_updated: datetime = None              # 最終更新日
    confidence_score: float = 0.0              # モデル信頼度
```

## パブリックメソッド

### accumulate_learning_data()

**シグネチャ**
```python
def accumulate_learning_data(self, request: AccumulationRequest) -> AccumulationResponse:
```

**目的**
指定されたタイプの学習データを収集、匿名化して蓄積する。

**引数**
- `request`: データ蓄積リクエスト

**戻り値**
- `AccumulationResponse`: 蓄積結果

**処理フロー**
1. **プライバシーチェック**: データ収集の合意確認
2. **データ収集**: 各タイプのデータを収集
3. **匿名化処理**: 個人情報の除去とハッシュ化
4. **データ検証**: データ品質と整合性の確認
5. **蓄積処理**: データベースへの保存
6. **パターン分析**: リアルタイムパターン検出
7. **モデル更新判定**: 更新闾値とトリガー判定

### generate_user_insights()

**シグネチャ**
```python
def generate_user_insights(self, user_hash: str, lookback_days: int = 30) -> UserInsights:
```

**目的**
蓄積された学習データからユーザーの洞察を生成する。

### build_learning_model()

**シグネチャ**
```python
def build_learning_model(self, user_hash: str, force_rebuild: bool = False) -> UserLearningProfile:
```

**目的**
ユーザー固有の学習モデルを構築または更新する。

### evaluate_improvement_effectiveness()

**シグネチャ**
```python
def evaluate_improvement_effectiveness(
    self,
    user_hash: str,
    suggestion_id: str,
    evaluation_period_days: int = 14
) -> EffectivenessResult:
```

**目的**
提供された改善提案の効果を測定する。

### export_anonymized_dataset()

**シグネチャ**
```python
def export_anonymized_dataset(
    self,
    data_types: list[LearningDataType],
    sample_size: int = 1000,
    anonymization_level: str = "high"
) -> Path:
```

**目的**
研究用の匿名化されたデータセットをエクスポートする。

## プライベートメソッド

### _collect_writing_behavior()

**シグネチャ**
```python
def _collect_writing_behavior(
    self,
    user_id: str,
    project_name: str,
    session_id: str | None
) -> dict[str, any]:
```

**目的**
執筆行動データを収集する。

**収集データ**
```python
writing_behavior = {
    "typing_speed": float,                 # タイピング速度
    "pause_patterns": list[int],           # 休憩パターン
    "revision_frequency": float,           # 修正頻度
    "session_duration": int,               # セッション時間
    "word_count_progression": list[int],   # 文字数進捗
    "preferred_writing_time": str,         # 好みの執筆時間
    "distraction_events": int,             # 集中中断回数
    "backspace_usage": float,              # バックスペース使用率
    "sentence_length_variance": float      # 文長バランス
}
```

### _collect_quality_feedback()

**シグネチャ**
```python
def _collect_quality_feedback(
    self,
    user_id: str,
    project_name: str,
    episode_number: int | None
) -> dict[str, any]:
```

**目的**
品質チェック結果とフィードバックデータを収集する。

**収集データ**
```python
quality_feedback = {
    "overall_quality_score": float,        # 総合品質スコア
    "category_scores": dict[str, float],   # カテゴリ別スコア
    "detected_issues": list[dict],         # 検出された問題
    "improvement_suggestions": list[str],  # 改善提案
    "user_acceptance": dict[str, bool],    # 提案受入状況
    "manual_feedback": str,                # 手動フィードバック
    "correction_history": list[dict],      # 修正履歴
    "quality_improvement": float           # 修正後の品質向上
}
```

### _anonymize_data()

**シグネチャ**
```python
def _anonymize_data(self, data: dict[str, any], level: str) -> dict[str, any]:
```

**目的**
データを指定されたレベルで匿名化する。

**匿名化レベル**
- **low**: 直接的な個人情報のみ除去
- **medium**: 準識別子をハッシュ化
- **high**: 概念的なパターンのみ保持
- **strict**: 統計的指標のみ保持

### _detect_patterns()

**シグネチャ**
```python
def _detect_patterns(
    self,
    data_points: list[LearningDataPoint],
    pattern_types: list[str]
) -> dict[str, any]:
```

**目的**
蓄積データから特定のパターンを検出する。

**検出パターン**
- **temporal_patterns**: 時間的パターン
- **quality_patterns**: 品質変化パターン
- **error_patterns**: エラー繰り返しパターン
- **improvement_patterns**: 改善パターン
- **behavioral_patterns**: 行動パターン

### _trigger_model_update()

**シグネチャ**
```python
def _trigger_model_update(self, user_hash: str, new_data_count: int) -> bool:
```

**目的**
モデル更新の必要性を判定し、必要に応じてトリガーする。

**更新トリガー条件**
- 新データが闾値を超えた場合（100件以上）
- 品質スコアに大きな変化があった場合
- 最終更新から30日以上経過した場合
- 新しいパターンが検出された場合

### _calculate_model_confidence()

**シグネチャ**
```python
def _calculate_model_confidence(
    self,
    data_volume: int,
    data_quality: float,
    pattern_consistency: float
) -> float:
```

**目的**
モデルの信頼度を計算する。

**信頼度計算式**
```python
confidence = (
    min(data_volume / 1000, 1.0) * 0.4 +        # データ量スコア
    data_quality * 0.3 +                        # データ品質スコア
    pattern_consistency * 0.3                   # パターン一貫性スコア
)
```

## 依存関係

### アプリケーションサービス
- `QualityCheckService`: 品質チェック結果の取得
- `WritingSessionService`: 執筆セッション情報の取得
- `UserBehaviorService`: ユーザー行動データの収集

### ドメインサービス
- `DataAnonymizer`: データ匿名化サービス
- `PatternDetector`: パターン検出サービス
- `ModelBuilder`: 機械学習モデル構築
- `EffectivenessEvaluator`: 効果測定サービス

### リポジトリ
- `LearningDataRepository`: 学習データの永続化
- `UserProfileRepository`: ユーザープロファイルの管理
- `ModelRepository`: 学習モデルの管理
- `ConsentRepository`: データ利用同意管理

## 設計原則遵守

### DDD準拠
- ✅ エンティティ（`LearningDataPoint`, `UserLearningProfile`）の適切な使用
- ✅ 値オブジェクト（列挙型）の活用
- ✅ ドメインサービス（各種Analyzer）の適切な活用
- ✅ リポジトリパターンによるデータアクセス抽象化

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的なエラーハンドリング
- ✅ 型安全な実装
- ✅ 列挙型による型安全性

### プライバシーファースト
- ✅ データ保護法遵守（GDPR等）
- ✅ ユーザー同意の適切な管理
- ✅ 匿名化の徹底
- ✅ データ保存期限の管理

## 使用例

```python
# 依存関係の準備
quality_service = QualityCheckService()
session_service = WritingSessionService()
behavior_service = UserBehaviorService()
data_anonymizer = DataAnonymizer()
pattern_detector = PatternDetector()
model_builder = ModelBuilder()
effectiveness_evaluator = EffectivenessEvaluator()
learning_data_repo = LearningDataRepository()
user_profile_repo = UserProfileRepository()
model_repo = ModelRepository()
consent_repo = ConsentRepository()

# ユースケース作成
use_case = LearningDataAccumulator(
    quality_service=quality_service,
    session_service=session_service,
    behavior_service=behavior_service,
    data_anonymizer=data_anonymizer,
    pattern_detector=pattern_detector,
    model_builder=model_builder,
    effectiveness_evaluator=effectiveness_evaluator,
    learning_data_repository=learning_data_repo,
    user_profile_repository=user_profile_repo,
    model_repository=model_repo,
    consent_repository=consent_repo
)

# リアルタイム学習データ蓄積
request = AccumulationRequest(
    user_id="user123",  # 実際は匿名化される
    project_name="fantasy_adventure",
    data_types=[
        LearningDataType.WRITING_BEHAVIOR,
        LearningDataType.QUALITY_FEEDBACK,
        LearningDataType.USER_PREFERENCE
    ],
    session_id="session_456",
    episode_number=5,
    real_time=True,
    privacy_level="strict",
    retention_days=365
)

response = use_case.accumulate_learning_data(request)

if response.success:
    print(f"学習データ蓄積完了: {response.accumulated_count}件")
    print(f"処理データタイプ: {[dt.value for dt in response.processed_data_types]}")

    if response.model_update_triggered:
        print("🤖 ユーザーモデルの更新がトリガーされました")

    if response.insights_generated:
        print("\n💡 生成された洞察:")
        for insight in response.insights_generated:
            print(f"  - {insight}")

    print(f"\nプライバシー遵守: {'✅' if response.privacy_compliance else '❌'}")
else:
    print(f"学習データ蓄積失敗: {response.message}")

# ユーザー洞察の生成
user_hash = "hashed_user_123"
insights = use_case.generate_user_insights(user_hash, lookback_days=30)

print(f"\n🔍 {user_hash[:8]}...の洞察:")
print(f"最も生産的な時間帯: {insights.peak_productivity_hours}")
print(f"頻出エラーパターン: {insights.common_error_patterns}")
print(f"最効果的な改善方法: {insights.most_effective_improvements}")

# 学習モデルの構築
profile = use_case.build_learning_model(user_hash, force_rebuild=False)

print(f"\n🤖 ユーザーモデル情報:")
print(f"モデルバージョン: {profile.model_version}")
print(f"信頼度: {profile.confidence_score:.2f}")
print(f"最終更新: {profile.last_updated}")

print("\n執筆パターン:")
for pattern, score in profile.writing_patterns.items():
    print(f"  {pattern}: {score:.2f}")

# 改善効果の評価
suggestion_id = "improve_dialogue_tags"
effectiveness = use_case.evaluate_improvement_effectiveness(
    user_hash=user_hash,
    suggestion_id=suggestion_id,
    evaluation_period_days=14
)

print(f"\n📈 改善提案 '{suggestion_id}' の効果:")
print(f"効果スコア: {effectiveness.effectiveness_score:.2f}")
print(f"品質向上: {effectiveness.quality_improvement:.1f}%")
print(f"ユーザー満足度: {effectiveness.user_satisfaction:.1f}/5")

# 研究用データセットのエクスポート
dataset_path = use_case.export_anonymized_dataset(
    data_types=[LearningDataType.WRITING_BEHAVIOR, LearningDataType.QUALITY_FEEDBACK],
    sample_size=5000,
    anonymization_level="high"
)

print(f"\n📄 匿名化データセットエクスポート完了: {dataset_path}")
```

## プライバシー保護対策

### データ保護法遵守
```python
# GDPR遵守のデータ処理
class GDPRCompliance:
    @staticmethod
    def ensure_consent(user_id: str, data_type: LearningDataType) -> bool:
        consent = get_user_consent(user_id)
        return consent.allows_data_type(data_type)

    @staticmethod
    def anonymize_personal_data(data: dict) -> dict:
        # 個人情報の完全除去
        sensitive_keys = ['user_name', 'email', 'ip_address', 'device_id']
        for key in sensitive_keys:
            data.pop(key, None)
        return data

    @staticmethod
    def apply_data_retention_policy(data_points: list[LearningDataPoint]) -> None:
        cutoff_date = datetime.now() - timedelta(days=365)
        for point in data_points:
            if point.timestamp < cutoff_date:
                delete_data_point(point.data_id)
```

### 匿名化レベル
```python
# 匿名化レベル別処理
class AnonymizationProcessor:
    @staticmethod
    def process_by_level(data: dict, level: str) -> dict:
        if level == "strict":
            # 統計情報のみ保持
            return {
                "session_duration_minutes": round(data.get("session_duration", 0) / 60),
                "words_written": min(data.get("words_written", 0), 5000),  # 上限制限
                "quality_category": categorize_quality(data.get("quality_score", 0)),
                "improvement_applied": bool(data.get("improvement_applied", False))
            }
        elif level == "high":
            # パターン情報を保持
            return {
                **AnonymizationProcessor.process_by_level(data, "strict"),
                "error_types": generalize_error_types(data.get("errors", [])),
                "writing_time_category": categorize_time(data.get("timestamp"))
            }
        # 他のレベルの処理...
```

## モデル構築と更新

### 機械学習モデルの構築
```python
class PersonalizedModelBuilder:
    def build_user_model(self, user_data: list[LearningDataPoint]) -> UserLearningProfile:
        # 特徴抽出
        features = self._extract_features(user_data)

        # パターン検出
        patterns = self._detect_user_patterns(features)

        # モデル訓練
        model = self._train_personalized_model(features, patterns)

        # モデル評価
        confidence = self._evaluate_model_quality(model, user_data)

        return UserLearningProfile(
            user_hash=hash_user_id(user_data[0].user_id_hash),
            writing_patterns=patterns,
            model_version=generate_model_version(),
            confidence_score=confidence,
            last_updated=datetime.now()
        )

    def _extract_features(self, data: list[LearningDataPoint]) -> dict:
        return {
            "temporal_features": extract_temporal_features(data),
            "behavioral_features": extract_behavioral_features(data),
            "quality_features": extract_quality_features(data),
            "improvement_features": extract_improvement_features(data)
        }
```

### A/Bテスト機能
```python
class ABTestManager:
    def evaluate_suggestion_effectiveness(self, suggestion_id: str, user_group: str) -> dict:
        # コントロールグループとテストグループの比較
        control_data = self.get_control_group_data(user_group)
        test_data = self.get_test_group_data(suggestion_id, user_group)

        return {
            "quality_improvement_difference": test_data.avg_quality - control_data.avg_quality,
            "user_satisfaction_difference": test_data.satisfaction - control_data.satisfaction,
            "adoption_rate": test_data.adoption_rate,
            "statistical_significance": calculate_statistical_significance(control_data, test_data)
        }
```

## エラーハンドリング

### データ収集エラー
```python
try:
    behavior_data = self.behavior_service.collect_writing_behavior(user_id, session_id)
except BehaviorDataUnavailable:
    logger.warning(f"ユーザー {user_id} の行動データが利用できません")
    behavior_data = {}  # デフォルト値
except Exception as e:
    logger.error(f"行動データ収集エラー: {e}")
    return AccumulationResponse(
        success=False,
        message=f"データ収集中にエラーが発生しました: {str(e)}"
    )
```

### モデル構築エラー
```python
try:
    model = self.model_builder.build_user_model(user_data)
except InsufficientDataError:
    logger.info(f"ユーザー {user_hash} のデータが不十分です。デフォルトモデルを使用します。")
    model = self.model_builder.get_default_model()
except ModelBuildingError as e:
    logger.error(f"モデル構築エラー: {e}")
    raise LearningSystemError(f"ユーザーモデルの構築に失敗しました: {str(e)}")
```

### プライバシー違反エラー
```python
if not self.consent_repository.has_consent(user_id, data_type):
    logger.warning(f"ユーザー {user_id} は {data_type.value} データの収集に同意していません")
    return AccumulationResponse(
        success=False,
        message="データ収集に必要なユーザー同意が得られていません",
        privacy_compliance=False
    )
```

## テスト観点

### 単体テスト
- 各データタイプの収集機能
- 匿名化処理の正確性
- パターン検出アルゴリズム
- モデル構築ロジック
- エラー条件での処理

### 統合テスト
- リアルタイムデータ収集
- 長期間のデータ蓄積
- モデル更新サイクル
- プライバシー保護機能

### プライバシーテスト
- 個人情報の完全除去
- データ匿名化の効果
- 同意管理システム
- データ保存期限の遵守

## 品質基準

- **プライバシーファースト**: データ保護法の完全遵守
- **データ品質**: 高品質な学習データの確保
- **モデル精度**: 個人化された高精度モデル
- **透明性**: ユーザーに対するデータ利用の透明性
- **持続性**: 長期的な学習と改善の継続
