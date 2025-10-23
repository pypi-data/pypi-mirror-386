# A28 Case Study: 転機型導入の実例 (Draft)

**Purpose**: A28_話別プロットプロンプト.md に追加するセクション
**Based on**: Accel World 第1話の構造分析
**Target Location**: A28 Stage 2 の後、または独立した付録セクション

---

## Case Study: 転機型導入の実例 (Accel World 第1話)

### 概要

この Case Study では、川原礫『Accel World』第1話を題材に、転機型導入パターンの構造を分析します。このパターンは以下の特徴を持ちます:

- **即座の共感獲得**: 冒頭3段落で主人公の弱点を明示
- **明確な転換点**: before_state → transition (trigger event) → after_state の構造化
  - Note: A28用語準拠。transition = 状態変化、trigger event = 変化を引き起こす具体的出来事
- **二重の動機**: 外的目的(生存)+ 内的欲求(承認)
- **行動による世界観説明**: 地の文説明を避け、体験シーンで設定提示
- **感情曲線の明確化**: 絶望→驚き→期待 の起伏

---

## 1. 主人公の現状と弱点 (冒頭2-3段落)

### 構造

```yaml
Opening Scene:
  設定: "主人公の日常と社会的立場"
  提示する弱点:
    - 社会的弱点: "いじめ被害者という立場"
    - 内的弱点: "自己評価の低さ、逃避癖"

  効果:
    - 読者の共感を即座に獲得
    - 成長の起点を明確化
    - 次の転機への期待を醸成
```

### 実装パターン

**Accel World の実例:**
- **社会的弱点**: 学校でのいじめ、居場所のなさ
- **内的弱点**: "自分は価値がない" という自己認識
- **日常の描写**: ゲームセンターでの逃避行動

**noveler 18-step での実装:**
```yaml
Step 3 (キャラクター設定):
  Layer 1 (心理基盤):
    根本的動機: "承認欲求 - 誰かに必要とされたい"
    価値観: "自分は弱い存在だ"
    トラウマ: "過去のいじめ経験"
    成長方向: "自己肯定感の獲得"

  Layer 2 (外見・性格):
    第一印象: "太っていて目立たない、うつむきがち"
    口調: "自信なさげ、謝罪癖"

Step 12 (初稿執筆):
  冒頭3段落で以下を提示:
    - 主人公の日常(いじめ被害)
    - 逃避行動(ゲームセンター)
    - 内的独白("自分は...でしかない")
```

**A28 Stage 3 (シーン設計) での配置:**
```yaml
scene_structure:
  scenes:
    - scene_id: "scene_001"
      act_position: "act_1_opening"
      importance_rank: "S"
      estimated_words: 800
      scene_purpose: "主人公の弱点提示と共感獲得"
      key_moments:
        - "いじめシーンの短い描写(500字以内)"
        - "逃避行動(ゲームセンター)への移動"
        - "内的独白で自己評価の低さを明示"
      emotional_design:
        starting_emotion: "絶望/諦め"
        ending_emotion: "わずかな期待(次のシーンへの伏線)"
```

---

## 2. 外的事件の発生 (転換点)

### 構造

```yaml
Turning Point:
  基本情報:
    title: "運命の出会い - 能力の授与"
    timing: "第一幕終盤 (全体の20-25%地点)"
    trigger_event: "黒雪姫との出会いと Brain Burst の授与"
    catalyst: "主人公を助けたいという黒雪姫の意図"

  キャラクター変化:
    before_state:
      状態: "いじめられ、逃げるだけの日常"
      心境: "自分には価値がない"
      能力: "何もできない(と自認)"

    transformation_moment:
      描写: "時間停止の体験 - 世界が静止する瞬間"
      感情: "驚き、混乱、そして一瞬の解放感"
      決断: "この力で何かが変わるかもしれない"

    after_state:
      状態: "加速世界への転移"
      心境: "新しい可能性への期待と恐怖"
      能力: "Brain Burst の初期使用権"
```

### 実装パターン

**A28 Stage 2 (三幕構成) での記述:**
```yaml
turning_point:
  title: "能力授与による世界の転換"
  timing: "第一幕終盤"
  trigger_event: "黒雪姫が主人公に Brain Burst をインストール"
  catalyst: "主人公を助けたいという黒雪姫の意図"

  protagonist:
    before_state: "いじめられ、逃げるだけの日常。自己評価は最低。"
    transformation_moment: |
      時間停止を初体験するシーン。
      世界が静止し、初めて「自分だけの時間」を得る。
      驚きと混乱、そして一瞬の解放感。
    after_state: "加速世界への転移。新しい可能性への期待と不安。"

  emotional_journey:
    - stage: "恐怖/不安"
      description: "何が起きたのか分からない混乱"
    - stage: "決意/理解"
      description: "黒雪姫の説明を聞き、可能性を理解"
    - stage: "希望/成長"
      description: "この力で変われるかもしれない、という期待"

  structural_function:
    setup_payoff: "第一幕で提示した弱点(いじめ被害)への初回答"
    conflict_resolution: "逃げるだけの日常からの脱却の糸口"
    foreshadowing_planted:
      - "加速世界のルールと危険性"
      - "黒雪姫の真の目的"
      - "主人公が助けるべき存在(黒雪姫)の提示"
```

**noveler 18-step での実装:**
```yaml
Step 6 (転機設計):
  転機の配置: "scene_002 終盤(全体の20-25%地点)"
  before_state → transition → after_state の明示:
    before_state: "いじめ被害者、自己評価低"
    transition: "Brain Burst 授与 (trigger event: 黒雪姫との出会い)"
    after_state: "加速世界への転移、新しい可能性"

  Note: A28用語。transformation_moment = transition の詳細描写。

Step 7 (対話設計):
  黒雪姫との対話で以下を明示:
    - Brain Burst の基本ルール(行動説明の一部)
    - 主人公が選ばれた理由(承認欲求への応答)
    - 次の目標提示(外的目的の設定)

Step 8 (感情曲線):
  emotion_curve:
    - point: "転機前"
      level: 2  # 絶望
    - point: "転機中(時間停止体験)"
      level: 7  # 驚き/解放感
    - point: "転機後(説明聞く)"
      level: 5  # 期待と不安の混在
```

---

## 3. 目的の二重化

### 構造

```yaml
Dual Motivation:
  外的目的 (External Goal):
    内容: "いじめからの解放"
    性質: "客観的、達成可能"
    機能: "ストーリー駆動力"

  内的欲求 (Internal Desire):
    内容: "黒雪姫を助けたい(恩返し)"
    性質: "心理的、感情的"
    機能: "キャラクター成長軸"

  統合:
    synergy: "両者が「戦う理由」として統一"
    conflict: "自己保存(逃げたい)と恩返し(戦いたい)の葛藤"
```

### 実装パターン

**A24 キャラクター設計での記述:**
```yaml
characters:
  main_character:
    character_goals:
      external: "いじめから逃れる(生存欲求)"
      internal: "黒雪姫を助ける(承認欲求/恩返し)"
      conflict: "逃げたい(安全) vs 戦いたい(恩返し)"

    growth_arc:
      starting_state: "逃げることしか考えていない"
      transformation_catalyst: "黒雪姫の信頼と期待"
      ending_state: "誰かのために戦う意志の芽生え"
```

**A28 Stage 3 での配置:**
```yaml
scene_structure:
  scenes:
    - scene_id: "scene_003"
      scene_purpose: "二重動機の明示"
      key_moments:
        - "外的目的: いじめっ子からの逃走成功(Brain Burst使用)"
        - "内的欲求: 黒雪姫への感謝と恩返しの決意"
      dialogue_highlights:
        - "「君を...守りたい」(内的欲求の表明)"
        - "「もう逃げない」(外的目的からの転換)"
```

**noveler Post-Apply Review での確認:**
```yaml
二重動機チェック:
  - [ ] 外的目的が第1話で明示されているか？
        → いじめからの解放が scene_002 で提示されているか確認

  - [ ] 内的欲求が行動の選択理由として機能しているか？
        → 黒雪姫を助けるという動機が scene_003 で表明されているか

  - [ ] 両者が矛盾せず、相互に強化し合っているか？
        → "戦う理由" として統一されているか確認
```

---

## 4. 行動による世界観説明

### 構造

```yaml
World Building via Action:
  原則: "説明するな、体験させろ (Show, Don't Tell)"

  禁止パターン:
    - "Brain Burst は時間を止める能力である" (地の文説明)
    - "加速世界にはルールがある" (抽象的説明)

  推奨パターン:
    - 時間停止の体験シーン (主人公の五感で体験)
    - 加速世界への転移 (視覚的・感覚的描写)
    - ルール説明は対話に織り込む (黒雪姫の説明)
```

### 実装パターン

**Accel World の実例:**

**NG例 (地の文説明):**
```
Brain Burst は時間を止める能力だ。
使用者は1000倍に加速された思考で行動できる。
ただし、使用回数には制限がある。
```

**OK例 (行動・五感描写):**
```
世界が――止まった。
音が消え、人々の動きが凍りつく。
自分だけが動ける。この感覚は...
「これが、Brain Burst」
黒雪姫の声だけが聞こえる。
```

**noveler 18-step での実装:**
```yaml
Step 10 (五感設計):
  triggers:
    - trigger_id: "TRIGGER_001"
      sense_type: "visual + auditory"
      description: "時間停止の瞬間 - 音が消え、世界が静止"
      intensity: 9  # 強烈なインパクト
      timing: "転機の瞬間"
      purpose: "Brain Burst の能力を体験で説明"
      character_reaction: "驚き、混乱、そして理解"

    - trigger_id: "TRIGGER_002"
      sense_type: "kinesthetic + visual"
      description: "加速世界への転移 - 体が軽くなる感覚、色彩の変化"
      intensity: 8
      timing: "転機直後"
      purpose: "加速世界のルールを感覚で提示"

Step 12 (初稿執筆):
  世界観説明の配置:
    - scene_002: 時間停止の体験 (TRIGGER_001)
    - scene_003: 加速世界への転移 (TRIGGER_002)
    - scene_003: 黒雪姫の対話でルール補足(最小限)
```

**A28 Stage 3 での配置:**
```yaml
scene_structure:
  scenes:
    - scene_id: "scene_002"
      scene_purpose: "Brain Burst の能力を体験で説明"
      key_moments:
        - "時間停止の体験 (視覚・聴覚描写)"
        - "主人公の混乱と理解"
      避けるべき表現:
        - "AはBである" 形式の説明文
        - 神の視点的な情報説明

    - scene_003:
      scene_purpose: "加速世界のルールを対話で補足"
      dialogue_highlights:
        - "「これは...仮想現実?」(主人公の推測)"
        - "「そう、でも死ねば現実でも...」(黒雪姫の警告)"
      # 対話に必要最小限のルール説明を織り込む
```

**noveler Post-Apply Review での確認:**
```yaml
行動説明チェック:
  - [ ] "AはBである" 形式の説明文を使っていないか？
        → fix_quality_issues で EXPLANATION_HEAVY 検出(将来機能)

  - [ ] 世界観を主人公の体験/五感で説明しているか？
        → enhanced_execute_writing_step 10 (五感設計) の配置確認

  - [ ] 対話での説明は必要最小限か？
        → 1シーンあたり説明的対話は3行以内を目安
```

---

## 5. 感情曲線の設計

### 構造

```yaml
Emotional Curve (Three-Act Structure):
  Act 1 (導入):
    emotion_level: 2-3  # 絶望/諦め
    purpose: "読者の共感獲得、現状の低さを強調"

  Act 2 (転機):
    emotion_level: 7-8  # 驚き/解放感
    purpose: "カタルシス、変化の実感"

  Act 3 (次への期待):
    emotion_level: 5-6  # 期待と不安の混在
    purpose: "次話への引き、新たな目標提示"

  変化幅: 5-6ポイント (2→8→5 の起伏)
```

### 実装パターン

**A28 Stage 2 での記述:**
```yaml
emotion_curve:
  - point: "導入(act_1)"
    emotion_type: "絶望/諦め"
    level: 2
    description: "いじめ被害、居場所のなさ"

  - point: "転機(act_2_climax)"
    emotion_type: "驚き/解放感"
    level: 8
    description: "時間停止体験、初めての自分だけの時間"

  - point: "次への引き(act_3)"
    emotion_type: "期待と不安"
    level: 5
    description: "新しい世界への転移、黒雪姫への決意"

emotion_tech_fusion:  # 技術要素を含む作品の場合
  peak_moments:
    - timing: "第二幕クライマックス"
      emotion_type: "驚き→理解→解放感"
      tech_concept: "時間加速のメカニズム"
      synergy_effect: "技術的驚きと感情的カタルシスが重なる"
```

**noveler 18-step での実装:**
```yaml
Step 8 (感情曲線追跡):
  emotions:
    - trigger_id: "DL001"  # いじめシーン
      viewpoint: "主人公"
      target_character: "主人公"
      observation_type: "内面描写"
      before_level: 2
      after_level: 2
      emotion_type: "絶望/諦め"

    - trigger_id: "DL005"  # 時間停止体験
      viewpoint: "主人公"
      target_character: "主人公"
      observation_type: "内面描写"
      before_level: 2
      after_level: 8
      emotion_type: "驚き/解放感"

    - trigger_id: "DL010"  # 加速世界への転移
      viewpoint: "主人公"
      target_character: "主人公"
      observation_type: "内面描写"
      before_level: 8
      after_level: 5
      emotion_type: "期待と不安"
```

**noveler Post-Apply Review での確認:**
```yaml
感情曲線チェック:
  - [ ] 導入(低)→転機(高)→次への期待 の起伏があるか？
        → emotion_level の変化幅が±2以上か確認

  - [ ] カタルシスの位置が第二幕終盤にあるか？
        → 全体の60-70%地点に最高点があるか

  - [ ] 次話への引きが明確か？
        → 最終シーンの emotion_level が5-6(中程度の期待)か
```

---

## noveler への適用まとめ

### 1. A28 (話別プロット) での活用

**Stage 2 (三幕構成設計) での記入:**
```yaml
# 上記の turning_point / emotion_curve / emotion_tech_fusion を参照
# 特に before_state / transformation_moment / after_state を明示
```

**Stage 3 (シーン肉付け) での配置:**
```yaml
scene_structure:
  scenes:
    - scene_001: "主人公の弱点提示" (importance_rank: A)
    - scene_002: "転機 - 能力授与" (importance_rank: S)
    - scene_003: "二重動機の明示" (importance_rank: A)
    - scene_004: "行動による世界観説明" (importance_rank: A)
    - scene_005: "次への引き" (importance_rank: B)
```

### 2. 18-Step Workflow での実装順序

```yaml
推奨実行順序:
  Step 3: キャラクター設定 (弱点/欠点を明確化)
  Step 6: 転機設計 (before_state → transition → after_state 構造化)
  Step 7: 対話設計 (外的目的+内的欲求を明示)
  Step 8: 感情曲線 (導入→転機→期待 の起伏設計)
  Step 10: 五感設計 (世界観を行動で説明)
  Step 11: 伏線配置
  Step 12: 初稿執筆 (上記をすべて統合)
```

### 3. Post-Apply Review での検証

**noveler_write.md の Gate W1 を使用:**
```yaml
物語構造の5要素チェック:
  - 弱点提示: scene_001 で明示されているか
  - 転機構造: scene_002 で before_state → transition → after_state が明確か
  - 二重動機: scene_003 で外的+内的が揃っているか
  - 行動説明: 地の文説明が最小限か
  - 感情曲線: emotion_level の変化幅が±2以上か
```

### 4. 失敗時の対処 (Troubleshooting)

**noveler_write.md の Troubleshooting セクションを参照:**
- 転機が弱い → Step 6 再実行
- 共感できない → Step 3 再実行
- 説明的 → Step 10 再実行
- 感情平坦 → Step 8 再実行

---

## 他のパターンへの応用

### パターン2: ミステリー型導入

```yaml
Structure:
  1. 謎の提示 (冒頭)
  2. 主人公の参入 (転機)
  3. 調査の動機 (二重動機: 真相究明+個人的理由)
  4. 手がかりの収集 (行動)
  5. 次の謎への引き

Reference: A28 Stage 2 で turning_point を "謎との遭遇" に設定
```

### パターン3: 日常崩壊型導入

```yaml
Structure:
  1. 平和な日常描写 (冒頭)
  2. 突然の崩壊 (転機)
  3. 生存と再建の目的 (二重動機)
  4. 新ルールの体験的理解 (行動)
  5. 次の脅威への引き

Reference: A28 Stage 2 で emotion_curve を "高→低→中" に設定
```

---

## Checklist: 転機型導入パターンの適用確認

### A28 (話別プロット) レベル
- [ ] Stage 2 で `turning_point` の詳細構造を記入したか
- [ ] `emotion_curve` が "低→高→中" の起伏を持つか
- [ ] Stage 3 で `scene_structure` に5要素を配置したか

### 18-Step Workflow レベル
- [ ] Step 3 で主人公の弱点を明確化したか
- [ ] Step 6 で before_state → transition → after_state を構造化したか
- [ ] Step 7 で外的目的+内的欲求を明示したか
- [ ] Step 10 で世界観を五感設計に織り込んだか
- [ ] Step 8 で感情レベル変化幅が±2以上か

### Post-Apply Review レベル
- [ ] noveler_write.md の Gate W1 を実行したか
- [ ] 5要素すべてが合格したか
- [ ] 不合格項目は該当 Step を再実行したか

---

**Status**: Draft for Codex Review
**Insertion Point**: A28_話別プロットプロンプト.md Stage 5 の後、または独立付録
**Related**: noveler_write.md (Post-Apply Review), A24 (目的設定)
