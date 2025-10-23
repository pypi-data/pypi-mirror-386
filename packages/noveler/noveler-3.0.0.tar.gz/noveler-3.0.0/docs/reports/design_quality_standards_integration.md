# 品質基準統合アーキテクチャ設計書

## 🎯 統合目標

### 現状課題
1. **二重管理問題**: QualityStandard.py (コード) ⟷ A30品質基準.md (ドキュメント)
2. **抽象的基準**: 「明確」「具体的」等の測定不能基準
3. **閾値ハードコーディング**: threshold値がコード内固定
4. **メンテナンス負荷**: 仕様変更時の二重更新作業

### 解決方針
**設定駆動統合型アーキテクチャ**による**Single Source of Truth**実現

## 🏗️ 統合アーキテクチャ

### Phase 1: 設定外部化
```yaml
# config/quality_standards.yaml
version: "4.1.0"
standards:
  plot_quality:
    P-04_turning_points:
      minimum_score: 70
      target_score: 80
      excellent_score: 90
      measurement:
        method: "turning_points_count_with_impact"
        criteria:
          minimum_turning_points: 5
          impact_score_range: [1, 10]
          required_causality_description: true
      validation:
        - "転換点5箇所以上"
        - "各転換点の影響度数値(1-10)"
        - "因果関係記述"

    P-06_scene_purpose:
      minimum_score: 75
      target_score: 85
      excellent_score: 95
      measurement:
        method: "scene_purpose_clarity"
        criteria:
          minimum_description_length: 50
          story_contribution_quantified: true
          reader_emotion_target_set: true
      validation:
        - "全章に目的記述50文字以上"
        - "物語進行への寄与数値化"
        - "読者感情目標設定"
```

### Phase 2: 統合実装層
```python
@dataclass(frozen=True)
class UnifiedQualityStandard:
    """統合品質基準"""

    item_id: str  # P-04, R-07, C-03等
    name: str
    category: QualityCategory  # PLOT, REVISION, CONCEPT等
    thresholds: QualityThreshold
    measurement: MeasurementSpec
    validation_criteria: list[str]
    abstraction_improvements: dict[str, str]  # 「明確」→具体基準マップ

@dataclass(frozen=True)
class MeasurementSpec:
    """測定仕様"""

    method: str  # 測定手法
    criteria: dict[str, Any]  # 具体的判定基準
    automation_level: AutomationLevel  # MANUAL, SEMI_AUTO, FULL_AUTO
```

### Phase 3: 抽象基準具体化マップ
```python
ABSTRACTION_IMPROVEMENT_MAP = {
    "明確": {
        "measurement": "文字数・要素数・記述完全性",
        "criteria": "最低文字数+必須要素網羅+論理的整合性",
        "threshold": "数値化された判定基準"
    },
    "具体的": {
        "measurement": "身体反応・行動描写・五感要素",
        "criteria": "身体化度80%以上+行動による感情表現",
        "threshold": "抽象表現0件"
    },
    "適切": {
        "measurement": "基準範囲・比率・バランス指標",
        "criteria": "規定範囲内+最適バランス達成",
        "threshold": "偏差係数・適合度数値"
    }
}
```

## 🔧 実装戦略

### Step 1: 品質基準設定ファイル作成
- `config/quality_standards.yaml`
- A30品質基準の数値化・構造化
- 抽象表現の具体化マッピング

### Step 2: 統合品質エンジン実装
```python
class UnifiedQualityEngine:
    """統合品質評価エンジン"""

    def __init__(self, config_path: str):
        self.standards = self.load_standards(config_path)

    def evaluate_quality(self, content: str, category: QualityCategory) -> QualityReport:
        """統合品質評価実行"""

    def get_concrete_criteria(self, abstract_term: str) -> ConcreteSpec:
        """抽象基準→具体基準変換"""

    def generate_improvement_plan(self, results: QualityReport) -> ImprovementPlan:
        """改善計画自動生成"""
```

### Step 3: レガシーコード統合
- QualityEvaluationService.py の閾値外部化
- A30品質基準.md の設定ファイル参照化
- YAML チェックリスト廃止・アーカイブ移動

## 🧪 テスト戦略

### 統合テスト項目
1. **設定駆動テスト**: YAML設定変更→評価結果変更確認
2. **抽象基準具体化テスト**: 「明確」→数値基準変換テスト
3. **閾値動的変更テスト**: threshold変更→判定結果変更確認
4. **後方互換性テスト**: 既存API動作保証

### 品質保証項目
1. **Single Source of Truth**: 設定ファイルが唯一の真実源
2. **具体化完全性**: 全抽象表現の具体基準マッピング
3. **測定可能性**: 全基準の自動測定可能化
4. **拡張性**: 新基準追加の容易性

## 📈 期待効果

### 1. メンテナンス性向上
- **一元管理**: 品質基準の変更が設定ファイル1箇所で完結
- **自動同期**: ドキュメント・コードの自動整合性確保

### 2. 品質基準の透明性
- **測定可能化**: 全ての基準が数値的に測定可能
- **客観性確保**: 主観的判断の排除

### 3. 開発効率向上
- **自動化促進**: 具体基準による品質チェック自動化
- **改善ガイダンス**: 具体的改善指示の自動生成

## 🚀 マイグレーション計画

### フェーズ1: 設定外部化（1-2日）
1. quality_standards.yaml 作成
2. A30品質基準の設定化
3. 抽象基準具体化マップ構築

### フェーズ2: エンジン実装（2-3日）
1. UnifiedQualityEngine 実装
2. レガシーコード統合
3. 統合テスト実装

### フェーズ3: 本格運用（1日）
1. YAML廃止・アーカイブ移動
2. ドキュメント更新
3. 運用テスト・検証

**合計工期: 4-6日間**（段階的実装による低リスク移行）

---

**この設計により、ユーザー指摘の「YAMLチェックリスト廃止→A30品質基準統合」が技術的にも完全実現されます。**
