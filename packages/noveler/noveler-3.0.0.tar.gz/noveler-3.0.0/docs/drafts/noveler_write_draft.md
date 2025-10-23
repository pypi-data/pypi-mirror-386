# noveler_write.md - Draft for Review

**Version**: 1.0.0 (Draft)
**Purpose**: MCP-driven 18-step writing workflow with narrative structure validation
**Target**: `.claude/commands/noveler_write.md` (new slash command)

---

## Overview

This slash command provides a unified interface for executing the 18-step writing workflow defined in the Noveler MCP system, with added narrative structure validation based on proven story patterns (Accel World analysis).

## Core Philosophy

**Before polish, ensure structure; before structure, clarify intent.**

- Creative intentions must be explicit before execution
- Structural elements (弱点/転機/動機/世界観/感情曲線) are validated post-apply
- Failed validation → targeted step re-execution, not full rewrite

---

## Usage Patterns

### Pattern 1: Preview & Verify (Recommended)
```
/noveler write <episode> --mode preview
→ Review creative intention checklist
→ Run polish_manuscript with dry_run=true
→ Check structural elements
→ Apply only if all pass
```

### Pattern 2: Direct Apply (Risk: structural issues discovered late)
```
/noveler write <episode> --mode apply
→ Runs polish_manuscript apply immediately
→ Post-apply structural check
→ Manual fix if issues found
```

### Pattern 3: Iterative Improvement
```
/noveler improve <episode> --target-score 80
→ Runs improve_quality_until with aspects=[rhythm, readability, grammar]
→ Auto-fixes via fix_quality_issues
→ Repeats until target score reached
```

---

## Creative Intention (5-Point Check)

**MUST be confirmed before enhanced_execute_writing_step 11 (初稿) or polish_manuscript:**

```yaml
Creative Intention (記入必須):
  1. Scene Goal: <このシーンで達成すべき物語上の目標>
     例: "主人公の弱点を冒頭で明示し、読者の共感を獲得"

  2. Emotional Goal: <読者に抱かせたい感情(共感/驚き/期待など)>
     例: "絶望→驚き→期待 の感情曲線"

  3. Character Arc: <主人公の変化>
     構造: before_state → transition (trigger event) → after_state
     例: "いじめ被害者 → 能力獲得(転機) → 加速世界への転移"

     Note: A28用語では「transition」を使用。trigger event は転機を引き起こす具体的出来事。

  4. World Building Strategy: <どの設定要素を、どの行動/五感描写で見せるか>
     例: "時間停止のルールを、主人公の体験シーンで説明(地の文禁止)"

  5. Voice Constraints: <人称/時制/禁止表現(地の文説明など)>
     例: "三人称単一視点/過去形/「AはBである」形式の説明文禁止"
```

**Reference:**
- A28_話別プロットプロンプト.md (転換点設計 - Stage 2)
- A24_キャラクター設計ガイド.md (成長軸設計 - Step 2)

### Creative Intention Lite版 (1分記入テンプレート)

**推奨**: 毎回の執筆前に負担を軽減するため、各項目30-60字のライト版を使用。

```yaml
Lite Template (1分記入版):
  1. Scene Goal: <30-60字で簡潔に>
     例: "主人公の弱点を冒頭で明示し共感獲得"

  2. Emotional Goal: <感情変化を1行で>
     例: "絶望→驚き→期待"

  3. Character Arc: <before/transition/after を各10字程度で>
     例: "いじめ被害者 → 能力獲得 → 新世界転移"

  4. World via Action: <説明禁止の具体策1つ>
     例: "時間停止を体験シーンで提示"

  5. Voice: <禁止表現を1つ明記>
     例: "「AはBである」形式禁止"
```

**使用タイミング:**
- Step 12 (初稿執筆) 直前
- polish_manuscript preview 実行前

**詳細版との使い分け:**
- Lite版: 日常的な執筆前チェック (毎回)
- 詳細版 (上記): 重要エピソード or 構造的問題発生時

---

## Workflow Commands

### 1. Polish Manuscript (Stage 2/3 推敲)

```bash
# Preview mode (dry_run=true, diff preview)
/noveler write <episode> --polish preview

# Apply mode (automatic application)
/noveler write <episode> --polish apply

# Custom stages
/noveler write <episode> --polish apply --stages stage2
```

**Internal Mapping:**
- `preview` → `polish_manuscript(episode, dry_run=true, include_diff=false)`
- `apply` → `polish_manuscript_apply(episode, dry_run=false, save_report=true)`

**Stages:**
- `stage2`: 内容推敲 (content refinement)
- `stage3`: 読者体験推敲 (reader experience optimization)

**Output:**
- Artifact ID (e.g., `artifact:a1b2c3d4`) for restored manuscript
- Brief summary of changes
- Optional: short diff (if `include_diff=true`, max 400 lines)

---

### 2. Quality Check & Auto-Fix

```bash
# Run quality checks (rhythm/readability/grammar)
/noveler check <episode> --aspects rhythm,readability

# Auto-fix safe issues (dry_run=true by default)
/noveler fix <episode> --apply

# Iterative improvement until target score
/noveler improve <episode> --target-score 80 --max-iterations 3
```

**Internal Mapping:**
- `check` → `run_quality_checks(episode, aspects=[...], format='summary')`
- `fix` → `fix_quality_issues(episode, dry_run=false)`
- `improve` → `improve_quality_until(episode, target_score=80)`

**Safe Auto-Fix Reason Codes (default):**
- `ELLIPSIS_INCONSISTENCY` (三点リーダー統一)
- `DASH_INCONSISTENCY` (ダッシュ統一)
- `SPACE_AROUND_PUNCTUATION` (句読点前後スペース削除)
- `EMPTY_LINE_RUNS` (連続空行削除)

**Manual Review Required:**
- `LONG_SENTENCE` (長文分割 - 文意変更リスク)
- `SHORT_SENTENCE_RUN` (短文連結 - テンポ変更リスク)
- `COMMA_OVERUSE` (読点過多 - 文構造変更リスク)

---

### 3. Execute Specific Writing Step

```bash
# Execute individual step (e.g., step 6 = 転機設計)
/noveler step <episode> <step_id>

# With dry-run
/noveler step <episode> <step_id> --dry-run
```

**Internal Mapping:**
- `step` → `enhanced_execute_writing_step(episode, step_id, dry_run=false)`

**Key Steps:**
- Step 3: キャラクター設定
- Step 6: 転機設計
- Step 7: 対話設計
- Step 8: 感情曲線
- Step 10: 五感設計
- Step 11: 伏線配置
- Step 12: 初稿執筆

---

## Post-Apply Review (Gate W1 - 構造チェック)

**MUST be checked after polish_manuscript apply:**

### 合格基準 (定量化)

```yaml
Pass Criteria:
  - 最小合格ライン: 5要素中 **4要素以上が Pass** (4/5以上)
  - Fail項目: 該当 Step を再実行後、polish 再適用
  - 感情曲線の特別基準:
      変化幅: ±2以上 (emotion_level の差)
      ピーク位置: 全体の60-70%地点 (第二幕終盤)

Scoring:
  - Pass: 該当要素が明確に存在し、機能している
  - Warn: 該当要素が存在するが、やや弱い or 配置が不適切
  - Fail: 該当要素が欠落、または機能していない

Gate判定:
  - All Pass (5/5): Gate W1 通過 → G系品質ゲートへ進む
  - **4 Pass + 1 Warn: 条件付き通過** → Warn項目を記録し、次話で改善
  - 3 Pass以下 or 1 Fail以上: Gate W1 不合格 → 該当Step再実行必須
```

### 物語構造の5要素チェック

```yaml
Checklist:
  - [ ] 弱点提示: 主人公の欠点/弱点を冒頭3段落以内で提示したか？
        → 失敗時: enhanced_execute_writing_step 3 (キャラクター設定) を再実行

  - [ ] 転機構造: 転換点で before_state → transition → after_state が明確か？
        → 失敗時: enhanced_execute_writing_step 6 (転機設計) を再実行

        Note: transition = 転換そのもの、trigger event = 転換を引き起こす出来事

  - [ ] 二重動機: 主人公の行動理由が外的目的+内的欲求の両面から伝わるか？
        → 失敗時: A24_キャラクター設計ガイド.md の目的設定セクションを参照

  - [ ] 行動説明: 世界観を地の文でなく、行動/対話/五感に織り込んだか？
        → 失敗時: enhanced_execute_writing_step 10 (五感設計) を再実行

  - [ ] 感情曲線: 導入(低)→転機(高)→次への期待 の起伏があるか？
        → 失敗時: enhanced_execute_writing_step 8 (感情曲線) を再実行
```

**Verification Method:**
1. `run_quality_checks` で rhythm/readability を確認 (基礎品質)
2. 上記5要素を手動確認 (物語構造)
3. 不合格項目があれば該当stepを再実行→polish再適用

**Reference Implementation:** Accel World 第1話
詳細は A28_話別プロットプロンプト.md の Case Study 参照 (追加予定)

---

## Troubleshooting (構造的問題への対処)

### 症状別の対処法

#### "転機が弱い" / "変化が伝わらない"
```
原因: turning_point の before_state/transition/after_state が不明瞭
対処: enhanced_execute_writing_step 6 (転機設計) を dry_run=false で再実行
手順:
  1. A28 Stage 2 の turning_point 詳細構造を参照
  2. before_state/transition (trigger event)/after_state を明示的に記述
  3. polish_manuscript で再推敲

Note: A28では transformation_moment と transition を使用。trigger event は転機の発火点。
```

#### "主人公に共感できない"
```
原因: 主人公の弱点/欠点が冒頭で提示されていない
対処: enhanced_execute_writing_step 3 (キャラクター) で弱点/欠点を追加
手順:
  1. A24 の Layer 1 心理基盤を確認
  2. 冒頭3段落に現状の苦悩を挿入
  3. 弱点と目的を結びつける
```

#### "世界観が説明的"
```
原因: "AはBである" 形式の地の文説明
対処: enhanced_execute_writing_step 10 (五感設計) で行動に置き換え
手順:
  1. 説明的な文をリストアップ
  2. 主人公の体験/対話/五感描写として再構成
  3. fix_quality_issues で EXPLANATION_HEAVY を検出(将来機能)
```

#### "感情の起伏がない"
```
原因: emotion_curve の設計が平坦
対処: enhanced_execute_writing_step 8 (感情曲線) でトリガーID見直し
手順:
  1. 各シーンの emotion_level 変化幅を±2以上に設定
  2. カタルシスの位置を第二幕終盤に配置
  3. 感情×技術の二重トラック(該当作品のみ)を確認
```

#### "polish後もスコアが上がらない"
```
原因: 自動修正不可能な構造的問題
対処: 段階的改善フロー
手順:
  1. fix_quality_issues で自動修正可能な項目を先に処理
  2. improve_quality_until で段階的改善 (target_score=80)
  3. 各アスペクト(rhythm→readability→grammar)を順次攻略
  4. 手動修正が必要な issue_id をリストアップ
```

---

## Workflow Templates (Narrative Patterns)

### 転機型導入 (Accel World型)

**Structure:**
1. 主人公の現状と弱点 (2-3段落)
2. 外的事件の発生 (転換点)
3. 新しい目的の提示
4. 行動による世界観説明
5. 次話への引き (疑問/期待)

**Usage:**
- `polish_manuscript preview` 時に上記5要素の有無を確認
- `enhanced_execute_writing_step 11` (初稿) 前にテンプレート選択

**Example Mapping to 18-Step Workflow:**
```yaml
Step 3 (キャラクター設定):
  output: "主人公の弱点/欠点を明確化"

Step 6 (転機設計):
  output: "before_state → transition (trigger event) → after_state の構造化"

  Note: transition = 状態変化、trigger event = 変化を引き起こす具体的出来事

Step 7 (対話設計):
  output: "外的目的+内的欲求を対話に織り込む"

Step 10 (五感設計):
  output: "世界観を行動/五感描写で説明"

Step 8 (感情曲線):
  output: "導入→転機→期待 の起伏設計"
```

---

## Integration with Existing Tools

### A28 (話別プロット) との連携
- Stage 2 の `turning_point` 詳細構造を参照
- `emotion_tech_fusion` (技術要素を含む作品) を確認
- `scene_structure` の重要度Sランクシーンを特定

### A24 (キャラクター設計) との連携
- Layer 1 心理基盤を確認
- 目的設定の二重動機 (外的目的+内的欲求) を検証
- 心理モデル要約をLLM入力に使用

### A34 (一気通貫実践) との連携
- `novel check 4` (キャラクター整合性) と連動
- `novel write` コマンドのサブセットとして機能
- 品質ゲートとの統合 (将来実装)

---

## Future Features (docs/future_features/narrative_structure_check.md 参照)

### 自動構造診断
- `polish_manuscript preview` 段階で5要素の有無を自動判定
- LLMベースの構造分析
- 早期警告メッセージ生成

### 統合品質ゲート
- `run_quality_checks` に新アスペクト `narrative_structure` 追加
- 物語構造スコア (0-100) の算出
- 基礎品質 (rhythm/readability) と構造品質の両面評価

---

## Examples

### Example 1: Preview → Verify → Apply
```bash
# Step 1: Preview changes
/noveler write 1 --polish preview

# Step 2: Check creative intention
# (Manual review of 5-point checklist)

# Step 3: Verify structure
/noveler check 1 --aspects rhythm,readability

# Step 4: Apply if all pass
/noveler write 1 --polish apply
```

### Example 2: Fix Structural Issue (転機が弱い)
```bash
# Step 1: Identify issue via Post-Apply Review
# → 転機構造が不明瞭

# Step 2: Re-execute step 6 (転機設計)
/noveler step 1 6

# Step 3: Re-apply polish
/noveler write 1 --polish apply
```

### Example 3: Iterative Improvement
```bash
# Step 1: Check current score
/noveler check 1 --aspects rhythm,readability,grammar --format summary

# Step 2: Improve until target score
/noveler improve 1 --target-score 80 --max-iterations 3

# Step 3: Verify final score
/noveler check 1 --format summary
```

---

## Output Format

All commands follow B20 output contract:
- **JSON mode**: Machine-readable with `artifact_id`, `file_hash`, `issue_id`
- **Summary mode**: Human-readable brief summary (default for slash commands)
- **Diff mode**: Short diff preview (max 400 lines, optional)

---

## Notes

- **Dry-run default**: Most commands default to `dry_run=true` for safety
- **Artifact storage**: All manuscripts stored in `.noveler/artifacts/` with SHA256 hash
- **Undo support**: Use `restore_manuscript_from_artifact` to rollback
- **Cross-reference**: All file paths use `artifact:` or `file_hash:` for lightweight output

---

**Last Updated**: 2025-10-09
**Status**: Draft for Codex Review
**Related Specs**: SPEC-CLI-050 (Slash Command Management), A28 (Plot), A24 (Character)
