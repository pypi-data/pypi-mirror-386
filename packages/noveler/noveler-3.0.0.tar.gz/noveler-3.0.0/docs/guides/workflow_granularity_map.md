# ワークフロー粒度マップ (Workflow Granularity Map)

**Purpose**: A28 Stage / 18-Step Workflow / Gates (W/G) の対応関係を明示
**Version**: 1.0.0
**Last Updated**: 2025-10-09

---

## 📊 粒度の定義

### 3層構造

```yaml
Layer 1 - Stage (A28):
  粒度: 粗い (大きなフェーズ)
  範囲: プロット設計の5段階
  目的: 話別プロット全体の構造設計
  対象: エピソード全体の青写真

Layer 2 - Step (18-Step Workflow):
  粒度: 中間 (個別作業単位)
  範囲: 執筆作業の18ステップ
  目的: 具体的な執筆タスクの実行
  対象: シーン/キャラ/対話など個別要素

Layer 3 - Gate (W系/G系):
  粒度: 細かい (検証ポイント)
  範囲: 作業完了後の検証
  目的: 品質保証とサニティチェック
  対象: 成果物の合否判定
```

---

## 🗺️ A28 Stage → 18-Step Workflow マッピング

### Stage 1: 骨格構築

**A28 作業内容:**
- episode_number / title / chapter_number 転記
- theme / purpose / emotional_core 設計
- viewpoint 指定
- synopsis 作成 (380-420字)
- key_events 設計 (2つ以上)

**対応する 18-Step:**
```yaml
Step 1: プロジェクト初期化
  - エピソード番号・タイトル設定

Step 2: 世界観・舞台設定
  - viewpoint (視点キャラクター) 指定
  - 舞台・時代背景の確認

(参考: Step 3-11 は Stage 2-3 で詳細化)
```

---

### Stage 2: 三幕構成の設計

**A28 作業内容:**
- setup / confrontation / resolution 設計
- emotion_curve 設計 (高→低→高)
- emotion_tech_fusion (該当作品のみ)
- turning_point 詳細構造:
  - 基本情報 (title/timing/trigger_event/catalyst)
  - キャラクター変化 (before_state/transition/after_state)
  - 感情アーク (emotional_journey)
  - 構造的機能 (setup_payoff/conflict_resolution/foreshadowing_planted)

**対応する 18-Step:**
```yaml
Step 6: 転機設計 (Turning Point Design)
  - before_state / transition (trigger event) / after_state の構造化
  - A28 の turning_point 詳細構造を実装

Step 8: 感情曲線追跡 (Emotion Curve Tracking)
  - A28 の emotion_curve を emotion_level で数値化
  - 変化幅±2以上を確保

Step 12: テーマ設計
  - A28 の theme / purpose / emotional_core を深掘り
```

**Note:** Stage 2 は Step 6/8/12 に分散して実装される。

---

### Stage 3: シーン肉付け

**A28 作業内容:**
- scene_structure 設計:
  - scene_id / act_position / importance_rank (S/A/B/C)
  - estimated_words / percentage
  - scene_purpose / key_moments / dialogue_highlights
- scene_balance_analysis (テンポ変化・バランススコア)
- viewpoint_consistency チェック
- characters 詳細化:
  - main_character (starting_state → arc → ending_state)
  - supporting_characters (関係性・役割)
- technical_elements / emotional_elements / reader_considerations

**対応する 18-Step:**
```yaml
Step 3: キャラクター設定
  - A28 の characters.main_character を実装
  - starting_state / arc / ending_state

Step 4: 関係性設計
  - A28 の supporting_characters を実装
  - 関係性・役割の明確化

Step 5: 背景設定
  - technical_elements (該当作品のみ) を確認

Step 7: 対話設計 (Dialogue Design)
  - A28 の dialogue_highlights を実装
  - 会話ID体系で対話構造を管理

Step 9: 情景設計 (Scene Design)
  - A28 の scene_structure を実装
  - 場所・時間・雰囲気の設計

Step 10: 五感設計 (Sensory Trigger Design)
  - A28 の emotional_elements を五感描写に変換
  - 感覚トリガーID体系で管理

Step 11: 初稿執筆
  - A28 Stage 1-3 の全要素を統合
  - scene_structure に従って執筆
```

**Note:** Stage 3 は Step 3/4/5/7/9/10/11 に広く分散。

---

### Stage 4: 技術・伏線統合

**A28 作業内容:**
- foreshadowing_tracker:
  - foreshadow_id / element / placement / significance
  - status (planted/referenced/resolved)
  - resolution_episode / dependency
- foreshadowing_analysis (矛盾チェック)
- plot_elements.themes 整理
- technical_elements.programming_concepts (該当作品)
- next_episode_connection 設計
- quality_checkpoints 明示

**対応する 18-Step:**
```yaml
(直接対応するStepなし - A28 Stage 4 は品質管理に近い)

参考実装:
  - Step 11 (初稿執筆) 完了後に A28 Stage 4 を実行
  - 伏線の配置確認・次話への引き設計
```

---

### Stage 5: 最終確認 & 出力整形

**A28 作業内容:**
- Stage 1-4 必須項目の検証
- synopsis 文字数確認 (380-420字)
- reader_response_prediction (読者反応予測)
- word_count_allocation (文字数配分)
- foreshadowing_final_check (伏線整合性)
- YAML 構文検証・整形

**対応する 18-Step:**
```yaml
Step 13: 品質チェック (一部)
  - A28 Stage 5 の検証項目を確認

Step 14-16: 推敲・校正・最終確認
  - word_count_allocation に従って調整

Step 17: 最終出力
  - A28 YAML と原稿の整合性確認

Step 18: アーカイブ・バックアップ
  - 完成版の保存
```

---

## 🚪 Gates (W系 / G系) との対応

### Gate分類

```yaml
W系ゲート (Work Sanity Gates):
  目的: 作業の完全性・構造的健全性の確認
  判定: Pass/Warn/Fail (構造要素の有無)
  タイミング: 作業完了直後
  対応: 不合格時は該当Stepを再実行

G系ゲート (Quality Gates):
  目的: 品質KPIの達成確認
  判定: スコア (0-100) + 閾値判定
  タイミング: W系ゲート通過後
  対応: 不合格時は改善→再検証
```

### Gate W0: プロット設計完了

**タイミング:** A28 Stage 5 完了後

**チェック項目:**
```yaml
- [ ] A28 Stage 1-5 の必須項目がすべて埋まっているか
- [ ] synopsis が380-420字で収まっているか
- [ ] turning_point 詳細構造が記載されているか
- [ ] scene_structure が定義され、重要度Sランクが存在するか
- [ ] YAML構文エラーがないか
```

**合格基準:** 上記5項目すべてPass

**不合格時:** 該当 Stage を再実行

---

### Gate W1: 構造サニティ (Post-Apply Review)

**タイミング:** Step 11 (初稿執筆) 完了後、または polish_manuscript apply 後

**チェック項目 (物語構造の5要素):**
```yaml
1. 弱点提示: 主人公の欠点/弱点が冒頭3段落で提示されているか
   → 対応Step: Step 3 (キャラクター設定)

2. 転機構造: before_state → transition → after_state が明確か
   → 対応Step: Step 6 (転機設計)

3. 二重動機: 外的目的 + 内的欲求が揃っているか
   → 対応Step: Step 3 (キャラ) + Step 7 (対話)

4. 行動説明: 世界観を地の文でなく行動/五感で説明しているか
   → 対応Step: Step 10 (五感設計)

5. 感情曲線: 導入(低) → 転機(高) → 期待(中) の起伏があるか
   → 対応Step: Step 8 (感情曲線)
```

**合格基準:**
- 最小合格ライン: 5要素中4要素以上が Pass
- 感情曲線の特別基準: 変化幅±2以上、ピーク位置60-70%

**不合格時:**
- Fail項目の対応Stepを再実行
- polish_manuscript を再適用

---

### Gate G0: 基礎品質チェック

**タイミング:** Gate W1 通過後

**チェック項目 (run_quality_checks):**
```yaml
Aspects:
  - rhythm: 文章リズム (文長連続/会話比率/語尾/読点密度)
  - readability: 読みやすさ (文長/難解語彙)
  - grammar: 文法・誤字脱字 (助詞誤り/表記揺れ/句読点)
  - style: 体裁・スタイル (空行/スペース/括弧)
```

**合格基準:**
- 各アスペクトで60点以上
- 総合スコア70点以上 (重み付き平均)

**不合格時:**
- fix_quality_issues で自動修正可能な項目を処理
- improve_quality_until でターゲットスコア(80)まで改善

---

### Gate G1: 総合品質達成

**タイミング:** Gate G0 通過後

**チェック項目:**
```yaml
- 総合品質スコア80点以上
- Critical/High重要度の問題が0件
- 読者配慮 (accessibility/engagement) が設計通り実装されているか
```

**合格基準:**
- 総合スコア80点以上
- Critical問題0件

**不合格時:**
- 該当問題を手動修正
- 再度 run_quality_checks で検証

---

## 📈 ワークフロー全体像

```
A28 Stage 1-5 (プロット設計)
  ↓
Gate W0 (プロット完了確認)
  ↓ Pass
18-Step Workflow (Step 1-11)
  ↓ Step 11 完了
Gate W1 (構造サニティ) ← noveler_write.md で実装
  ↓ Pass (4/5以上)
polish_manuscript (Stage 2/3 推敲)
  ↓
Gate W1 再確認
  ↓ Pass
Gate G0 (基礎品質)
  ↓ Pass (70点以上)
improve_quality_until (反復改善)
  ↓
Gate G1 (総合品質)
  ↓ Pass (80点以上)
完成・アーカイブ (Step 17-18)
```

---

## 🔄 粒度間の相互参照

### A28 → 18-Step

```yaml
A28で設計した内容を18-Stepで実装:
  - A28 turning_point → Step 6 で実装
  - A28 scene_structure → Step 9/11 で実装
  - A28 emotion_curve → Step 8 で数値化
  - A28 characters → Step 3/4 で詳細化
```

### 18-Step → Gates

```yaml
18-Stepの成果物をGatesで検証:
  - Step 11 完了 → Gate W1 (構造チェック)
  - polish後 → Gate W1 再確認
  - W1通過後 → Gate G0 (基礎品質)
  - G0通過後 → Gate G1 (総合品質)
```

### Gates → A28/18-Step (フィードバックループ)

```yaml
Gate不合格時の対応:
  - Gate W0 不合格 → A28 該当Stage を再実行
  - Gate W1 不合格 → 18-Step 該当Step を再実行
  - Gate G0/G1 不合格 → fix/improve で改善
```

---

## 📝 実用例

### 例1: 転機が弱い問題

```
問題発生: Gate W1 で「転機構造」がFail
↓
原因分析: before_state/transition/after_state が不明瞭
↓
対応: Step 6 (転機設計) を再実行
↓
再実装: A28 Stage 2 の turning_point 詳細構造を参照
↓
再検証: Gate W1 で「転機構造」がPass
↓
次へ: Gate G0 (基礎品質) に進む
```

### 例2: 品質スコア低下

```
問題発生: Gate G0 で rhythm が55点 (不合格)
↓
原因分析: 長文連続 (3箇所) + 読点過多 (5箇所)
↓
対応: fix_quality_issues で自動修正
↓
再検証: Gate G0 で rhythm が72点 (Pass)
↓
次へ: improve_quality_until でターゲット80点まで改善
```

---

## 🎯 まとめ

### 粒度の使い分け

```yaml
設計フェーズ (プロット):
  - A28 Stage 1-5 を使用
  - 大まかな構造を決定

実装フェーズ (執筆):
  - 18-Step Workflow を使用
  - 具体的な作業を実行

検証フェーズ (品質保証):
  - W系ゲート (構造サニティ)
  - G系ゲート (品質KPI)
```

### 棲み分けの原則

```yaml
重複なし:
  - A28 Stageは設計のみ、実装は18-Stepで行う
  - W系は構造、G系は品質で役割分離
  - 各層で明確な責任範囲

連携あり:
  - A28 → 18-Step: 設計を実装に落とし込む
  - 18-Step → Gates: 成果物を検証
  - Gates → A28/18-Step: フィードバックで改善
```

---

**Last Updated**: 2025-10-09
**Version**: 1.0.0
**Related**:
- A28_話別プロットプロンプト.md
- A30_執筆ワークフロー.md (W/Gゲート定義)
- noveler_write.md (Gate W1 実装)
