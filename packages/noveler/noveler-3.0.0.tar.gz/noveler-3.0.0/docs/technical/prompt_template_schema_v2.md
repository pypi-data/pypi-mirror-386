# Prompt Template Schema v2（A38準拠・構造化プロンプト仕様）

最終更新: 2025-09-25

---

## 目的
- テンプレート指示を「短い主指示 + 構造化セクション」へ分離し、LLMの遵守率・再現性・機械検証性・ツール連携性を高める。
- 既存の `prompt.main_instruction` は後方互換のため保持しつつ、実要件は構造化フィールドに定義する。

## 適用範囲と前提
- 対象: `templates/writing/*` および `templates/quality/checks/check_step*` に配置される各STEPテンプレート。
- 適用システム: ProgressiveWriteManager / ProgressiveCheckManager
- 前提: A38_執筆プロンプトガイド.md のコア制約（例: 8000字基準、視点統一、禁止表現回避）を踏まえる。
- 互換性: v1（従来）テンプレとの併存を許容。v2 が存在する場合は v2 を優先して合成する。

## 設計方針
- main_instruction は「目的の要約 + 構造化セクション参照 + 出力形式」のみ（3文以内が目安）。
- 入力（Inputs）、制約（Constraints）、作業（Tasks）、成果物（Artifacts）、検収（Acceptance）を main_instruction の外に分離。
- 成果物仕様と検収基準を明示し、自動検証可能にする。

---

## ルートキー一覧（概要）
- `metadata`（必須）: テンプレ識別・管理情報。
- `llm_config`（強推）: 役割メッセージ等の共通挙動を安定化。
- `prompt`（必須）: 主指示（短文）。
- `inputs`（強推）: 参照ファイル/変数の宣言。
- `constraints`（強推）: Hard/Soft の両制約。
- `tasks`（強推）: 具体タスクの箇条書き。
- `artifacts`（必須）: 出力形式/保存先/必須項目/例。
- `acceptance_criteria`（必須）: チェックリスト/メトリクス。
- `next`（必須）: 次工程への誘導（制御文の源）。
- `variables`（必須）: プレースホルダ解決に必要な共通変数。
- `control_settings`（必須）: 実行ガード（既存と同義）。

## 品質チェックテンプレート（ProgressiveCheckManager）
- LangGraph ワークフローでは `available_tools` ブロックを必須とし、各要素に `{tool_id, min_severity, requires_user_confirmation, fallback_tool_id}` を含める。
- 本文抜粋を扱う場合は `inputs.variables` に `manuscript_hash`, `excerpt_hash`, `source_key` を追加し、LLM へは抜粋のみを渡す。
- `control_settings.by_task` と併せて `tool_selection_status` を出力するテンプレート変数を定義し、WorkflowStateStore に記録する。
- 対象: `templates/quality/checks/check_step01_typo_check.yaml` 〜 `check_step12_final_quality_approval.yaml`。
- 追加必須キー: `check_criteria`（issuesカテゴリの定義）、`control_settings.by_task`（issues.* との対応付け）、必要に応じて `control_settings.final_step`。
- `artifacts.required_fields` は `{"summary", "issues", "recommendations", "metrics"}` を固定化。
- `variables` は基底6項目（step_id / step_name / episode_number / completed_steps / total_steps / phase）を必ず含める。
- `acceptance_criteria.checklist` + `metrics` により LLM 出力を機械検証。`control_settings.by_task[*].field` は `issues.<category>` 形式で記述し、`check_criteria` に同じカテゴリ ID を定義する。
- STEP12 のみ `control_settings.final_step: true` を設定し、`next.message_template` で完了メッセージを明示する。

---

## フィールド定義（詳細）

### 1) metadata（必須）
- `step_id`: int（0–18）
- `step_name`: string
- `phase`: enum {structural_design, content_development, writing_execution, quality_assurance, publication}
- `version`: semver（例: "2.0.0"）
- `last_updated`: YYYY-MM-DD
- `author`: string（任意）
- `description`: string（任意）

### 2) llm_config（強く推奨）
- `role_messages.system`: string（ハード制約/出力形式/安全策などの宣言を記載）
- `role_messages.user`: string（このSTEPの狙いと、参照セクションの指示）
- `params`: 任意（`temperature`, `top_p`, `max_tokens` など将来拡張）

### 3) prompt（必須）
- `main_instruction`: string（目的の要約 + 構造化セクション参照 + 出力形式明示）

### 4) inputs（強く推奨）
- `files[]`:
  - `path`: string（テンプレ可）例: `{project_root}/20_プロット/話別プロット/ep{episode_number:03d}.yaml`
  - `required`: bool
  - `description`: string（任意）
- `variables`（map）:
  - 任意の変数名: `{ type: enum{int,string,path,bool}, required: bool, description?: string }`

### 5) constraints（強く推奨）
- `hard_rules[]`: 破るとNGなルール（例: 「8000字以上（日本語Unicode）」）
- `soft_targets[]`: 目安（例: 「セクション配分15/70/15%」）

### 6) tasks（強く推奨）
- `bullets[]`: 実行すべき具体タスク（短文・検証可能粒度）
- `details[]`（任意だが推奨）: サブタスクの構造化定義
  - `name`: string（小見出し）
  - `items[]`: 以下いずれかの形式
    - string（従来互換）
    - object（推奨）：`{ id: string, text: string, required?: bool }`
      - `id`: 検収とトレーサビリティ用の安定ID（例: `start.inner_state`）
      - `text`: LLMが実行すべき観点の説明
      - `required`: 必須観点なら true（省略時は true と解釈）

例（STEP1の一部）:
```yaml
tasks:
  bullets:
    - 開始/終了状態（内面/外面/関係性）を定義する
  details:
    - name: 開始状態の定義
      items:
        - id: start.inner_state
          text: 主人公の内面状態（感情/認識/目標）
        - id: start.approval_density
          text: 承認欲求表現密度（1000字あたり定量）
        - id: start.outer_state
          text: 外面状況（立場/環境/関係性）
        - id: start.surroundings
          text: 周囲の状況（世界・他キャラの状態）
```

### 7) artifacts（必須）
- `format`: enum{yaml,md,txt,json}
- `path_template`: string（変数可）
- `required_fields[]`: list（YAMLキー/JSONパス/Markdown見出し 等）
- `example`: string（最小有効サンプル: 5–20行推奨）
> ルール: format=yaml の場合、`required_fields` はトップレベルキー名で指定。

### 8) acceptance_criteria（必須）
- `checklist[]`: 真偽で判定できる検収項目
- `metrics[]`: `{ name, target, method }` の配列
  - 例: `{ name: "spec_completeness", target: ">= 1.0", method: "必須キー充足率" }`
- `by_task[]`（任意だが推奨）: `tasks.details.items[].id` と出力フィールド/判定条件のマッピング
  - 要素: `{ id: string, field: string, rule?: string, range?: string }`
    - `field`: 出力YAMLのフィールド（トップレベル相対パス。例: `story_structure.start_state.inner`）
    - `rule`: `present|nonempty|enum:...|regex:...` などの簡易規則
    - `range`: `a-b` 形式の数値範囲指定（例: `0.60-0.70`）

例（STEP1の一部）:
```yaml
acceptance_criteria:
  by_task:
    - id: start.inner_state
      field: story_structure.start_state.inner
      rule: present
    - id: start.approval_density
      field: story_structure.approval_density_per_1000
      range: 3-5
```

### 9) next（必須）
- `next_step_id`: int（0–18）
- `message_template`: string（既存の「次は …」制御文の元文）

### 10) variables（必須）
- 既定: `step_id, step_name, episode_number, completed_steps, total_steps, phase`

### 11) control_settings（必須）
- 既定: `strict_single_step: true, require_completion_confirm: true, auto_advance_disabled: true, batch_execution_blocked: true`
- 任意: `final_step: true`（STEP18など）

---

## バリデーション規則
1. 必須キー
   - ルート: `metadata, prompt, artifacts, acceptance_criteria, next, variables, control_settings` 必須。
   - `metadata.step_id` は 0–18。
   - `artifacts.format` は列挙値、`path_template` はプレースホルダ解決可能。
2. 参照整合
   - `next.next_step_id` は工程に整合。
   - `artifacts.required_fields` は `artifacts.example` に最低1回以上出現（format=yaml のとき）。
3. 内容検査（推奨）
   - A38のコア制約（8000字/視点統一/禁止表現回避）が該当STEPで `constraints.hard_rules` に含まれる。
   - `inputs.files[].required=true` のパスは存在が確認可能なパターン。

---

### バリデーション実行方法
- `make validate-templates` で品質テンプレート専用のスキーマチェックを実行。
  - 内部で `tests/unit/templates/test_quality_check_schema_v2.py` を呼び出し、必須キー・by_task整合・exampleのJSON妥当性を確認。
  - CI (`make ci`) に組み込み済み。テンプレ変更時はローカルでも実行して差分を検証する。

## 自動バリデータ仕様（by_task準拠）

目的: acceptance_criteria.by_task に基づき、生成物（artifacts.format=yaml/markdown）の充足を機械的に判定する。

### 評価対象
- YAML出力（format=yaml）: by_task.field をトップレベル相対パスとして解釈し、値を取得して判定。
- Markdown出力（format=md）: by_task は任意。原則は metrics と checklist を評価する。必要に応じてメタ注釈等で拡張可。

### ルール評価
- `rule`（省略可）
  - `present`: フィールドが存在する
  - `nonempty`: フィールドが存在し、空でない（配列/文字列/オブジェクト/数値）
  - `enum:a|b|c`: 文字列値が列挙いずれかに一致
  - `regex:...`: 文字列値が正規表現にマッチ
- `range`（省略可）
  - 形式: `min-max`（例: `0.60-0.70`）
  - 数値（int/float）に変換して判定。`min`/`max` どちらか省略可（`-max` や `min-`）。
- 併用時は AND 判定（`rule` と `range` を両方満たす必要）。

### フィールド解決
- by_task.field は `a.b.c` のドット記法をサポート。配列は次のいずれか:
  - `nodes`: 配列全体に対して `nonempty` 等の集合判定を適用
  - 配列要素の個別評価や探索は今後の拡張（v2.1）で `[*].field` 記法を追加予定

### 判定ロジック
- details.items[].required が明示 true（または省略）で、対応する by_task が存在し、かつ判定成功 → 合格
- required だが by_task が存在しない → 警告（WARN）または実装ポリシーで不合格（推薦はWARN）
- 非必須（required=false）の観点は by_task が無くても合格に影響しない
- ファイル全体の合否は:
  - checklist（すべてtrue）AND metrics（しきい値クリア）AND by_task（required観点が全て合格）

### レポート形式（推奨JSON）
```json
{
  "success": true,
  "by_task": [
    {"id":"start.inner_state","status":"pass"},
    {"id":"start.approval_density","status":"fail","expected":"range 3-5","actual":2.1}
  ],
  "checklist": {"all": true, "failed": []},
  "metrics": {"unicode_char_count": 8123, "total_score": 0.86},
  "errors": []
}
```

### 既定動作
- 合否（success）は上記ロジックで決定。
- 阻害要因（パース失敗/型不一致など）は `errors[]` に収集し success=false。

### スコア表記の取り扱い（基準）
- 機械検証・集計用のスコアは 0–1 実数を準拠値とする。
- 表示用/ドキュメントの説明は 0–100 のパーセンテージを用いてよい（例: 80% ≒ 0.80）。
- テンプレの `metrics.target` は 0–1 の表記を推奨。

---

## プロンプト合成順序（推奨）
1. `llm_config.role_messages.system`
2. `llm_config.role_messages.user`
3. `prompt.main_instruction`
4. 構造化セクション（`inputs`, `constraints`, `tasks`, `artifacts`, `acceptance_criteria`）
5. 必要に応じて `artifacts.example` を参考情報として末尾に添付（LLMへ貼る場合はコメント扱い）。

---

## 例: STEP 0（スコープ定義）v2 テンプレ（抜粋）

```yaml
metadata:
  step_id: 0
  step_name: "スコープ定義"
  phase: "structural_design"
  version: "2.0.0"
  last_updated: "2025-09-23"

llm_config:
  role_messages:
    system: |
      あなたはプロ編集者です。constraints.hard_rules を必ず遵守し、
      出力は artifacts の仕様どおりに YAML のみを返してください。
    user: |
      本STEPはエピソードのスコープ定義です。inputs/constraints/tasks/artifacts を参照してください。

prompt:
  main_instruction: |
    目的は「エピソード{episode_number}のスコープ定義」です。
    inputs/constraints/tasks を満たし、artifacts の YAMLのみをコードブロックで出力してください。

inputs:
  files:
    - path: "{project_root}/20_プロット/話別プロット/ep{episode_number:03d}.yaml"
      required: true
      description: 話別プロット
  variables:
    episode_number: { type: int, required: true }
    PROJECT_ROOT: { type: path, required: true }

constraints:
  hard_rules:
    - "文字数基準: 8000字以上（日本語Unicode）"
    - "視点統一: 1シーン1視点"
    - "禁止表現回避: 直説説明/感情直書きを用いない"
  soft_targets:
    - "セクション配分: 15/70/15%"
    - "承認欲求表現密度: 3-5箇所/1000字"
    - "山場の位置: 後半2/3"

tasks:
  bullets:
    - 前後話の引き継ぎ要素を特定する
    - 物語目標・読者体験・キャラ成長を具体化する
    - ハード制約の運用方針を記述する

artifacts:
  format: yaml
  path_template: "{project_root}/60_作業ファイル/EP{episode_number:03d}_step00.yaml"
  required_fields: ["scope_definition", "constraints", "handover_to_next"]
  example: |
    scope_definition:
      story_goal: "○○を達成し△△を示す"
      reader_experience: "緊張→高揚→余韻"
      character_growth: "内面A→B"
      continuity:
        from_prev: ["前話の引き継ぎ要素1"]
        to_next: ["次話への布石1"]
    constraints:
      word_count_min: 8000
      pov_policy: "one_pov_per_scene"
      banned_expressions_policy: "直説説明/感情直書きを避ける"
    handover_to_next:
      notes: "配分/山場/承認密度をSTEP1/2へ引き渡し"

acceptance_criteria:
  checklist:
    - "required_fields がすべて存在する"
    - "word_count_min >= 8000 が明記されている"
    - "pov_policy と banned_expressions_policy が明記されている"
  metrics:
    - name: "spec_completeness"
      target: ">= 1.0"
      method: "必須キー充足率"
    - name: "typo_error_rate"
      target: "<= 0.001"
      method: "誤字率（推定）。A41では0.1%以下を合格閾値とする。"

next:
  next_step_id: 1
  message_template: |
    次のステップは以下で実行:
    execute_writing_step episode_number={episode_number} step_id=1

variables: [step_id, step_name, episode_number, completed_steps, total_steps, phase]

control_settings:
  strict_single_step: true
  require_completion_confirm: true
  auto_advance_disabled: true
  batch_execution_blocked: true
```

---

## 後方互換方針
- v1 の長い `main_instruction` は当面許容（残置）。
- v2 が存在する場合、プロンプト合成器は v2 の構造化セクションを優先。
- 当面は `artifacts` と `acceptance_criteria` の検証を必須とし、他は警告ログに留める。

## バージョニング
- semver 準拠。破壊的変更は MAJOR をインクリメント。
- 本書は v2 の初版仕様。将来、共通 `system` メッセージの外部共通化も検討可能。

## 移行手順（推奨）
1. STEP 0 を v2 化（例のとおり）。
2. STEP 1/2/3/12/16/17 を段階展開（数値KPIの多いSTEPを優先）。
3. 全STEPへ展開し、CLI/MCP側で構造化セクションを優先合成。
4. 自動検証: 必須キー、例の整合、ファイル存在、メトリクスの閾値チェックを導入。

## 運用ガイド
- LLMへ貼る順序は「System → User → main_instruction → 構造化セクション」。
- RAG/コンテキスト注入は `inputs.files` を基に自動解決する。
- `artifacts.example` は開発者向けの最小例。LLMへ渡す場合は注釈扱いにすること。

### 追加セクション: manuscript_excerpt (任意)
- 本文抜粋を構造化する場合に使用。
- 推奨フィールド: `excerpt_text`, `excerpt_hash`, `source_key`, `range_checksum`, `notes`.
