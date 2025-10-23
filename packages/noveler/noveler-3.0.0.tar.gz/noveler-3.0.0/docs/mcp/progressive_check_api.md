# Progressive Check API 仕様書（LangGraph必須・セッションID対応）

最終更新: 2025-09-27
対象: MCP クライアント実装者・社内開発者

---

## 1. 概要

> CLI ラッパ方針: `noveler check` は評価導線、`noveler polish` は改稿導線。内部で ProgressiveCheckManager によりテンプレ/ステート/I-O を共通管理します。

Progressive Check は、大きな原稿の品質検査を段階的・部分的に実行・再開・参照するための API 群です。各 API は MCP ツールとして公開され、ハンドラ層では共通ラッパ `_safe_async` により統一エラー形式を返します。2025-09-27 以降は LangGraph を必須とし（`NOVELER_LG_PROGRESSIVE_CHECK=1` 運用）、セッション開始は `get_check_tasks` を起点とします（旧 `progressive_check.start_session` は非推奨）。

想定ユースケース:
- 大量テキストの「差分再チェック」
- CI での失敗箇所のみの再実行
- エディタ連携（進捗・履歴の可視化）

---

## 2. ツール一覧とI/O

### 2.1 get_check_tasks（セッション開始）
- 説明: 実行可能なチェックタスク一覧を返します。初回呼び出し時に LangGraph ワークフローの `session_id` を払い出します。
- 入力: `{ "episode_number": int, "project_root"?: string }`
- 出力 (success):
```json
{
  "success": true,
  "episode_number": 1,
  "session_id": "QC_EP001_20250927_0900",
  "current_step": 1,
  "current_task": {
    "id": 1,
    "name": "誤字脱字チェック",
    "phase": "basic_quality",
    "description": "基本的な誤字脱字の検出"
  },
  "executable_tasks": [
    { "id": 1, "name": "誤字脱字チェック", "phase": "basic_quality", "estimated_duration": "3-5分" },
    { "id": 2, "name": "文法・表記統一チェック", "phase": "basic_quality", "estimated_duration": "5-8分" }
  ],
  "progress": { "completed": 0, "total": 12, "percentage": 0.0 },
  "llm_instruction": "Step1 を実行し、結果を要約してください",
  "next_action": "execute_check_step",
  "phase_info": { "phase": "basic_quality" }
}
```

### 2.2 execute_check_step
- 説明: 指定タスクを実行します（dry-run対応）。
- 入力: `{ "episode_number": int, "step_id": int, "dry_run": bool, "options": object | null }`
- 出力 (success):
```json
{
  "success": true,
  "step_id": 202,
  "status": "completed",
  "issues": [ { "id": "EXPR-002", "severity": "moderate", "message": "比喩の多用" } ],
  "artifacts": [ { "path": "reports/quality/2025-09-22/expr_002.json", "sha256": "..." } ]
}
```

### 2.3 get_check_status
- 説明: 実行中・直近のチェックの進捗と状態を返します。`session_id` をレスポンスに含めるため、`episode_number` のみを指定すれば最新セッションを取得できます。
- 入力: `{ "episode_number": int, "project_root"?: string }`
- 出力 (success):
```json
{
  "success": true,
  "episode_number": 1,
  "session_id": "QC_EP001_20250927_0900",
  "status_info": {
    "session_id": "QC_EP001_20250927_0900",
    "episode_number": 1,
    "current_step": 4,
    "completed_steps": 3,
    "failed_steps": [],
    "progress": { "completed": 3, "total": 12, "percentage": 25.0 },
    "current_task": { "id": 4, "name": "構成バランスチェック" },
    "last_updated": "2025-09-27T09:15:22+09:00"
  },
  "message": "品質チェック進捗状況確認完了"
}
```

### 2.4 get_check_history
- 説明: 過去の実行履歴を返します。
- 入力: `{ "episode_number": int, "limit": int | null, "cursor": string | null }`
- 出力 (success):
```json
{
  "success": true,
  "history": [
    { "run_id": "20250922_101530", "status": "passed", "duration_ms": 5100 },
    { "run_id": "20250921_232011", "status": "failed", "failed_steps": [301] }
  ],
  "next_cursor": "eyJvZmZzZXQiOjEwfQ==",
  "order": "desc"
}
```

### 2.5 generate_episode_preview
- 説明: エピソードの要約・プレビューを生成します（レビュー用途）。
- 入力: `{ "episode_number": int, "style": "short|detailed" | null }`
- 出力 (success):
```json
{
  "success": true,
  "episode_number": 1,
  "preview": {
    "title": "第001話 新たな朝",
    "summary": "主人公は...",
    "key_points": ["転機", "目的の提示", "障害の予兆"]
  }
}
```

---

## 3. 統一エラー形式（_safe_async）

全 API は失敗時に次の形式で応答します。

```json
{
  "success": false,
  "error": "<human_readable_message>",
  "tool": "<tool_name>",
  "arguments": { "episode_number": 1, "step_id": 202 },
  "domain_logs": ["...optional structured logs..."]
}
```

補足:
- `arguments` はハンドラ側で `include_arguments=True` の場合のみ出力されます。
- 入力バリデーションエラーは 400 系、システム例外は 500 系に相当する `error` メッセージを返却（HTTP ではなく JSON プロトコル上の規約）。

---

## 4. パラメータ型と制約

| パラメータ | 型 | 必須 | 制約 |
|---|---|---|---|
| `episode_number` | int | ✔ | 1..9999 |
| `step_id` | int | execute_check_stepのみ | 正の整数 |
| `dry_run` | bool | 任意 | 既定: false |
| `limit` | int | 任意 | 1..100（既定: 20） |
| `style` | enum | 任意 | `short` or `detailed` |
| `m` | string | get_check_tasksのみ | `unit`/`integration`/`e2e` いずれか、または簡易 `pytest -m` 式（`and`/`or`/`not`/括弧のみ） |

---

## 5. 運用メモ（LangGraph/MCP/xdist）

- 並列実行時は、マーカーで対象集合を絞る: `-m "(not e2e) and (not integration_skip)"`。
- Domain 依存ガードは pytest キャッシュを用いるため、Domain 配下更新後は `pytest --cache-clear tests/unit/domain/test_domain_dependency_guards.py` を推奨。
- LangGraph 必須化: `NOVELER_LG_PROGRESSIVE_CHECK=1` を既定とし、`=0` の互換経路は廃止。
- `get_check_tasks` 応答には `session_id` が含まれ、ログは `.noveler/checks/<session_id>/` 配下に生成されます。
- 旧 `progressive_check.start_session` を呼び出した場合は、ガイダンス文を返して `get_check_tasks` へ誘導します。

---

## 6. 例: MCP クライアント呼び出し

```python
# get_check_tasks
client.call_tool("get_check_tasks", {"episode_number": 1})

# execute_check_step
client.call_tool("execute_check_step", {"episode_number": 1, "step_id": 202, "dry_run": false})

# get_check_status
client.call_tool("get_check_status", {"episode_number": 1})

# get_check_history
client.call_tool("get_check_history", {"episode_number": 1, "limit": 10})

# generate_episode_preview
client.call_tool("generate_episode_preview", {"episode_number": 1, "style": "short"})
```

---

## 7. 代表的エラー例

### 7.1 ValidationError（入力不正）
```json
{
  "success": false,
  "error": "step_id must be a positive integer",
  "tool": "execute_check_step",
  "arguments": { "episode_number": 1, "step_id": -5, "dry_run": false }
}
```

### 7.2 Timeout（実行タイムアウト）
```json
{
  "success": false,
  "error": "execution timeout (30000 ms)",
  "tool": "get_check_status",
  "arguments": { "episode_number": 1 },
  "domain_logs": ["check runner started", "warning: slow plugin ..."]
}
```

---

## 8. レスポンス要素スキーマ（簡易）

> 参考用の簡易スキーマです。実装の拡張によりフィールドが追加される場合があります。

### 8.1 issues 要素
```json
{
  "type": "object",
  "required": ["id", "severity", "message"],
  "properties": {
    "id": { "type": "string", "description": "一意識別子 (例: EXPR-002)" },
    "severity": { "type": "string", "enum": ["low", "moderate", "high", "critical"] },
    "message": { "type": "string" },
    "location": { "type": "string", "nullable": true },
    "suggestions": { "type": "array", "items": { "type": "string" } }
  }
}
```

### 8.2 artifacts 要素
```json
{
  "type": "object",
  "required": ["path", "sha256"],
  "properties": {
    "path": { "type": "string" },
    "sha256": { "type": "string" },
    "size_bytes": { "type": "integer", "minimum": 0 },
    "content_type": { "type": "string", "nullable": true }
  }
}
```

### 8.3 history 要素
```json
{
  "type": "object",
  "required": ["run_id", "status"],
  "properties": {
    "run_id": { "type": "string" },
    "status": { "type": "string", "enum": ["passed", "failed", "running", "canceled"] },
    "duration_ms": { "type": "integer", "minimum": 0 },
    "failed_steps": { "type": "array", "items": { "type": "integer" } }
  }
}
```

---

関連: B33 MCPツール統合ガイド（docs/B33_MCPツール統合ガイド.md）

---

## 9. `m` パラメータの簡易EBNF

```text
Expr    := Term { ("and" | "or") Term }
Term    := ["not"] Factor
Factor  := Ident | "(" Expr ")"
Ident   := "unit" | "integration" | "e2e"
```

例: `"unit or integration"`, `"not e2e"`, `"(unit and not e2e) or integration"`

---

## 10. execute_check_step.options のチェック別スキーマ（参照）

各チェックの `options` は以下の参照スキーマを基準とします（情報提供・後方互換優先／additionalProperties: true）。

| step_key        | Schema URI                                                        |
|-----------------|------------------------------------------------------------------|
| `basic`         | docs/mcp/schemas/execute_check_step.basic.schema.json            |
| `story_elements`| docs/mcp/schemas/execute_check_step.story_elements.schema.json   |
| `expression`    | docs/mcp/schemas/execute_check_step.expression.schema.json       |

---

## 11. エラーコード ↔ HTTP 相当コード（移植用）

| error_code      | HTTP 相当                  | 備考 |
|-----------------|----------------------------|------|
| validation_error| 400 Bad Request            | 入力不正 |
| not_found       | 404 Not Found              | 対象なし |
| timeout         | 408 Request Timeout        | 実行タイムアウト |
| busy            | 409 Conflict               | 競合（同一エピソード稼働中） |
| rate_limited    | 429 Too Many Requests      | レート超過 |
| internal_error  | 500 Internal Server Error  | 予期せぬ内部例外 |

注: MCP応答はHTTPではなくJSON-RPC準拠のため、上表はポータビリティ確保の参考値です。
