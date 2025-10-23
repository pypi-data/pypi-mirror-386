# 自動チェックシステム仕様書

## 1. 概要

### 1.1 目的
YAMLチェックリスト（A11_企画設計、A21_プロット作成、A31_原稿執筆）を自動的に読み込み、各チェック項目を検証して、原稿やプロットごとに詳細なチェック結果を記録するシステムを構築する。

### 1.2 対象範囲
- A11_企画設計・コンセプト策定ガイド.md（品質チェック統合済み）
- A30_執筆品質基準.md（プロット・推敲品質チェック統合済み）
- A31_原稿執筆チェックリスト.yaml

**注**: YAMLチェックリスト（A11/A25/A41）は2025-08-23にMarkdown品質基準に統合済み。詳細は`docs/archive/yaml_legacy/README.md`参照。

### 1.3 期待される効果
- チェック作業の完全自動化
- 客観的で一貫性のある品質評価
- 即時フィードバックによる品質向上
- 改善点の明確化と具体的な修正提案
- AI支援による手動項目の効率化
- チェック履歴の管理と分析

## 2. システム設計

### 2.1 ディレクトリ構造とCLIコマンド対応

```
$PROJECT_ROOT/
├── 10_企画/                                    # novel check-project
│   └── 企画書.yaml                             # A11チェック対象
├── 20_プロット/                                # novel check-plot
│   ├── 全体構成.yaml                           # novel check-plot master
│   └── 章別プロット/                           # novel check-plot chapter [N]
│       ├── 第1章.yaml
│       ├── 第2章.yaml
│       └── 第3章.yaml
├── 30_設定集/                                  # novel check-project（参照）
│   ├── キャラクター.yaml                       # A11チェック参照ファイル
│   ├── 世界観.yaml                             # A11/A21チェック参照ファイル
│   └── 用語集.yaml                             # A21チェック参照ファイル
├── 40_原稿/                                    # novel check [N]
│   ├── 第001話_システムエラーと魔法陣.md        # novel check 1
│   ├── 第002話_レベル1エラーハンドラー.md      # novel check 2
│   └── 第003話_魔法デバッガーの覚醒.md          # novel check 3
└── 50_管理資料/                                # チェック結果出力先
    └── チェック結果/                           # --save-results時の保存先
        ├── A11_企画設計_チェック結果.yaml      # novel check-project結果
        ├── A21_プロット作成_チェック結果.yaml  # novel check-plot all結果
        ├── 第001話_システムエラーと魔法陣_チェック結果.yaml  # novel check 1結果
        ├── 第002話_レベル1エラーハンドラー_チェック結果.yaml  # novel check 2結果
        └── 全体品質チェック_YYYY-MM-DD.yaml     # novel check-all結果
```

**CLI対応詳細**
- `novel check [番号|ファイル名]`: 40_原稿/内の特定原稿をA31でチェック
- `novel check-plot master`: 20_プロット/全体構成.yamlをA21でチェック
- `novel check-plot chapter [番号]`: 20_プロット/章別プロット/第X章.yamlをA21でチェック
- `novel check-plot all`: プロット関連ファイル全体をA21でチェック
- `novel check-project`: 企画・設定関連ファイルをA11でチェック
- `novel check-all`: 全ファイルを対応するチェックリストでチェック

### 2.2 チェック結果ファイル形式

#### 2.2.1 原稿チェック結果（A31）

```yaml
# 第001話_システムエラーと魔法陣_チェック結果.yaml
metadata:
  source_file: "40_原稿/第001話_システムエラーと魔法陣.md"
  checklist_used: "$GUIDE_ROOT/A31_原稿執筆チェックリスト.yaml"
  check_date: "2025-07-25T14:30:00"
  overall_result:
    total_items: 42
    auto_check_items: 25
    ai_assist_items: 8
    manual_items: 9
    passed_items: 35
    failed_items: 4
    ai_suggestions: 6
    pass_rate: 83.33

check_results:
  Phase2_執筆段階:
    - id: "A31-021"
      item: "冒頭3行で読者を引き込む工夫"
      type: "content_quality"
      status: "passed"
      auto_check: true
      check_logic: "opening_hook_analysis"
      details:
        first_three_lines: |
          レオは目を疑った。
          魔法陣から飛び出してきたのは、召喚獣でも精霊でもない。
          ［システムエラー：不明なオブジェクトが検出されました］
        hook_score: 8.5
        hook_elements: ["感情語句: 疑", "簡潔な導入", "システム要素"]
        criteria: "hook_score >= 7.0"

    - id: "A31-023"
      item: "五感描写を適切に配置"
      type: "sensory_check"
      status: "failed"
      auto_check: true
      check_logic: "sensory_description_analysis"
      details:
        sensory_elements:
          visual: 12
          auditory: 3
          tactile: 1
          olfactory: 0
          gustatory: 0
        used_senses_count: 3
        missing_senses: ["olfactory", "gustatory"]
        minimum_required: 3
        recommendation: "嗅覚や味覚の描写を追加することで、より立体的な表現になります"

  Phase5_公開前最終確認:
    - id: "A31-061"
      item: "タイトルが内容を適切に表現"
      type: "content_review"
      status: "ai_assisted"
      auto_check: false
      ai_support: true
      details:
        ai_analysis:
          current_title: "第001話_システムエラーと魔法陣"
          content_summary: "主人公が魔法陣召喚でシステムエラーに遭遇する導入話"
          title_content_match_score: 8.5
          analysis_points:
            - "システムエラー要素が適切に表現されている"
            - "魔法陣との関連性が明確"
            - "導入話としての位置づけが不明確"
          improvement_suggestions:
            - title: "第001話_召喚魔法とシステムの謎"
              reason: "謎要素を強調してより読者の興味を引く"
            - title: "第001話_エラーから始まる異世界デバッグ"
              reason: "シリーズ全体のテーマを暗示"
          confidence_level: 0.85
        manual_review_needed: true
        final_decision: "要ユーザー判断"
```

#### 2.2.2 プロットチェック結果（A21）

```yaml
# A21_プロット作成_チェック結果.yaml
metadata:
  checklist_used: "$GUIDE_ROOT/A21_プロット作成チェックリスト.yaml"
  check_date: "2025-07-25T12:00:00"
  overall_result:
    total_items: 93
    auto_check_items: 45
    ai_assist_items: 25
    manual_items: 23
    passed_items: 82
    failed_items: 7
    ai_suggestions: 18
    pass_rate: 88.17

check_results:
  事前準備確認:
    - id: "A21-001"
      item: "A11_企画設計チェックリストの必須項目が全て完了"
      type: "prerequisite_check"
      status: "passed"
      auto_check: true
      check_logic: "checklist_completion_check"
      details:
        required_items_completed: 30
        total_required_items: 30
        completion_rate: 100.0
        file_path: "$GUIDE_ROOT/A11_企画設計・コンセプト策定ガイド.md#企画設計品質チェック項目統合"

  ファイル1_全体構成yaml作成:
    - id: "A21-012"
      item: "**三幕構成** 序章・展開・終章の配分を決定"
      type: "structure_design"
      status: "failed"
      auto_check: true
      check_logic: "three_act_structure_analysis"
      details:
        current_structure:
          act1_episodes: 8
          act2_episodes: 15
          act3_episodes: 7
          total_episodes: 30
        current_ratio: [26.7, 50.0, 23.3]
        ideal_ratio_range: [[20, 30], [45, 55], [20, 30]]
        analysis: "第1幕が理想範囲をやや上回っています"
        recommendation: "第1幕を6-7話に短縮することを検討してください"

  ファイル2_章別プロット作成:
    - id: "A21-051"
      item: "**第1章.yaml** 作成・各章の詳細記載完了"
      type: "chapter_creation"
      status: "passed"
      auto_check: true
      check_logic: "chapter_file_completeness"
      details:
        file_path: "20_プロット/章別プロット/第1章.yaml"
        required_fields_found: 15
        required_fields_total: 15
        episodes_detailed: 5
        structure_completeness: 100.0
        validation_result: "全必須フィールドが適切に記載されています"

    - id: "A21-061"
      item: "**伏線配置** setup/payoff話数の明記完了"
      type: "foreshadowing_management"
      status: "failed"
      auto_check: true
      check_logic: "foreshadowing_setup_analysis"
      details:
        total_foreshadowing: 8
        properly_mapped: 5
        missing_setup: 2
        missing_payoff: 1
        incomplete_items:
          - foreshadowing_id: "FORE-003"
            name: "古代魔法の謎"
            issue: "payoff_episodeが未設定"
          - foreshadowing_id: "FORE-007"
            name: "レオの真の力"
            issue: "setup_episodeが未設定"
        recommendation: "未設定の伏線について話数配置を決定してください"

  品質確認:
    - id: "A21-131"
      item: "**全体構成と章別の整合性** 話数・内容の一致確認"
      type: "consistency_check"
      status: "passed"
      auto_check: true
      check_logic: "plot_consistency_analysis"
      details:
        total_episodes_master: 30
        total_episodes_chapters: 30
        title_matches: 30
        content_matches: 28
        minor_discrepancies: 2
        discrepancy_details:
          - episode: 12
            issue: "概要の表現が微妙に異なる"
            severity: "low"
        overall_consistency_score: 93.3

    - id: "A21-162"
      item: "各話に読み続けたくなる要素があるか"
      type: "reader_experience"
      status: "ai_assisted"
      auto_check: false
      ai_support: true
      details:
        ai_analysis:
          analyzed_episodes: 15
          hook_elements_found: 12
          weak_endings_identified: 3
          improvement_suggestions:
            - episode: "第3話"
              current_ending: "レオは新しいスキルを習得した。"
              suggested_improvement: "スキル習得の瞬間に予期せぬ副作用が発生し、次話への謎を残す"
              reason: "より強いクリフハンガー効果"
            - episode: "第7話"
              current_ending: "一日の訓練が終わった。"
              suggested_improvement: "訓練中に発見した異常なログメッセージについて言及"
              reason: "継続読書への動機付け"
          confidence_level: 0.82
        manual_review_needed: true
        final_decision: "要ユーザー判断"
```

#### 2.2.3 企画チェック結果（A11）

```yaml
# A11_企画設計_チェック結果.yaml
metadata:
  checklist_used: "$GUIDE_ROOT/A11_企画設計・コンセプト策定ガイド.md#企画設計品質チェック項目統合"
  check_date: "2025-07-25T10:00:00"
  overall_result:
    total_items: 30
    auto_check_items: 15
    ai_assist_items: 10
    manual_items: 5
    passed_items: 28
    failed_items: 2
    ai_suggestions: 8
    pass_rate: 93.33

check_results:
  市場調査段階:
    - id: "A11-001"
      item: "ターゲットジャンルの人気作品を10作品以上分析"
      type: "market_research"
      status: "passed"
      auto_check: true
      check_logic: "market_research_count"
      details:
        analyzed_works_count: 12
        criteria: "count >= 10"
        file_path: "10_企画/市場調査結果.yaml"

  コンセプト設計段階:
    - id: "A11-013"
      item: "読者の「読みたい」と思わせるフックを設計"
      type: "hook_design"
      status: "ai_assisted"
      auto_check: false
      ai_support: true
      details:
        ai_analysis:
          current_hooks: ["Fランク魔法使い", "DEBUGログ", "異世界プログラマー"]
          hook_effectiveness_scores: [7.2, 8.9, 6.8]
          target_audience_match: 0.82
          improvement_suggestions:
            - "デバッグスキルの具体的な魅力をより強調"
            - "読者の共感を呼ぶプログラマーあるある要素の追加"
          confidence_level: 0.78
```

## 3. 実装仕様

### 3.1 チェック実行の基本フロー

#### 3.1.1 コマンド解析とターゲット特定

1. **コマンド引数の解析**
   - `novel check 1` → A31原稿チェック、第1話対象
   - `novel check-plot master` → A21プロットチェック、全体構成.yaml対象
   - `novel check-project` → A11企画チェック、企画書.yaml等対象

2. **対象ファイルの特定**
   ```
   A31: 40_原稿/第XXX話_タイトル.md
   A21: 20_プロット/全体構成.yaml, 20_プロット/章別プロット/第X章.yaml
   A11: 10_企画/企画書.yaml, 30_設定集/世界観.yaml等
   ```

3. **適用チェックリストの決定**
   - コマンドとオプションから使用するYAMLチェックリストを決定
   - `--checklist` オプションで明示的に指定可能

#### 3.1.2 チェック項目処理

1. **YAMLチェックリストの読み込み**
   - 対応するA11/A21/A31チェックリスト.yamlを読み込み
   - 各フェーズの項目を順次処理

2. **各チェック項目の処理方法判定**
   - チェック項目のIDに対応する検証関数が実装されているかを確認
   - YAMLチェックリスト内の`type`フィールドから処理方法を決定
     - **自動化対応タイプ**: content_quality、content_balance、structure_design等
       → 自動チェック実行
     - **AI支援対応タイプ**: content_review、feasibility_check、reader_experience等
       → AIアシスト機能を実行
     - **完全手動タイプ**: manual_entry、document_review等
       → スキップまたは確認促進メッセージ表示
   - 必要な入力ファイル（input_files）が存在するかを確認

3. **検証実行**
   - 対象ファイル（原稿、プロット等）を読み込み
   - 項目ごとに定義された検証ロジックを実行
   - AI支援が必要な項目についてはAIに問い合わせを実行

#### 3.1.3 結果処理と出力

1. **結果の集計**
   - 各項目のチェック結果（passed/failed/ai_assisted/skipped）を集計
   - 全体の集計情報（合格率、要対応項目数等）を算出

2. **結果の保存**
   - `--save-results` オプション有効時: 結果をYAML形式でチェック結果ファイルに保存
   - 保存先: `50_管理資料/チェック結果/[対象ファイル]_チェック結果.yaml`

3. **出力**
   - コンソールに結果を表示（3.5.1 コンソール出力形式に従って）
   - `--output-format` オプションに応じてyaml/json/markdown形式で出力

### 3.2 検証ロジックの基本設計方針

#### 3.2.1 原稿チェック検証ロジック（A31）

**A31-021: 冒頭3行のフック力検証**
- 原稿の最初の3行を抽出
- 感情を揺さぶる語句の有無をチェック（驚、疑、謎、異常、衝撃、困惑）
- 疑問符・感嘆符の使用状況を確認
- 文字数が150文字以内の簡潔性を評価
- 対話から始まるかどうかを判定
- 各要素にポイントを配点し、合計スコアで判定
- 基準点7.0以上で合格

**A31-022: 会話と地の文の比率チェック**
- 「」で囲まれた会話文を正規表現で抽出
- 会話文の総文字数と全体文字数から比率を計算
- 適正範囲（30%～40%）内かを判定
- 範囲外の場合は改善提案を生成

**A31-023: 五感描写のチェック**
- 視覚、聴覚、触覚、嗅覚、味覚のキーワードリストを定義
- 各感覚のキーワード出現回数をカウント
- 使用されている感覚の種類数を集計
- 3つ以上の感覚が使われていれば合格
- 不足している感覚について改善提案を生成

#### 3.2.2 プロットチェック検証ロジック（A21）

**A21-012: 三幕構成の配分チェック**
- 全体構成.yamlから三幕構成情報を読み込み
- 序章、展開、終章の話数範囲を解析
- 各幕の話数から比率を計算
- 理想的な比率（2:5:3または3:5:2）と比較
- 許容範囲内であれば合格

**A21-021: 主要ターニングポイントを5-7箇所設定**
- 全体構成.yamlからターニングポイント配列を確認
- 要素数が5-7個の範囲内かをチェック
- 各ポイントに必須項目（episode、description、impact_level）があるかを確認

**A21-001: A11_企画設計チェックリストの必須項目が全て完了**
- A11_企画設計・コンセプト策定ガイド.md（企画設計品質チェック項目統合セクション）を読み込み
- 各項目のstatusがtrueになっているかを確認
- required: trueの項目がすべて完了していれば合格

**A21-051: 第1章.yaml 作成・各章の詳細記載完了**
- 20_プロット/章別プロット/第1章.yamlの存在を確認
- ファイル内の必須フィールド（章構成、各話詳細）が記載されているかをチェック
- opening/middle/ending構成が全話分記載されていれば合格

**A21-061: 伏線配置 setup/payoff話数の明記完了**
- 50_管理資料/伏線管理.yamlから伏線リストを確認
- 各伏線にsetup_episode、payoff_episodeが設定されているかをチェック
- 全伏線で話数が明記されていれば合格

**A21-131: 全体構成と章別の整合性 話数・内容の一致確認**
- 全体構成.yamlの話数情報と章別プロット.yamlの話数を照合
- 各話のタイトルと概要が一致しているかを確認
- 矛盾がなければ合格

**A21-162: 各話に読み続けたくなる要素があるか**
- 各章別プロット.yamlから各話のending部分を抽出
- クリフハンガー、謎提示、次話への引きの要素を分析
- AI支援により読者継続意欲を評価

#### 3.2.3 企画チェック検証ロジック（A11）

**A11-001: 市場調査の完了確認**
- 10_企画/市場調査結果.yamlの存在を確認
- ファイル内のanalyzed_works配列の要素数をカウント
- 10作品以上あれば合格

**A11-012: 独自性要素の設定確認**
- 企画書.yamlから独自要素リストを確認
- 要素数が3つ以上あるかをチェック
- 各要素に説明が記載されているかを確認

### 3.3 AI支援チェック機能

#### 3.3.1 AI支援の基本仕組み
- 対象ファイル（原稿、プロット、企画書等）の内容を読み込み
- チェック項目の内容とファイル内容をAIに送信
- AIからの分析結果と改善提案を取得
- 結果をチェック結果ファイルに記録

#### 3.3.2 AI支援対象項目の例

**A31-061: タイトルが内容を適切に表現（content_review）**
- 原稿内容とタイトルをAIに送信
- AIがタイトルと内容の一致度を分析
- より適切なタイトル候補を提案
- 改善理由も含めて結果に記録

**A11-063: 読者視点でのワクワク感を再確認（excitement_check）**
- 企画書の内容をAIに送信
- エンタメ要素の分析と評価
- ワクワク感を高める具体的な改善提案
- 読者の興味を引く要素の追加提案

**A21-162: 各話に読み続けたくなる要素があるか（reader_experience）**
- 各話のプロット内容をAIに送信
- クリフハンガーや引きの要素を分析
- より効果的な引きの作り方を提案
- 読者の継続意欲を高める改善案

**A31-032: 文章のリズムと読みやすさを確認（readability_check）**
- 原稿の文章構造をAIが分析
- 文体のバリエーション、リズム感を評価
- より読みやすい文章構成の提案
- 具体的な修正箇所の指摘

**A11-024: 読者が感情移入できる要素を確認（empathy_check）**
- キャラクター設定と読者層分析をAIに送信
- 感情移入ポイントの分析
- より共感しやすいキャラクター要素の提案
- ターゲット読者との親和性評価

#### 3.3.3 AI支援結果の記録形式

AI支援項目には以下の詳細情報を記録：

```yaml
details:
  ai_analysis:
    current_state: "現在の状況分析"
    analysis_points: ["分析ポイント1", "分析ポイント2"]
    strengths: ["強み1", "強み2"]
    weaknesses: ["改善点1", "改善点2"]
    improvement_suggestions:
      - suggestion: "具体的な改善提案"
        reason: "改善理由"
        priority: "high/medium/low"
    confidence_level: 0.85
  manual_review_needed: true
  final_decision: "要ユーザー判断"
```

### 3.4 コマンドインターフェース

#### 3.4.1 チェック実行コマンド

**原稿チェック（A31）**
```bash
# 原稿ファイル名指定での自動チェック（AI支援含む）
$ novel check 第001話_システムエラーと魔法陣.md --auto-validate --ai-assist

# 原稿番号指定での自動チェック（AI支援含む）
$ novel check 1 --auto-validate --ai-assist

# 特定の原稿のA31チェックリストのみ実行
$ novel check 1 --checklist A31 --ai-assist

# AI支援のみ実行（自動チェックはスキップ）
$ novel check 1 --ai-only

# 複数話の一括チェック
$ novel check 1-5 --auto-validate --ai-assist
```

**プロットチェック（A21）**
```bash
# 全体構成.yamlのチェック
$ novel check-plot master --auto-validate --ai-assist

# 章別プロットのチェック
$ novel check-plot chapter 1 --auto-validate --ai-assist
$ novel check-plot chapter 1-3 --auto-validate --ai-assist

# プロット全体の一括チェック（全体構成+全章別プロット）
$ novel check-plot all --auto-validate --ai-assist

# A21チェックリスト全項目の実行
$ novel check --checklist A21 --ai-assist
```

**企画設計チェック（A11）**
```bash
# 企画設計の自動チェック（AI支援含む）
$ novel check-project --auto-validate --ai-assist

# A11チェックリスト全項目の実行
$ novel check --checklist A11 --ai-assist

# 特定フェーズのみチェック
$ novel check-project --phase market-research --ai-assist
$ novel check-project --phase concept-design --ai-assist
```

**横断的チェック**
```bash
# 全チェックリストの一括実行（AI支援含む）
$ novel check-all --auto-validate --ai-assist

# 特定のチェックタイプのみ実行
$ novel check-all --type auto-only      # 自動チェックのみ
$ novel check-all --type ai-only        # AI支援チェックのみ
$ novel check-all --type manual-only    # 手動チェック項目のリスト表示のみ
```

#### 3.4.2 コマンドオプション詳細

**共通オプション**
- `--auto-validate`: 自動チェック機能を有効化
- `--ai-assist`: AI支援チェック機能を有効化
- `--ai-only`: AI支援チェックのみ実行（自動チェックをスキップ）
- `--checklist [A11|A21|A31]`: 特定のチェックリストのみ実行
- `--output-format [yaml|json|markdown]`: 結果出力形式の指定
- `--save-results`: チェック結果を管理資料/チェック結果/に保存
- `--verbose`: 詳細ログ出力
- `--dry-run`: 実際のチェックを行わず、実行予定項目のみ表示

**原稿チェック固有オプション**
- `--episode-range [1-5]`: 複数話の範囲指定
- `--focus-phase [Phase1|Phase2|Phase3|Phase4|Phase5]`: 特定フェーズのみチェック

**プロットチェック固有オプション**
- `--target [master|chapter|all]`: チェック対象の指定
- `--chapter-range [1-3]`: 章番号の範囲指定

**企画チェック固有オプション**
- `--phase [market-research|concept-design|character-design|worldbuilding|document-creation|initialization|final-check]`: 特定段階のみチェック

#### 3.4.3 実行例とユースケース

**日常的な原稿チェック**
```bash
# 第5話を執筆後の標準チェック
$ novel check 5 --auto-validate --ai-assist --save-results

# 複数話をまとめてチェック（週次レビュー等）
$ novel check 1-7 --auto-validate --ai-assist --verbose
```

**プロット設計段階での確認**
```bash
# 全体構成作成後の確認
$ novel check-plot master --auto-validate --ai-assist

# 第1章プロット完成後の確認
$ novel check-plot chapter 1 --auto-validate --ai-assist --verbose

# プロット全体の最終確認
$ novel check-plot all --auto-validate --ai-assist --save-results
```

**企画段階での段階的チェック**
```bash
# 市場調査完了後の確認
$ novel check-project --phase market-research --auto-validate

# 企画全体の最終確認
$ novel check-project --auto-validate --ai-assist --save-results
```

**品質管理とレビューワークフロー**
```bash
# 公開前の全体品質チェック
$ novel check-all --auto-validate --ai-assist --save-results --verbose

# AI支援による改善提案のみ取得
$ novel check-all --ai-only --output-format markdown

# 手動確認が必要な項目のリスト表示
$ novel check-all --type manual-only
```

### 3.5 出力形式

#### 3.5.1 コンソール出力

```
🔍 自動チェック実行中...

📝 A31_原稿執筆チェックリスト - 第001話_システムエラーと魔法陣

Phase2_執筆段階:
  ✅ [A31-021] 冒頭3行で読者を引き込む工夫 - PASSED (score: 8.5)
  ✅ [A31-022] 会話と地の文のバランス - PASSED (35.2%)
  ❌ [A31-023] 五感描写を適切に配置 - FAILED
     └─ 嗅覚・味覚の描写が不足しています
  ✅ [A31-025] 文末の単調さを回避 - PASSED

Phase3_推敲段階:
  ✅ [A31-031] 誤字脱字の基本チェック - PASSED (0件)
  ⚠️  [A31-033] キャラクターの口調一貫性 - WARNING
     └─ レオの口調に2箇所不整合の可能性

Phase5_公開前最終確認:
  🤖 [A31-061] タイトルが内容を適切に表現 - AI_ASSISTED
     └─ 改善提案: 「第001話_エラーから始まる異世界デバッグ」
     └─ 理由: シリーズ全体のテーマを暗示してより魅力的
  🤖 [A31-062] 前書き・後書きの追加検討 - AI_ASSISTED
     └─ 提案: この話のシステムエラー要素について簡単な解説を追加
     └─ 効果: 読者の理解を助け、次話への期待感を高める

📊 チェック結果サマリー
  自動チェック: 22/25項目合格 (88.0%)
  AI支援項目: 6件 (改善提案あり: 4件)
  要対応項目: 3件

🤖 AI支援による改善提案を確認してください
💾 詳細結果を保存しました:
  50_管理資料/チェック結果/第001話_システムエラーと魔法陣_チェック結果.yaml
```

#### 3.5.2 レポート生成

**レポート構成**
- チェック結果レポートのタイトル
- 生成日時と対象ファイル情報
- 総合評価（自動チェック合格率、AI支援項目数、要対応項目数）
- フェーズ別の詳細結果
- 自動チェック失敗項目には改善提案を付与
- AI支援項目には分析結果と改善提案を詳細記載
- 優先度別の改善アクションリスト
- マークダウン形式で生成し、可読性を向上

## 4. 拡張性

### 4.1 新規チェックロジックの追加

新しいチェック項目を追加する場合は、以下の手順で実装：

1. YAMLチェックリストに項目を追加
2. 自動チェック対応の場合：対応する検証関数を実装
3. AI支援対応の場合：AIプロンプトテンプレートを作成
4. validators辞書またはai_assistants辞書に関数を登録

### 4.2 カスタムチェックリスト

プロジェクト固有のチェックリストも同様の仕組みで対応可能：

```yaml
# custom_checklist.yaml
checklist_items:
  プロジェクト固有チェック:
    - id: "CUSTOM-001"
      item: "魔法システムの一貫性確認"
      type: "custom_validation"
      auto_check: true
    - id: "CUSTOM-002"
      item: "デバッグ要素の魅力度確認"
      type: "content_review"
      auto_check: false
      ai_support: true
```

### 4.3 AI支援機能の拡張

- より高度な文章分析（感情分析、可読性スコア等）
- ジャンル特化型の分析モデル
- 読者レビューデータとの照合分析
- 複数話にわたる整合性チェック

## 5. 今後の拡張計画

1. **高度なAI分析**: GPT-4等の最新モデルを活用した深度分析
2. **統計分析**: 複数作品のチェック結果を統計的に分析
3. **自動修正提案**: 問題箇所に対する具体的な修正案の生成
4. **CI/CD統合**: GitHubActionsなどでの自動チェック実行
5. **ダッシュボード**: チェック結果の可視化とトレンド分析
6. **学習機能**: ユーザーのフィードバックからチェック精度を向上
7. **チーム機能**: 複数人でのチェック結果共有とレビュー機能
