# YAML品質記録強化リポジトリ仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、AI学習型品質記録強化システムのYAMLファイルベース永続化を提供する。

### 1.2 スコープ
- 個人化品質改善データの作成・保存・検索・分析機能
- AI学習データとトレンド分析の統合管理
- 成長パターンと改善提案の永続化
- レガシー品質記録との互換性確保

### 1.3 アーキテクチャ位置
```
Domain Layer
├── QualityRecordEnhancementRepository (Interface) ← Infrastructure Layer
└── QualityRecordEnhancement (Entity)              └── YamlQualityRecordEnhancementRepository (Implementation)
```

## 2. 機能仕様

### 2.1 基本CRUD操作
```python
# 保存
def save(enhancement_record: QualityRecordEnhancement, project_id: str) -> None

# 検索
def find_by_project(project_id: str) -> QualityRecordEnhancement | None
def find_by_writer_id(writer_id: str) -> list[QualityRecordEnhancement]
def find_latest_enhancement(project_id: str) -> QualityRecordEnhancement | None

# 存在確認
def exists(project_id: str) -> bool

# 更新
def update_learning_data(project_id: str, learning_data: dict) -> bool
def append_improvement_suggestion(project_id: str, suggestion: dict) -> bool

# 削除
def delete(project_id: str) -> bool
def cleanup_old_records(before_date: datetime, keep_count: int = 10) -> int
```

### 2.2 AI学習データ管理
```python
# 学習データの蓄積
def accumulate_learning_data(
    project_id: str,
    episode_data: dict,
    quality_scores: dict,
    improvement_metrics: dict
) -> None

# パターン認識データの取得
def get_writing_patterns(
    project_id: str,
    pattern_type: str = "all"  # "strength", "weakness", "trend"
) -> dict[str, Any]

# 予測モデルデータの管理
def save_prediction_model(
    project_id: str,
    model_data: dict,
    model_version: str
) -> bool

def load_prediction_model(
    project_id: str,
    model_version: str | None = None  # None = latest
) -> dict | None
```

### 2.3 トレンド分析機能
```python
# 成長トレンドの分析
def analyze_growth_trend(
    project_id: str,
    time_window_days: int = 30
) -> dict[str, Any]

# 品質改善トレンドの取得
def get_improvement_trend(
    project_id: str,
    metric_names: list[str] | None = None
) -> dict[str, list[float]]

# 弱点分析
def analyze_weakness_patterns(
    project_id: str,
    include_suggestions: bool = True
) -> dict[str, Any]

# 強み分析
def analyze_strength_patterns(
    project_id: str,
    highlight_consistent: bool = True
) -> dict[str, Any]
```

### 2.4 個人化改善提案機能
```python
# カスタム改善提案の生成
def generate_personalized_suggestions(
    project_id: str,
    current_episode_data: dict,
    max_suggestions: int = 5
) -> list[dict]

# 改善提案の効果測定
def measure_suggestion_effectiveness(
    project_id: str,
    suggestion_id: str,
    outcome_data: dict
) -> dict[str, float]

# 提案履歴の管理
def get_suggestion_history(
    project_id: str,
    include_effectiveness: bool = True
) -> list[dict]

# 成功パターンの抽出
def extract_successful_patterns(
    project_id: str,
    min_improvement_threshold: float = 5.0
) -> list[dict]
```

### 2.5 統計・比較分析
```python
# 個人統計の取得
def get_writer_statistics(
    project_id: str,
    include_predictions: bool = False
) -> dict[str, Any]

# 他プロジェクトとの比較分析
def compare_with_other_projects(
    project_id: str,
    comparison_metrics: list[str],
    anonymize: bool = True
) -> dict[str, Any]

# ベンチマーク分析
def get_benchmark_analysis(
    project_id: str,
    benchmark_type: str = "genre"  # "genre", "experience", "length"
) -> dict[str, Any]
```

## 3. データ構造仕様

### 3.1 ファイル配置
```
プロジェクトルート/
├── 50_管理資料/                      # 品質記録強化データ
│   ├── 品質記録_AI学習用.yaml         # メインの強化記録
│   ├── 学習データ/                    # 詳細学習データ
│   │   ├── パターン認識.yaml
│   │   ├── 予測モデル.yaml
│   │   └── 改善履歴.yaml
│   └── 個人化分析/                    # 個人化データ
│       ├── 執筆傾向.yaml
│       ├── 成長パターン.yaml
│       └── 改善提案履歴.yaml
└── backup/                           # バックアップ（任意）
    └── 20250721_143022/
        └── 品質記録_AI学習用.yaml
```

### 3.2 品質記録強化YAML構造
```yaml
metadata:
  project_name: "転生したら最強の魔法使いだった件"
  writer_id: "writer_001"
  last_updated: "2025-07-21T14:30:22"
  enhancement_version: "2.1"
  analysis_level: "advanced"

# 個人化学習データ
learning_data:
  writing_patterns:
    strengths:
      - pattern: "対話シーンでの感情表現"
        confidence: 0.92
        evidence_count: 15
        avg_score_improvement: 8.3
      - pattern: "アクションシーンの臨場感"
        confidence: 0.87
        evidence_count: 12
        avg_score_improvement: 6.7

    weaknesses:
      - pattern: "心理描写の深度不足"
        confidence: 0.89
        evidence_count: 18
        avg_score_decline: -4.2
        improvement_potential: 12.5
      - pattern: "場面転換の唐突感"
        confidence: 0.84
        evidence_count: 9
        avg_score_decline: -3.1
        improvement_potential: 8.7

    trends:
      overall_improvement_rate: 2.3  # % per episode
      consistency_score: 0.76
      learning_acceleration: 1.15
      plateau_indicators: []

# 改善トレンド分析
improvement_trends:
  basic_writing_style:
    - episode: 1
      score: 75.2
      timestamp: "2025-07-15T10:30:00"
    - episode: 2
      score: 78.1
      timestamp: "2025-07-16T14:20:00"
    - episode: 3
      score: 81.5
      timestamp: "2025-07-17T11:45:00"

  story_structure:
    - episode: 1
      score: 82.0
      timestamp: "2025-07-15T10:30:00"
    - episode: 2
      score: 85.3
      timestamp: "2025-07-16T14:20:00"
    - episode: 3
      score: 87.8
      timestamp: "2025-07-17T11:45:00"

# 個人化改善提案
personalized_suggestions:
  current_suggestions:
    - id: "ps_001"
      category: "心理描写強化"
      priority: "high"
      confidence: 0.91
      suggestion: "キャラクターの内面の葛藤をより具体的に描写してください"
      specific_advice:
        - "感情の変化を身体的反応と組み合わせて表現"
        - "過去の経験との対比を使用した心理的深度の追加"
        - "独白と行動の矛盾を利用した複雑性の演出"
      expected_improvement: 7.5
      implementation_difficulty: "medium"

    - id: "ps_002"
      category: "場面転換技法"
      priority: "medium"
      confidence: 0.83
      suggestion: "シーン間の繋がりをより自然にするための技法活用"
      specific_advice:
        - "前のシーンの余韻を次のシーンに引き継ぐ"
        - "時間経過や場所移動の明示的な説明追加"
        - "キャラクターの感情的連続性を重視"
      expected_improvement: 5.2
      implementation_difficulty: "easy"

  suggestion_history:
    - id: "ps_old_001"
      category: "対話描写"
      suggested_at: "2025-07-15T10:30:00"
      applied_at: "2025-07-16T09:15:00"
      effectiveness_score: 8.7
      actual_improvement: 6.3
      feedback: "非常に効果的でした"

# AI予測モデルデータ
prediction_models:
  current_model:
    version: "2.1.0"
    created_at: "2025-07-21T10:00:00"
    accuracy_score: 0.87
    features:
      - "文章長"
      - "対話比率"
      - "感情語使用頻度"
      - "修辞技法使用回数"
    parameters:
      learning_rate: 0.001
      regularization: 0.01
      hidden_layers: [128, 64, 32]

  model_performance:
    training_accuracy: 0.89
    validation_accuracy: 0.87
    test_accuracy: 0.85
    overfitting_score: 0.04

# 成長パターン分析
growth_patterns:
  learning_style: "steady_improver"  # "rapid_learner", "plateau_breaker", "consistent_grower"
  optimal_feedback_frequency: 2  # episodes
  motivation_factors:
    - "具体的な改善例"
    - "定量的な成長指標"
    - "他作品との比較"
  resistance_patterns:
    - "抽象的なアドバイス"
    - "過度の批判"

# 比較・ベンチマークデータ
benchmark_data:
  genre_comparison:
    genre: "異世界転生"
    percentile: 78
    above_average_categories:
      - "世界観設定"
      - "キャラクター魅力"
    below_average_categories:
      - "心理描写"
      - "文章技巧"

  experience_level_comparison:
    level: "中級者"
    typical_progression_rate: 1.8
    current_progression_rate: 2.3
    acceleration_factor: 1.28

# メタ分析情報
meta_analysis:
  data_quality_score: 0.91
  confidence_intervals:
    improvement_predictions: [2.1, 2.5]
    plateau_risk: [0.15, 0.25]
  statistical_significance: 0.95
  sample_size_adequacy: true

  update_frequency: "after_each_episode"
  last_comprehensive_analysis: "2025-07-20T15:30:00"
  next_scheduled_update: "2025-07-22T10:00:00"
```

### 3.3 詳細学習データ構造
```yaml
# パターン認識.yaml
pattern_recognition:
  recurring_issues:
    - pattern_id: "pr_001"
      description: "説明的文章の過多"
      frequency: 0.67
      severity: "medium"
      episodes_affected: [1, 3, 5, 7, 9]
      improvement_suggestions: [...]

  successful_techniques:
    - technique_id: "st_001"
      description: "五感を使った情景描写"
      success_rate: 0.89
      episodes_used: [2, 4, 6, 8, 10]
      impact_score: 8.5

# 予測モデル.yaml（詳細）
prediction_model_details:
  feature_importance:
    文章長: 0.23
    対話比率: 0.19
    感情語頻度: 0.17
    修辞技法: 0.15
    シーン転換回数: 0.12
    キャラクター登場数: 0.14

  correlation_matrix:
    文章長_対話比率: -0.34
    感情語頻度_修辞技法: 0.67
    # ... 他の相関関係
```

## 4. 技術仕様

### 4.1 依存関係
```python
# 外部ライブラリ
import yaml
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Dict, List
import json

# ドメイン層
from domain.entities.quality_record_enhancement import QualityRecordEnhancement, LearningPattern
from domain.repositories.quality_record_enhancement_repository import QualityRecordEnhancementRepository
from domain.value_objects.improvement_score import ImprovementScore
from domain.value_objects.confidence_score import ConfidenceScore
```

### 4.2 エラーハンドリング
```python
# カスタム例外
class QualityRecordEnhancementRepositoryError(Exception):
    pass

class EnhancementRecordNotFoundError(QualityRecordEnhancementRepositoryError):
    pass

class InvalidLearningDataError(QualityRecordEnhancementRepositoryError):
    pass

class PredictionModelError(QualityRecordEnhancementRepositoryError):
    pass

class InsufficientDataError(QualityRecordEnhancementRepositoryError):
    pass
```

## 5. パフォーマンス要件

### 5.1 応答時間
- 学習データ読み込み: 100ms以内
- トレンド分析実行: 500ms以内
- 改善提案生成: 1秒以内
- 予測モデル更新: 5秒以内

### 5.2 メモリ使用量
- 基本強化記録: 20MB以内
- 学習データ全体: 100MB以内
- 予測モデル: 50MB以内

### 5.3 同時実行性
- 読み取り操作: 並行実行可能
- 学習データ更新: 排他制御
- 分析処理: 並行実行可能

## 6. 品質保証

### 6.1 データ整合性
- 学習データの一貫性検証
- 予測精度の定期的評価
- トレンドデータの妥当性確認
- 統計的有意性の検証

### 6.2 エラー回復
- 破損した学習データの復旧
- 予測モデルの自動再構築
- 不完全なデータでの部分的動作
- デフォルト提案への自動フォールバック

### 6.3 品質監視
- 予測精度の継続監視
- 学習データ品質の評価
- 改善提案の効果測定
- システム全体の健全性チェック

## 7. セキュリティ

### 7.1 アクセス制御
- ファイルシステム権限に基づくアクセス制御
- プロジェクト固有データの完全分離
- 学習データの匿名化処理

### 7.2 データ保護
- 個人情報の除去・暗号化
- 機械学習データの安全な保存
- バックアップデータの暗号化
- 一時ファイルの安全な削除

## 8. 互換性

### 8.1 レガシーシステム
- 既存品質記録との互換性保持
- 段階的AI機能の追加
- 旧データの自動変換
- 機能の選択的有効化

### 8.2 将来拡張性
- 新しい学習アルゴリズムへの対応
- 外部AI サービスとの連携準備
- 分散学習システムへの拡張
- リアルタイム改善提案機能

## 9. 使用例

### 9.1 基本的な使用パターン
```python
# リポジトリ初期化
enhancement_repo = YamlQualityRecordEnhancementRepository()

# 学習データの蓄積
episode_data = {"word_count": 3247, "dialogue_ratio": 0.35}
quality_scores = {"basic_style": 85.2, "story_structure": 82.7}
improvement_metrics = {"trend_improvement": 3.2}

enhancement_repo.accumulate_learning_data(
    "project-001", episode_data, quality_scores, improvement_metrics
)

# 個人化改善提案の生成
suggestions = enhancement_repo.generate_personalized_suggestions(
    "project-001", episode_data, max_suggestions=3
)

for suggestion in suggestions:
    print(f"提案: {suggestion['suggestion']}")
    print(f"期待改善度: {suggestion['expected_improvement']}")
```

### 9.2 分析・トレンド機能の活用例
```python
# 成長トレンドの分析
growth_trend = enhancement_repo.analyze_growth_trend("project-001", 30)
print(f"成長率: {growth_trend['overall_growth_rate']}")

# 弱点パターンの分析
weakness_patterns = enhancement_repo.analyze_weakness_patterns("project-001")
for pattern in weakness_patterns['patterns']:
    print(f"弱点: {pattern['description']}")
    print(f"改善可能性: {pattern['improvement_potential']}")

# ベンチマーク比較
benchmark = enhancement_repo.get_benchmark_analysis("project-001", "genre")
print(f"同ジャンル内順位: {benchmark['percentile']}%")
```

### 9.3 予測モデル管理例
```python
# 予測モデルの更新
model_data = {
    "version": "2.2.0",
    "accuracy": 0.89,
    "features": ["word_count", "dialogue_ratio", "emotion_words"]
}

enhancement_repo.save_prediction_model("project-001", model_data, "2.2.0")

# 最新予測モデルの読み込み
latest_model = enhancement_repo.load_prediction_model("project-001")
print(f"モデルバージョン: {latest_model['version']}")
```

## 10. テスト仕様

### 10.1 単体テスト
- 学習データ蓄積・検索のテスト
- トレンド分析アルゴリズムのテスト
- 改善提案生成ロジックのテスト
- 予測モデル管理のテスト

### 10.2 統合テスト
- 実際のプロジェクトデータでの動作確認
- AI学習と提案生成の統合テスト
- パフォーマンステスト
- 長期運用テスト

### 10.3 AI品質テスト
- 予測精度の評価テスト
- 改善提案の有効性テスト
- バイアス検出テスト
- 学習データ品質テスト

## 11. 運用・監視

### 11.1 ログ出力
- 学習データ更新のログ
- 予測精度の定期ログ
- 改善提案生成のログ
- エラー・例外の詳細ログ

### 11.2 メトリクス
- 予測精度の推移監視
- 改善提案の採用率
- システム応答時間
- データ品質スコア

### 11.3 アラート
- 予測精度の急激な低下
- 学習データの品質劣化
- システムパフォーマンス低下
- 重要な改善機会の検出

## 12. 実装メモ

### 12.1 実装ファイル
- **メインクラス**: `src/noveler/infrastructure/repositories/yaml_quality_record_enhancement_repository.py`
- **テストファイル**: `tests/unit/infrastructure/repositories/test_yaml_quality_record_enhancement_repository.py`

### 12.2 設計方針
- DDD原則の厳格な遵守
- AI学習機能の段階的実装
- データプライバシーの完全保護
- 拡張性を重視したアーキテクチャ

### 12.3 今後の改善点
- [ ] 深層学習モデルとの統合
- [ ] リアルタイム品質予測機能
- [ ] 執筆者コミュニティとの比較機能
- [ ] 自動執筆支援機能の追加
- [ ] マルチモーダル品質分析（画像・音声対応）
