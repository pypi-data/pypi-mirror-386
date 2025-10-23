# 物語構造の自動診断 (Future Feature Spec)

**Status**: Draft Specification (未実装)
**Target File**: `docs/future_features/narrative_structure_check.md`
**Priority**: Low (Phase 3)
**Related**: noveler_write.md (Gate W1), A28 (Case Study), A24 (目的設定)

---

## 概要

### 目的

`polish_manuscript preview` 段階で物語構造の5要素(弱点提示/転機/二重動機/行動説明/感情曲線)の有無を自動判定し、構造的問題を早期発見する。

### 背景

**現状の課題:**
- 構造的問題が `polish_manuscript apply` 後に発見される
- 手動での Post-Apply Review (Gate W1) が必要
- 問題発見→Step再実行→再polish の繰り返しで非効率

**改善目標:**
- Preview 段階で構造診断を自動実行
- 問題箇所と対処 Step を即座に提示
- Apply 前に修正完了し、手戻りを削減

---

## 機能仕様

### 1. 自動構造診断 (Narrative Structure Analysis)

#### 入力
```yaml
Input:
  - episode_number: int
  - file_path: Path (optional, defaults to episode_number)
  - project_root: Path (optional, defaults to env)
  - analysis_depth: str (optional, "basic" | "detailed", default: "basic")
```

#### 出力
```yaml
Output Format (JSON):
  structure_score: float  # 0-100 の総合スコア
  element_checks:
    - element_id: str  # "flaw_presentation", "turning_point", etc.
      element_name: str  # "弱点提示", "転機構造", etc.
      status: str  # "pass", "warn", "fail"
      score: float  # 0-100
      findings: List[str]  # 具体的な検出内容
      recommendations: List[str]  # 対処法
      related_step: int  # 修正すべき enhanced_execute_writing_step の番号

  summary:
    passed_elements: int
    warned_elements: int
    failed_elements: int
    overall_recommendation: str

  artifacts:
    analysis_id: str  # "analysis:XXXXXXXX" 形式
    timestamp: str
    llm_model: str  # 使用した LLM モデル
```

#### 実装方針

**Phase 1: ルールベース診断 (簡易版)**
```yaml
実装難易度: 低
精度: 中程度 (70-80%)

手法:
  - 弱点提示: 冒頭3段落内に否定的キーワード検出
  - 転機: before/after 状態変化の語彙分析
  - 二重動機: 外的/内的キーワードの存在確認
  - 行動説明: "である" "という" 密度測定
  - 感情曲線: 感情語彙の分布分析

利点:
  - 即座に実行可能
  - LLM コスト不要
  - 再現性高い

欠点:
  - 誤検知の可能性
  - 文脈理解不足
```

**Phase 2: LLMベース診断 (高精度版)**
```yaml
実装難易度: 中
精度: 高 (85-95%)

手法:
  - LLM に構造分析プロンプト送信
  - 各要素の有無を自然言語理解で判定
  - 具体的な引用箇所を提示

利点:
  - 高精度
  - 文脈理解
  - 具体的な指摘

欠点:
  - LLM コスト
  - 実行時間(数秒〜十数秒)
  - 再現性やや低
```

**Phase 3: ハイブリッド診断 (推奨)**
```yaml
実装難易度: 中〜高
精度: 高 (90-95%)

手法:
  - Phase 1 で候補箇所を絞り込み
  - Phase 2 で該当箇所のみ LLM 判定
  - コスト削減と高精度の両立

利点:
  - 高速 + 高精度
  - コスト最適化
  - 具体的指摘 + 再現性

欠点:
  - 実装複雑度高
```

---

### 2. 統合品質ゲート (Integrated Quality Gate)

#### run_quality_checks への新アスペクト追加

```yaml
New Aspect: "narrative_structure"

Usage:
  noveler check <episode> --aspects narrative_structure

Output (Summary Mode):
  Narrative Structure Score: 85/100

  Elements:
    ✅ 弱点提示: Pass (92/100) - 冒頭2段落で明示
    ✅ 転機構造: Pass (88/100) - before→trigger→after 明確
    ⚠️  二重動機: Warn (75/100) - 内的欲求がやや弱い
    ✅ 行動説明: Pass (90/100) - 地の文説明最小限
    ✅ 感情曲線: Pass (85/100) - 起伏明確

  Recommendations:
    - 二重動機: Step 7 (対話設計) で内的欲求を明示的に描写
```

#### 既存アスペクトとの統合

```yaml
run_quality_checks(
  episode=1,
  aspects=["rhythm", "readability", "grammar", "narrative_structure"],
  format="summary"
)

Output:
  Overall Score: 82/100

  Aspect Scores:
    - rhythm: 80/100
    - readability: 85/100
    - grammar: 90/100
    - narrative_structure: 85/100  # NEW

  Weighted Average: 82/100

  Priority Issues:
    1. [narrative_structure] 二重動機がやや弱い → Step 7 再実行
    2. [rhythm] 長文連続 (3箇所) → fix_quality_issues で分割
    3. [readability] 難解語彙 (5箇所) → 手動修正
```

---

### 3. noveler_write.md への統合

#### Preview Mode での自動実行

```yaml
# 現状 (手動)
/noveler write 1 --polish preview
→ dry_run=true で diff 生成
→ 手動で Gate W1 チェック
→ 問題あれば Step 再実行

# 将来 (自動)
/noveler write 1 --polish preview --check-structure
→ dry_run=true で diff 生成
→ **自動で narrative_structure 診断**
→ 問題箇所と対処 Step を即座に提示
→ 承認後に apply または Step 再実行
```

#### Workflow 統合例

```bash
# Step 1: Preview with structure check
/noveler write 1 --polish preview --check-structure

# Output:
# ✅ Polish preview generated (artifact:a1b2c3d4)
# 🔍 Structure Analysis:
#    Overall Score: 75/100
#    ⚠️  Issue: 二重動機がやや弱い (75/100)
#    📝 Recommendation: Step 7 (対話設計) で内的欲求を明示

# Step 2: Fix issue
/noveler step 1 7

# Step 3: Re-preview
/noveler write 1 --polish preview --check-structure

# Output:
# ✅ Structure Score: 88/100 (All elements pass)

# Step 4: Apply
/noveler write 1 --polish apply
```

---

## 技術仕様

### 診断ロジック (Phase 1: ルールベース)

#### 1. 弱点提示 (Flaw Presentation)

```yaml
Target: 冒頭3段落 (約500-800字)

Detection Rules:
  否定的キーワード:
    - 感情: "絶望", "諦め", "恐怖", "不安", "孤独"
    - 状態: "いじめ", "失敗", "弱い", "できない", "逃げる"
    - 自己評価: "価値がない", "無力", "ダメ", "役立たず"

  判定基準:
    - Pass (80+): 冒頭3段落に否定的描写3箇所以上
    - Warn (60-79): 冒頭3段落に否定的描写1-2箇所
    - Fail (<60): 否定的描写なしまたは4段落以降に出現

Implementation:
  def check_flaw_presentation(text: str) -> StructureCheckResult:
      paragraphs = text.split('\n\n')[:3]
      opening_text = '\n'.join(paragraphs)

      negative_keywords = [
          "絶望", "諦め", "恐怖", "不安", "孤独",
          "いじめ", "失敗", "弱い", "できない", "逃げる",
          "価値がない", "無力", "ダメ", "役立たず"
      ]

      count = sum(1 for kw in negative_keywords if kw in opening_text)

      if count >= 3:
          score = min(100, 80 + count * 5)
          status = "pass"
      elif count >= 1:
          score = 60 + count * 10
          status = "warn"
      else:
          score = 40
          status = "fail"

      return StructureCheckResult(
          element_id="flaw_presentation",
          element_name="弱点提示",
          status=status,
          score=score,
          findings=[f"冒頭3段落に否定的描写{count}箇所検出"],
          recommendations=[
              "Step 3 (キャラクター設定) で弱点を明確化",
              "冒頭2-3段落に主人公の苦悩・欠点を配置"
          ] if status != "pass" else [],
          related_step=3
      )
```

#### 2. 転機構造 (Turning Point Structure)

```yaml
Target: 全文 (特に20-40%地点)

Detection Rules:
  変化語彙:
    - Before: "だった", "していた", "いつも", "以前"
    - Trigger: "しかし", "その時", "突然", "初めて"
    - After: "変わった", "なった", "できる", "今は"

  判定基準:
    - Pass (80+): Before/Trigger/After 全パターン検出
    - Warn (60-79): 2パターンのみ検出
    - Fail (<60): 1パターン以下

Implementation:
  def check_turning_point(text: str) -> StructureCheckResult:
      # 全文を10分割し、20-40%地点を重点的に検査
      length = len(text)
      turning_point_section = text[int(length*0.2):int(length*0.4)]

      before_patterns = ["だった", "していた", "いつも", "以前"]
      trigger_patterns = ["しかし", "その時", "突然", "初めて"]
      after_patterns = ["変わった", "なった", "できる", "今は"]

      before_found = any(p in turning_point_section for p in before_patterns)
      trigger_found = any(p in turning_point_section for p in trigger_patterns)
      after_found = any(p in turning_point_section for p in after_patterns)

      found_count = sum([before_found, trigger_found, after_found])

      if found_count == 3:
          score = 90
          status = "pass"
      elif found_count == 2:
          score = 70
          status = "warn"
      else:
          score = 50
          status = "fail"

      return StructureCheckResult(
          element_id="turning_point",
          element_name="転機構造",
          status=status,
          score=score,
          findings=[
              f"Before: {'検出' if before_found else '未検出'}",
              f"Trigger: {'検出' if trigger_found else '未検出'}",
              f"After: {'検出' if after_found else '未検出'}"
          ],
          recommendations=[
              "Step 6 (転機設計) で before→trigger→after を明示",
              "A28 Stage 2 の turning_point 詳細構造を参照"
          ] if status != "pass" else [],
          related_step=6
      )
```

#### 3. 二重動機 (Dual Motivation)

```yaml
Target: 全文 (特に前半40%)

Detection Rules:
  外的目的キーワード:
    - "倒す", "救う", "手に入れる", "逃れる", "達成"
    - "勝つ", "守る", "見つける", "解決"

  内的欲求キーワード:
    - "認められたい", "助けたい", "償いたい"
    - "必要とされたい", "証明したい", "理解されたい"

  判定基準:
    - Pass (80+): 外的+内的の両方検出、かつ近接配置(1000字以内)
    - Warn (60-79): 片方のみ検出、または遠隔配置
    - Fail (<60): 両方未検出

Implementation:
  def check_dual_motivation(text: str) -> StructureCheckResult:
      external_keywords = [
          "倒す", "救う", "手に入れる", "逃れる", "達成",
          "勝つ", "守る", "見つける", "解決"
      ]
      internal_keywords = [
          "認められたい", "助けたい", "償いたい",
          "必要とされたい", "証明したい", "理解されたい"
      ]

      # 前半40%を検査
      target = text[:int(len(text)*0.4)]

      external_positions = [
          i for kw in external_keywords
          for i in find_all(target, kw)
      ]
      internal_positions = [
          i for kw in internal_keywords
          for i in find_all(target, kw)
      ]

      has_external = len(external_positions) > 0
      has_internal = len(internal_positions) > 0

      # 近接性チェック (1000字以内に両方存在)
      proximity = False
      if has_external and has_internal:
          for ext_pos in external_positions:
              for int_pos in internal_positions:
                  if abs(ext_pos - int_pos) <= 1000:
                      proximity = True
                      break

      if has_external and has_internal and proximity:
          score = 90
          status = "pass"
      elif has_external and has_internal:
          score = 70
          status = "warn"
          findings_note = "両方検出したが配置が遠い"
      elif has_external or has_internal:
          score = 60
          status = "warn"
          findings_note = "片方のみ検出"
      else:
          score = 40
          status = "fail"
          findings_note = "両方未検出"

      return StructureCheckResult(
          element_id="dual_motivation",
          element_name="二重動機",
          status=status,
          score=score,
          findings=[
              f"外的目的: {'検出' if has_external else '未検出'}",
              f"内的欲求: {'検出' if has_internal else '未検出'}",
              findings_note
          ],
          recommendations=[
              "Step 7 (対話設計) で外的目的を明示",
              "Step 3 (キャラクター) で内的欲求を深掘り",
              "A24 目的設定チェックリストを参照"
          ] if status != "pass" else [],
          related_step=7
      )
```

#### 4. 行動説明 (Action-based Explanation)

```yaml
Target: 全文

Detection Rules:
  説明的パターン (禁止):
    - "AはBである", "AとはBのことだ"
    - "〜という", "〜というものだ"
    - "これは〜だ", "それは〜である"

  判定基準:
    - Pass (80+): 説明的文が全体の5%未満
    - Warn (60-79): 説明的文が5-10%
    - Fail (<60): 説明的文が10%超

Implementation:
  def check_action_explanation(text: str) -> StructureCheckResult:
      sentences = split_sentences(text)
      total_sentences = len(sentences)

      explanation_patterns = [
          r'は.{1,20}である',
          r'とは.{1,20}のことだ',
          r'という.{1,20}だ',
          r'これは.{1,20}だ',
          r'それは.{1,20}である'
      ]

      explanation_count = 0
      for sent in sentences:
          if any(re.search(p, sent) for p in explanation_patterns):
              explanation_count += 1

      explanation_ratio = explanation_count / total_sentences

      if explanation_ratio < 0.05:
          score = 95
          status = "pass"
      elif explanation_ratio < 0.10:
          score = 70
          status = "warn"
      else:
          score = 50
          status = "fail"

      return StructureCheckResult(
          element_id="action_explanation",
          element_name="行動説明",
          status=status,
          score=score,
          findings=[
              f"説明的文: {explanation_count}/{total_sentences} ({explanation_ratio*100:.1f}%)"
          ],
          recommendations=[
              "Step 10 (五感設計) で説明的文を行動描写に置換",
              "「AはBである」を主人公の体験・対話に変換",
              "fix_quality_issues で EXPLANATION_HEAVY 検出(将来)"
          ] if status != "pass" else [],
          related_step=10
      )
```

#### 5. 感情曲線 (Emotional Curve)

```yaml
Target: 全文を3分割 (導入/転機/結末)

Detection Rules:
  感情語彙 (ポジティブ):
    - "嬉しい", "期待", "希望", "安心", "楽しい", "驚き"

  感情語彙 (ネガティブ):
    - "悲しい", "絶望", "恐怖", "不安", "怒り", "諦め"

  判定基準:
    - Pass (80+): 導入(低)→転機(高)→結末(中) の起伏
    - Warn (60-79): 起伏あるが変化幅小
    - Fail (<60): 平坦または逆転

Implementation:
  def check_emotional_curve(text: str) -> StructureCheckResult:
      # 3分割
      length = len(text)
      part1 = text[:int(length*0.33)]  # 導入
      part2 = text[int(length*0.33):int(length*0.66)]  # 転機
      part3 = text[int(length*0.66):]  # 結末

      positive_kw = ["嬉しい", "期待", "希望", "安心", "楽しい", "驚き"]
      negative_kw = ["悲しい", "絶望", "恐怖", "不安", "怒り", "諦め"]

      def emotion_level(part: str) -> float:
          pos = sum(part.count(kw) for kw in positive_kw)
          neg = sum(part.count(kw) for kw in negative_kw)
          # 正規化: -1.0 (ネガティブ) 〜 +1.0 (ポジティブ)
          return (pos - neg) / (pos + neg + 1)

      level1 = emotion_level(part1)  # 導入
      level2 = emotion_level(part2)  # 転機
      level3 = emotion_level(part3)  # 結末

      # 理想: level1 < 0, level2 > 0.5, -0.3 < level3 < 0.5
      ideal_pattern = (level1 < 0) and (level2 > 0.5) and (-0.3 < level3 < 0.5)
      variation = max(level2 - level1, level2 - level3)

      if ideal_pattern and variation > 0.8:
          score = 95
          status = "pass"
      elif variation > 0.5:
          score = 75
          status = "warn"
      else:
          score = 55
          status = "fail"

      return StructureCheckResult(
          element_id="emotional_curve",
          element_name="感情曲線",
          status=status,
          score=score,
          findings=[
              f"導入: {level1:.2f} (理想: <0)",
              f"転機: {level2:.2f} (理想: >0.5)",
              f"結末: {level3:.2f} (理想: -0.3〜0.5)",
              f"変化幅: {variation:.2f}"
          ],
          recommendations=[
              "Step 8 (感情曲線) で emotion_level 変化幅を±2以上に",
              "カタルシスを第二幕終盤(60-70%地点)に配置",
              "A28 Stage 2 の emotion_curve を参照"
          ] if status != "pass" else [],
          related_step=8
      )
```

---

### 診断ロジック (Phase 2: LLMベース)

#### LLM プロンプト設計

```yaml
System Prompt:
  role: "Narrative Structure Analyzer"
  task: |
    あなたは小説の物語構造を分析する専門家です。
    与えられた原稿を以下の5要素で評価してください:
    1. 弱点提示: 主人公の欠点/弱点が冒頭で提示されているか
    2. 転機構造: before→trigger→after の構造が明確か
    3. 二重動機: 外的目的+内的欲求が揃っているか
    4. 行動説明: 世界観を行動/五感で説明しているか
    5. 感情曲線: 導入(低)→転機(高)→結末(中)の起伏があるか

  output_format: "JSON"
  output_schema: |
    {
      "structure_score": <0-100>,
      "elements": [
        {
          "element_id": "flaw_presentation",
          "element_name": "弱点提示",
          "status": "pass" | "warn" | "fail",
          "score": <0-100>,
          "findings": ["具体的な検出内容"],
          "quote": "該当箇所の引用(50字以内)",
          "recommendations": ["対処法"]
        },
        ...
      ]
    }

User Prompt Template:
  |
  以下の原稿を分析してください:

  ---
  {manuscript_text}
  ---

  各要素について、以下を回答してください:
  1. 該当箇所の有無
  2. スコア(0-100)
  3. 具体的な引用(50字以内)
  4. 改善推奨事項
```

#### 実装例

```python
async def analyze_with_llm(
    episode_number: int,
    project_root: Path
) -> NarrativeStructureResult:
    # 原稿取得
    manuscript_path = project_root / "manuscripts" / f"ep{episode_number:03d}.txt"
    manuscript_text = manuscript_path.read_text(encoding="utf-8")

    # LLM 呼び出し
    response = await call_llm(
        system_prompt=NARRATIVE_ANALYZER_SYSTEM_PROMPT,
        user_prompt=NARRATIVE_ANALYZER_USER_PROMPT.format(
            manuscript_text=manuscript_text
        ),
        response_format="json"
    )

    # JSON パース
    result = NarrativeStructureResult.from_json(response)

    # アーティファクト保存
    analysis_id = save_analysis_artifact(result)
    result.artifacts.analysis_id = analysis_id

    return result
```

---

### Phase 3: ハイブリッド診断

```yaml
Strategy:
  Step 1: ルールベースでスコアリング
  Step 2: Warn/Fail 要素のみ LLM で再判定
  Step 3: LLM 結果でルールベース結果を上書き

利点:
  - Pass 要素は LLM 不要 (コスト削減)
  - Warn/Fail 要素のみ精密判定 (精度向上)
  - 全体処理時間の短縮

Implementation:
  async def analyze_hybrid(
      episode_number: int,
      project_root: Path
  ) -> NarrativeStructureResult:
      # Step 1: ルールベース診断
      rule_based_result = analyze_rule_based(episode_number, project_root)

      # Step 2: Warn/Fail 要素を抽出
      needs_llm = [
          elem for elem in rule_based_result.element_checks
          if elem.status in ["warn", "fail"]
      ]

      if not needs_llm:
          # 全要素 Pass → LLM 不要
          return rule_based_result

      # Step 3: LLM で再判定
      llm_result = await analyze_with_llm_partial(
          episode_number, project_root, needs_llm
      )

      # Step 4: 結果マージ
      merged_result = merge_results(rule_based_result, llm_result)

      return merged_result
```

---

## 統合仕様

### noveler MCP への統合

```yaml
New Tool: "check_narrative_structure"

Parameters:
  - episode_number: int (required)
  - file_path: str (optional)
  - project_root: str (optional)
  - analysis_depth: str (optional, "basic" | "detailed" | "hybrid")
  - save_report: bool (optional, default: true)

Returns:
  - structure_score: float
  - element_checks: List[ElementCheckResult]
  - summary: AnalysisSummary
  - artifacts: AnalysisArtifacts

Example MCP Call:
  {
    "tool": "check_narrative_structure",
    "arguments": {
      "episode_number": 1,
      "analysis_depth": "hybrid",
      "save_report": true
    }
  }
```

### run_quality_checks への統合

```yaml
Modified Function Signature:
  def run_quality_checks(
      episode_number: int,
      aspects: List[str],  # NEW: "narrative_structure" を追加可能
      format: str = "summary",
      severity_threshold: str = "low",
      ...
  ) -> QualityCheckResult:
      ...

Usage:
  noveler check 1 --aspects rhythm,readability,narrative_structure

Implementation:
  if "narrative_structure" in aspects:
      narrative_result = await check_narrative_structure(
          episode_number=episode_number,
          analysis_depth="hybrid"
      )
      # 既存の QualityCheckResult に統合
      result.narrative_structure_score = narrative_result.structure_score
      result.narrative_structure_issues = narrative_result.failed_elements
```

---

## 開発計画

### Phase 1: ルールベース診断 (3-5日)

```yaml
Tasks:
  - [ ] StructureCheckResult データクラス定義
  - [ ] 5要素の診断関数実装
  - [ ] 統合関数 analyze_rule_based 実装
  - [ ] ユニットテスト作成
  - [ ] MCP ツール "check_narrative_structure" 実装

Deliverables:
  - src/noveler/domain/services/narrative_structure_checker.py
  - tests/unit/domain/services/test_narrative_structure_checker.py
  - MCP tool integration
```

### Phase 2: LLMベース診断 (5-7日)

```yaml
Tasks:
  - [ ] LLM プロンプト設計
  - [ ] LLM 呼び出しインフラ整備
  - [ ] レスポンスパーサー実装
  - [ ] アーティファクト保存機能
  - [ ] エラーハンドリング
  - [ ] ユニットテスト + 統合テスト

Deliverables:
  - src/noveler/infrastructure/llm/narrative_analyzer.py
  - プロンプトテンプレート
  - LLM レスポンスサンプル
```

### Phase 3: ハイブリッド診断 + 統合 (5-7日)

```yaml
Tasks:
  - [ ] ハイブリッドロジック実装
  - [ ] run_quality_checks への統合
  - [ ] noveler_write.md への統合
  - [ ] CLI コマンド追加
  - [ ] ドキュメント作成
  - [ ] E2E テスト

Deliverables:
  - ハイブリッド診断機能
  - run_quality_checks 拡張
  - noveler_write.md 更新
  - docs/guides/narrative_structure_check.md
```

---

## テスト戦略

### ユニットテスト

```yaml
Target: 各診断関数

Test Cases (例: check_flaw_presentation):
  - test_pass_case: 冒頭3段落に否定的描写3箇所以上
  - test_warn_case: 冒頭3段落に否定的描写1-2箇所
  - test_fail_case: 否定的描写なし
  - test_boundary_case: ちょうど3段落目に出現
  - test_late_appearance: 4段落目以降に出現
```

### 統合テスト

```yaml
Target: analyze_hybrid 全体フロー

Test Cases:
  - test_all_pass: 全要素 Pass → LLM 呼び出しなし
  - test_partial_warn: 一部 Warn → LLM で該当要素のみ再判定
  - test_all_fail: 全要素 Fail → LLM で全再判定
  - test_llm_error: LLM エラー時のフォールバック
```

### E2Eテスト

```yaml
Target: noveler_write.md 統合

Test Cases:
  - test_preview_with_structure_check:
      - /noveler write 1 --polish preview --check-structure
      - 構造診断実行確認
      - レポート生成確認

  - test_fix_and_recheck:
      - 構造問題検出
      - Step 再実行
      - 再診断で Pass 確認
```

---

## リリース計画

### v1.0.0: ルールベース診断

```yaml
Features:
  - 5要素のルールベース診断
  - MCP ツール "check_narrative_structure"
  - CLI: noveler check <ep> --aspects narrative_structure

Target: 2025-Q2
```

### v1.1.0: LLMベース診断

```yaml
Features:
  - LLM による高精度診断
  - 引用箇所の提示
  - 詳細レポート生成

Target: 2025-Q3
```

### v1.2.0: ハイブリッド診断 + 統合

```yaml
Features:
  - ハイブリッド診断 (コスト最適化)
  - noveler_write.md への完全統合
  - 自動修正提案 (Step 再実行ガイド)

Target: 2025-Q4
```

---

## 参考資料

- noveler_write.md (Gate W1 - 物語構造の5要素チェック)
- A28 Case Study (Accel World 分析)
- A24 目的設定チェックリスト
- SPEC-CLI-050 (Slash Command Management)

---

**Status**: Draft Specification (未実装)
**Priority**: Low (Phase 3 - 現状は手動 Gate W1 で対応可能)
**Next Step**: Phase 1 実装前に Codex レビュー + 設計承認
