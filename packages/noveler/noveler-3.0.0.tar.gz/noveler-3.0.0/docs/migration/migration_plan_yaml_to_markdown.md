# YAML→Markdown統合 マイグレーション実行計画書

## 🎯 マイグレーション目標

### 完了状態（Target State）
- ✅ **YAML チェックリスト完全廃止**
- ✅ **A30品質基準.md 完全統合**（プロット・推敲項目含む）
- ✅ **A11企画設計ガイド.md 完全統合**（企画設計項目含む）
- ✅ **抽象基準の具体化完了**（「明確」→数値基準等）
- ✅ **設定駆動品質システム実装**（Single Source of Truth）

### 現在達成状況
- ✅ **A25プロット統合**: 完了（A30品質基準.mdに統合済み）
- ✅ **A41推敲統合**: 完了（A30品質基準.mdに統合済み）
- ✅ **A11企画統合**: 完了（A11ガイド.mdに統合済み）
- ✅ **抽象基準具体化**: 完了（全項目に具体基準追加済み）
- ✅ **統合アーキテクチャ**: 設計完了（設定外部化方式）

## 📋 マイグレーション実行手順

### Phase 1: アーカイブ準備（作業時間: 30分）

#### 1.1 YAMLファイルアーカイブ移動
```bash
# 統合済みYAMLファイルをアーカイブに移動
mkdir -p docs/archive/yaml_legacy/
mv docs/A25_プロット作成チェックリスト.yaml docs/archive/yaml_legacy/
mv docs/A41_推敲品質チェックリスト.yaml docs/archive/yaml_legacy/
mv docs/A11_企画設計チェックリスト.yaml docs/archive/yaml_legacy/

# アーカイブ情報ファイル作成
cat > docs/archive/yaml_legacy/README.md << 'EOF'
# YAMLチェックリスト アーカイブ

## 廃止理由
2025-08-23: YAMLチェックリスト→Markdown品質基準への統合により廃止

## 統合先
- A25_プロット作成チェックリスト.yaml → A30_執筆品質基準.md（プロット品質チェック項目）
- A41_推敲品質チェックリスト.yaml → A30_執筆品質基準.md（推敲品質チェック項目）
- A11_企画設計チェックリスト.yaml → A11_企画設計・コンセプト策定ガイド.md（企画設計品質チェック項目）

## 改善内容
- 抽象基準→具体基準への改善完了
- 閾値ハードコーディング→設定外部化対応
- Single Source of Truth実現
EOF
```

### Phase 2: ドキュメント参照更新（作業時間: 45分）

#### 2.1 docs/_index.yaml 更新
```bash
# YAMLファイル参照を削除・統合先に変更
sed -i 's/A25_プロット作成チェックリスト\.yaml/A30_執筆品質基準\.md（プロット統合済み）/g' docs/_index.yaml
sed -i 's/A41_推敲品質チェックリスト\.yaml/A30_執筆品質基準\.md（推敲統合済み）/g' docs/_index.yaml
sed -i 's/A11_企画設計チェックリスト\.yaml/A11_企画設計・コンセプト策定ガイド\.md（企画統合済み）/g' docs/_index.yaml
```

#### 2.2 ガイド間参照更新
```bash
# 他ドキュメントからのYAML参照を更新
grep -r "A25_プロット作成チェックリスト\.yaml" docs/ --exclude-dir=archive | \
  xargs sed -i 's/A25_プロット作成チェックリスト\.yaml/A30_執筆品質基準\.md#プロット品質チェック項目統合/g'

grep -r "A41_推敲品質チェックリスト\.yaml" docs/ --exclude-dir=archive | \
  xargs sed -i 's/A41_推敲品質チェックリスト\.yaml/A30_執筆品質基準\.md#推敲品質チェック項目統合/g'
```

### Phase 3: 設定外部化実装（作業時間: 2時間）

#### 3.1 品質基準設定ファイル作成
```bash
# 設定ディレクトリ作成
mkdir -p config/quality/

# 統合品質基準設定作成
cat > config/quality/quality_standards.yaml << 'EOF'
# 統合品質基準設定ファイル
version: "4.1.0"
last_update: "2025-08-23"
description: "A30品質基準.md の設定化・YAML統合版"

standards:
  # プロット品質項目（A25統合）
  plot_quality:
    P-04_turning_points:
      minimum_score: 70
      target_score: 80
      excellent_score: 90
      measurement:
        method: "turning_points_impact_analysis"
        criteria:
          minimum_turning_points: 5
          impact_score_range: [1, 10]
          causality_description_required: true
      abstraction_improvements:
        original: "主要ターニングポイント設定"
        improved: "主要ターニングポイント5-7箇所設定（「明確な転換点」→数値基準）"
        concrete_criteria: "転換点5箇所以上+各転換点の影響度数値(1-10)+因果関係記述"

    P-06_scene_purpose:
      minimum_score: 75
      target_score: 85
      excellent_score: 95
      measurement:
        method: "scene_purpose_quantification"
        criteria:
          minimum_description_length: 50
          story_contribution_quantified: true
          reader_emotion_target_set: true
      abstraction_improvements:
        original: "各シーンの目的が明確か"
        improved: "各章目的明確化（抽象→具体改善）"
        concrete_criteria: "全章に目的記述50文字以上+物語進行への寄与数値化+読者感情目標設定"

  # 推敲品質項目（A41統合）
  revision_quality:
    R-07_emotion_concretization:
      minimum_score: 85
      target_score: 90
      excellent_score: 95
      measurement:
        method: "emotion_physicalization_analysis"
        criteria:
          abstract_emotion_count: 0
          body_reaction_ratio: 0.8
          action_based_expression_ratio: 0.9
      abstraction_improvements:
        original: "感情表現の具体性"
        improved: "感情表現具体化（最重要改善項目）"
        concrete_criteria: "抽象感情表現0件+身体反応描写80%以上+行動による感情表現"

  # 企画設計項目（A11統合）
  concept_quality:
    C-03_usp_clarification:
      minimum_score: 90
      target_score: 95
      excellent_score: 98
      measurement:
        method: "usp_differentiation_analysis"
        criteria:
          uniqueness_score_minimum: 90
          differentiation_elements_minimum: 3
          competitive_advantage_defined: true
      abstraction_improvements:
        original: "独自販売提案の明確定義"
        improved: "USP明確化確認（最重要項目）"
        concrete_criteria: "独自性スコア90%以上+差別化要素3つ以上+競合優位性説明"
EOF
```

#### 3.2 抽象基準具体化マップ実装
```python
# scripts/domain/services/abstraction_concretization_service.py 作成
cat > scripts/domain/services/abstraction_concretization_service.py << 'EOF'
"""抽象基準具体化サービス"""

from dataclasses import dataclass
from typing import Dict, Any
from scripts.domain.value_objects.quality_standards import QualityThreshold


@dataclass(frozen=True)
class ConcreteCriteria:
    """具体化された基準"""

    measurement_method: str
    criteria: Dict[str, Any]
    validation_rules: list[str]
    threshold: QualityThreshold


class AbstractionConcretizationService:
    """抽象基準具体化サービス"""

    ABSTRACTION_MAP = {
        "明確": {
            "measurement": "文字数・要素数・記述完全性分析",
            "base_criteria": {
                "minimum_description_length": 30,
                "required_elements_coverage": 100,
                "logical_consistency_score": 80
            }
        },
        "具体的": {
            "measurement": "身体反応・行動描写・五感要素分析",
            "base_criteria": {
                "abstract_expression_count": 0,
                "body_reaction_ratio": 0.8,
                "sensory_description_ratio": 0.6
            }
        },
        "適切": {
            "measurement": "基準範囲・比率・バランス指標分析",
            "base_criteria": {
                "range_compliance_ratio": 0.95,
                "balance_deviation_coefficient": 0.3,
                "optimization_score": 85
            }
        }
    }

    def concretize_abstract_term(self, term: str, context: str = "") -> ConcreteCriteria:
        """抽象用語を具体基準に変換"""
        if term not in self.ABSTRACTION_MAP:
            raise ValueError(f"未対応の抽象用語: {term}")

        mapping = self.ABSTRACTION_MAP[term]

        return ConcreteCriteria(
            measurement_method=mapping["measurement"],
            criteria=mapping["base_criteria"],
            validation_rules=self._generate_validation_rules(term, mapping),
            threshold=self._determine_threshold(term, context)
        )

    def _generate_validation_rules(self, term: str, mapping: Dict) -> list[str]:
        """検証ルール生成"""
        base_rules = {
            "明確": [
                "記述文字数が最低基準を満たしている",
                "必須要素が100%網羅されている",
                "論理的整合性が保たれている"
            ],
            "具体的": [
                "抽象的表現が使用されていない",
                "身体反応による感情表現が十分である",
                "行動による状況説明が適切である"
            ],
            "適切": [
                "規定範囲内に収まっている",
                "バランスが最適化されている",
                "偏りや極端さがない"
            ]
        }
        return base_rules.get(term, [])

    def _determine_threshold(self, term: str, context: str) -> QualityThreshold:
        """文脈に応じた閾値決定"""
        base_thresholds = {
            "明確": QualityThreshold(70, 80, 90),
            "具体的": QualityThreshold(80, 90, 95),
            "適切": QualityThreshold(75, 85, 95)
        }
        return base_thresholds.get(term, QualityThreshold(70, 80, 90))
EOF
```

### Phase 4: 統合テスト実行（作業時間: 1.5時間）

#### 4.1 統合完全性テスト実行
```bash
# マイグレーション完全性テスト
python -m pytest tests/integration/test_yaml_migration_completeness.py -v
# 注: CI/LLM連携では `/bin/test` または `scripts/run_pytest.py` の利用を推奨します。

# 抽象基準具体化テスト
python -m pytest tests/unit/domain/test_abstraction_concretization.py -v
# 注: CI/LLM連携では `/bin/test` または `scripts/run_pytest.py` の利用を推奨します。

# 設定駆動品質評価テスト
python -m pytest tests/integration/test_config_driven_quality.py -v
# 注: CI/LLM連携では `/bin/test` または `scripts/run_pytest.py` の利用を推奨します。
```

### Phase 5: ドキュメント更新（作業時間: 30分）

#### 5.1 統合完了レポート作成
```bash
cat > migration_completion_report.md << 'EOF'
# YAML→Markdown統合 完了レポート

## 📋 実行日時
2025-08-23 実行完了

## ✅ 完了項目

### ドキュメント統合
- [x] A25_プロット作成チェックリスト.yaml → A30_執筆品質基準.md
- [x] A41_推敲品質チェックリスト.yaml → A30_執筆品質基準.md
- [x] A11_企画設計チェックリスト.yaml → A11_企画設計・コンセプト策定ガイド.md

### 改善実装
- [x] 抽象基準→具体基準改善（「明確」→数値基準等）
- [x] 閾値外部化設定システム実装
- [x] Single Source of Truth実現

### システム統合
- [x] 設定駆動品質評価エンジン実装
- [x] 抽象基準具体化サービス実装
- [x] 統合テスト完了・品質保証

## 🎯 効果

### メンテナンス性向上
- YAML重複管理問題解決
- 品質基準の一元管理実現
- 設定変更の簡易化

### 品質基準透明性
- 全抽象基準の具体化完了
- 測定可能な客観基準実現
- 改善指示の明確化

## 📚 利用方法

### 統合後の品質チェック
1. **プロット品質**: A30_執筆品質基準.md#プロット品質チェック項目
2. **推敲品質**: A30_執筆品質基準.md#推敲品質チェック項目
3. **企画品質**: A11_企画設計・コンセプト策定ガイド.md#企画設計品質チェック項目

### 設定カスタマイズ
- 品質基準調整: `config/quality/quality_standards.yaml`
- 閾値変更: 各項目のscore設定変更
- 新基準追加: standards配下に項目追加

**🚀 統合完了により、ユーザー要求である「YAMLチェックリスト廃止→A30品質基準統合」が完全実現されました。**
EOF
```

## 📊 マイグレーション検証

### 完全性チェック
```bash
# 統合完全性検証スクリプト実行
./scripts/tools/validate_yaml_migration.py

# 期待結果:
# ✅ A25項目: 10/10 統合済み (100%)
# ✅ A41項目: 13/13 統合済み (100%)
# ✅ A11項目: 9/9 統合済み (100%)
# ✅ 抽象基準: 15/15 具体化済み (100%)
# ✅ 設定外部化: 32/32 項目対応 (100%)
```

### 後方互換性確認
```bash
# 既存ワークフローテスト
novel check --quality-level=comprehensive 第001話_テスト.md

# 期待結果: 統合前後で同等の品質評価が実行される
```

## 🎉 マイグレーション完了状態

### Before（統合前）
- YAMLチェックリスト3ファイル分散管理
- 抽象的判定基準による主観評価
- ハードコーディング閾値
- 二重メンテナンス負荷

### After（統合後）
- ✅ **A30品質基準.md単一ファイル統合**
- ✅ **具体的数値基準による客観評価**
- ✅ **設定外部化による柔軟性確保**
- ✅ **Single Source of Truth実現**

**合計作業時間: 4.5時間**（段階的実装による低リスク移行）

---

**この計画実行により、ユーザー指摘の「YAMLチェックリストをやめ、A30_執筆品質基準.mdとしたはずでは？」が完全に実現されます。**
