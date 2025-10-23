# A28 Case Study: 転機型導入パターンの実践ガイド

**Version**: 1.0.0
**Purpose**: A28 Template Loader Service を活用した転機型導入パターンの実装ガイド
**Based on**: Accel World 第1話の構造分析
**Related**:
- [A28 Template Loader Service](../../src/noveler/domain/services/a28_template_loader_service.py)
- [A28 Turning Point Template](../../src/noveler/domain/templates/a28_turning_point_template.yaml)
- [Workflow Granularity Map](workflow_granularity_map.md)
- [Draft Specification](../drafts/a28_case_study_draft.md) - 詳細な構造分析

---

## 📖 Overview

このガイドでは、**転機型導入パターン**（Turning Point Introduction Pattern）の実装方法を説明します。このパターンは、以下の5要素で構成されます:

### 5つの構造要素

1. **弱点提示** (Weakness Introduction): 冒頭3段落で主人公の弱点を明示
2. **転機構造** (Turning Point): before_state → transition → after_state の明確な変化
3. **二重動機** (Dual Motivation): 外的目的（生存・勝利）+ 内的欲求（承認・成長）
4. **行動説明** (Show-don't-tell): 地の文説明を避け、体験シーンで設定提示
5. **感情曲線** (Emotional Arc): 絶望→驚き→期待 の起伏

これらの要素は、[Gate W1 (構造サニティ)](workflow_granularity_map.md#gate-w1-構造サニティ-post-apply-review) で検証されます。

---

## 🛠️ A28 Template Loader Service の使い方

### 基本的な使い方

```python
from pathlib import Path
from noveler.domain.services.a28_template_loader_service import A28TemplateLoaderService

# サービスをインスタンス化
loader = A28TemplateLoaderService()

# テンプレートを読み込み
template_path = Path("src/noveler/domain/templates/a28_turning_point_template.yaml")
template_data = loader.load_template(template_path)

# 転機構造を取得
turning_point = template_data.turning_point
print(f"Title: {turning_point.title}")
print(f"Before: {turning_point.before_state}")
print(f"Transition: {turning_point.transition}")
print(f"After: {turning_point.after_state}")

# シーン構造を取得
for scene in template_data.scenes:
    print(f"Scene {scene.scene_id}: {scene.scene_purpose}")
```

### データ構造

#### A28TurningPointData

```python
@dataclass
class A28TurningPointData:
    title: str                         # 転機のタイトル
    timing: str                        # タイミング (e.g., "第一幕終盤 20-25%地点")
    trigger_event: str                 # 転機を引き起こす具体的出来事
    catalyst: str                      # 転機の触媒（他キャラの意図など）
    before_state: str                  # 転機前の状態
    transformation_moment: str         # 変化の瞬間（体験シーン）
    after_state: str                   # 転機後の状態
    emotional_journey: list[dict]      # 感情変化の段階
    structural_function: dict          # 構造的機能（setup/payoff等）
```

#### A28SceneData

```python
@dataclass
class A28SceneData:
    scene_id: str                      # シーンID (e.g., "scene_001")
    act_position: str                  # 幕の位置 (e.g., "act_1_opening")
    importance_rank: str               # 重要度 (S/A/B/C)
    estimated_words: int               # 推定文字数
    percentage: str                    # 全体に占める割合
    scene_purpose: str                 # シーンの目的
    key_moments: list[str]             # 重要な瞬間のリスト
    dialogue_highlights: list[dict]    # 重要な対話
    emotional_design: dict             # 感情設計
```

---

## 📋 実装チェックリスト

### Step 1: 弱点提示 (冒頭3段落)

**目標**: 読者の共感を即座に獲得

- [ ] 主人公の社会的弱点を提示 (いじめ/孤立/失敗など)
- [ ] 主人公の内的弱点を提示 (自己評価の低さ/逃避癖など)
- [ ] 日常シーンで自然に描写 (説明口調を避ける)
- [ ] 内的独白で自己認識を明示

**実装箇所**:
- **18-Step**: Step 3 (キャラクター設定) で Layer 1 (心理基盤) を定義
- **A28**: Stage 3 scene_structure で scene_001 (importance_rank: S) として配置

**Example from Template**:
```yaml
scene_001:
  scene_purpose: "主人公の弱点提示と共感獲得"
  key_moments:
    - "いじめシーンの短い描写(500字以内)"
    - "逃避行動(ゲームセンター)への移動"
    - "内的独白で自己評価の低さを明示"
  emotional_design:
    starting_emotion: "絶望/諦め"
    ending_emotion: "わずかな期待"
```

---

### Step 2: 転機構造の設計

**目標**: before_state → transition → after_state の明確な変化

- [ ] **Before State**: 転機前の状態を明確に定義
  - 心理状態、社会的立場、能力レベル
- [ ] **Transition (Trigger Event)**: 変化を引き起こす具体的出来事
  - 出会い/能力獲得/事件発生など
- [ ] **After State**: 転機後の状態を定義
  - 新しい世界への転移、能力の発現、視点の変化

**実装箇所**:
- **18-Step**: Step 6 (転機設計)
- **A28**: Stage 2 turning_point セクション

**Example from Template**:
```yaml
turning_point:
  title: "運命の出会い - 能力の授与"
  timing: "第一幕終盤 (全体の20-25%地点)"
  trigger_event: "黒雪姫との出会いと Brain Burst の授与"
  before_state: "いじめられ、逃げるだけの日常"
  transformation_moment: "時間停止を初体験するシーン"
  after_state: "加速世界への転移、新たな可能性の認識"
```

---

### Step 3: 二重動機の設定

**目標**: 外的目的 + 内的欲求の両立

- [ ] **External Goal** (外的目的): 客観的に達成可能な目標
  - 生存、勝利、問題解決など
- [ ] **Internal Desire** (内的欲求): 心理的・感情的な動機
  - 承認欲求、自己肯定感、トラウマ克服など

**実装箇所**:
- **18-Step**: Step 3 (キャラクター設定) Layer 1 (心理基盤)
- **Gate W1**: 二重動機チェック項目で検証

**Example from Template**:
```yaml
dual_motivation:
  external_goal:
    short_term: "レベル1から脱出"
    mid_term: "デュエルで勝利を重ねる"
    long_term: "黒雪姫の謎を解明"
  internal_desire:
    core_need: "承認欲求 - 誰かに必要とされたい"
    fear: "再び一人ぼっちに戻ること"
    growth_axis: "自己肯定感の獲得"
```

---

### Step 4: Show-don't-tell (行動説明)

**目標**: 地の文説明を避け、体験シーンで世界観を提示

- [ ] 世界観の説明を「体験シーン」に変換
  - ❌ 「AはBである」形式の説明文
  - ✅ 主人公が体験し、反応する描写
- [ ] 五感描写を活用
  - 視覚、聴覚、触覚、嗅覚、味覚
- [ ] 対話で設定を自然に提示
  - 説明口調を避け、自然な会話

**実装箇所**:
- **18-Step**: Step 10 (五感設計)
- **Creative Intention**: world_via_action フィールドで明示
- **Gate W1**: 行動説明チェック項目で検証

**Example**:
```yaml
# ❌ Bad: 説明口調
地の文: "Brain Burstは時間を停止させるアプリケーションである。"

# ✅ Good: 体験シーン
主人公の体験:
  1. 時間停止ボタンを押す
  2. 周囲の人々が動きを止める
  3. 驚愕と困惑の反応
  4. 徐々にルールを理解していく過程
```

---

### Step 5: 感情曲線の設計

**目標**: 絶望→驚き→期待 の起伏を作る

- [ ] **Starting Emotion** (導入): 絶望/諦め (感情レベル: 低)
- [ ] **Turning Point** (転機): 驚き/混乱 (感情レベル: 高)
- [ ] **Ending** (期待): 期待/決意 (感情レベル: 中)

**実装箇所**:
- **18-Step**: Step 8 (感情曲線追跡)
- **A28**: Stage 2 emotion_curve
- **Gate W1**: 感情曲線チェック（変化幅±2以上、ピーク位置60-70%）

**Example from Template**:
```yaml
emotion_curve:
  opening:
    position: "0-10%"
    level: 2  # 低
    emotion: "絶望/諦め"

  turning_point:
    position: "20-25%"
    level: 8  # 高
    emotion: "驚き/混乱"

  resolution:
    position: "90-100%"
    level: 6  # 中
    emotion: "期待/決意"
```

---

## 🔍 Gate W1 による検証

### 構造サニティチェック

[Gate W1](workflow_granularity_map.md#gate-w1-構造サニティ-post-apply-review) は、Step 11 (初稿執筆) 完了後、または `polish_manuscript_apply` 後に以下の5要素を検証します:

```yaml
Gate W1 (構造サニティ):
  1. 弱点提示: 主人公の欠点/弱点が冒頭3段落で提示されているか
  2. 転機構造: before_state → transition → after_state が明確か
  3. 二重動機: 外的目的 + 内的欲求が揃っているか
  4. 行動説明: 世界観を地の文でなく行動/五感で説明しているか
  5. 感情曲線: 導入(低) → 転機(高) → 期待(中) の起伏があるか

合格基準:
  - 最小合格ライン: 5要素中4要素以上が Pass
  - 感情曲線の特別基準: 変化幅±2以上、ピーク位置60-70%

不合格時:
  - Fail項目の対応Stepを再実行
  - polish_manuscript を再適用
```

---

## 🧪 テストとカバレッジ

### テストの実行

```bash
# A28 統合テスト (11 passed, 2 skipped)
python scripts/run_pytest.py tests/integration/test_a28_workflow.py -v

# カバレッジ: 92.74%
python scripts/run_pytest.py tests/integration/test_a28_workflow.py --cov=src/noveler/domain/services/a28_template_loader_service.py
```

### テストカバレッジ詳細

- **Template Loading**: ✅ YAML読み込み、バリデーション、型変換
- **Error Handling**: ✅ ファイル不在、フィールド欠損、型不一致
- **Data Structures**: ✅ A28TurningPointData, A28SceneData, A28TemplateData
- **18-Step Mapping**: ⏭️ Skipped (Future Feature)

---

## 📚 参考資料

### コアファイル

1. **Service Implementation**: [a28_template_loader_service.py](../../src/noveler/domain/services/a28_template_loader_service.py)
   - A28TemplateLoaderService クラス
   - データクラス定義 (A28TurningPointData, A28SceneData, A28TemplateData)

2. **Template YAML**: [a28_turning_point_template.yaml](../../src/noveler/domain/templates/a28_turning_point_template.yaml)
   - Accel World 実例テンプレート
   - 5要素の具体的実装パターン

3. **Integration Tests**: [test_a28_workflow.py](../../tests/integration/test_a28_workflow.py)
   - テンプレート読み込みテスト
   - エラーハンドリングテスト

### ガイド文書

- [Workflow Granularity Map](workflow_granularity_map.md) - A28/18-Step/Gates マッピング
- [Draft Specification](../drafts/a28_case_study_draft.md) - 詳細な構造分析
- [Noveler Write Draft](../drafts/noveler_write_draft.md) - Creative Intention 5-Point Check

---

## 🚀 次のステップ

### 実装フロー

1. **A28 Template Loader を使用してテンプレートを読み込み**
   ```python
   loader = A28TemplateLoaderService()
   template = loader.load_template(Path("path/to/template.yaml"))
   ```

2. **Creative Intention 5-Point Check を記入**
   - Scene Goal: シーンの物語上の目標
   - Emotional Goal: 読者に抱かせたい感情
   - Character Arc: before/transition/after
   - World via Action: Show-don't-tell 戦略
   - Voice Constraints: 人称/時制/禁止表現

3. **Step 11 (初稿執筆) を実行**
   - A28 テンプレートに従って執筆
   - 5要素を意識して構造化

4. **Gate W1 で構造サニティチェック**
   - 5要素中4要素以上が Pass
   - 不合格時は対応Stepを再実行

5. **polish_manuscript で推敲**
   - Stage 2: 内容推敲（文章の質）
   - Stage 3: 読者体験（読みやすさ）

---

**Last Updated**: 2025-10-10
**Version**: 1.0.0
**Status**: Implementation Complete (85% - Documentation Integration)
