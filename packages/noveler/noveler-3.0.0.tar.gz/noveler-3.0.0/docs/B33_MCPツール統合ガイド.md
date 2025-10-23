# B33_MCPツール統合ガイド

最終更新: 2025-09-02
バージョン: v2.0.0 (マイクロサービス統合版)
対象: システム開発者・執筆システム利用者

## 📋 概要

小説執筆支援システムの**18個のマイクロサービス型MCPツール**とJSON変換システムを統合し、**95%のトークン削減**とClaude Codeでの直接利用を実現する統合ガイド。

### 🎯 主要機能

- **18個のMCPツール**: 単一責任・独立実行可能なマイクロサービス
- **Claude Code直接統合**: MCPサーバー登録による透明な連携
- **JSON変換**: CLI実行結果を構造化JSONに自動変換（95%トークン削減）
- **完全性保証**: SHA256による改ざん検出・エラー復旧
- **チェック→修正→再チェック**: 効率的な品質向上サイクル

### 📂 統合アーキテクチャ

```
MCPツール統合システム
├── 18個のマイクロサービス型ツール
│   ├── 執筆関連（3個）: noveler_write, write_stage, write_resume
│   ├── 品質チェック（8個）: noveler_check, check_basic, check_story_elements, fix_style_extended等
│   ├── プロット関連（1個）: noveler_plot
│   ├── プロジェクト管理（2個）: status, noveler_complete
│   └── JSON変換（3個）: convert_cli_to_json等
├── JSON変換エンジン（95%トークン削減）
├── ファイル参照システム（SHA256完全性保証）
└── Claude Code統合ブリッジ
```

---

## 🚀 17個のマイクロサービス型MCPツール

### 📝 執筆関連ツール（3個）

| ツール名 | 機能 | 主な用途 | 使用例 |
|---------|------|---------|-------|
| `noveler_write` | 小説エピソード執筆（全19ステップ） | Schema v2準拠の段階的執筆で高品質原稿を生成 | `mcp__noveler__noveler_write(episode=1)` |
| `write_stage` | 特定ステージのみ執筆実行 | plot_data_preparation等の個別実行・再開可能 | `mcp__noveler__write_stage(episode=1, stage="plot_analysis")` |
| `write_resume` | 中断位置から執筆再開 | セッションIDを指定して前回の続きから実行 | `mcp__noveler__write_resume(episode=1, session_id="xxx")` |

#### 19ステップ構成概要（Schema v2）
0. **Scope Definition**: スコープ定義・制約整理
1. **Chapter Purpose**: 章の目的線明文化
2. **Section Goals**: セクション配分設計
2.5. **Theme Uniqueness**: テーマ独自性検証
3. **Section Balance**: 構造バランス調整
4. **Scene Beats**: シーン／ビート展開設計
5. **Logic Verification**: 因果・整合性チェック
6. **Character Detail**: キャラクター詳細設計
7. **Dialogue Design**: 対話設計
8. **Emotion Curve**: 感情曲線設計
9. **Atmosphere & Worldview**: 雰囲気・世界観演出
10. **Foreshadow Placement**: 伏線配置
11. **First Draft**: 初稿生成
12. **Style Adjustment**: 文体調整
13. **Description Enhancement**: 描写強化
14. **Readability Optimization**: 読みやすさ最適化
15. **Quality Check**: 品質チェック（KPI連動）
16. **Reader Experience**: 読者体験最適化
17. **Final Preparation**: 公開準備
18. **Completion**: 最終確認・引き継ぎ

> **LLM制御**: `defaults.writing_steps.use_llm`（config/novel_config.yaml）を `true` にすると各ステップ実行時に LLM プロンプトが送信されます。CI やオフライン検証時は `false` のままモック executor で実行します。テンプレート仕様は `docs/technical/prompt_template_schema_v2.md` を参照してください。

### 🔍 品質チェック関連ツール（8個）

> LangGraph 版 ProgressiveCheckManager は SPEC-QUALITY-120 に従い `WorkflowStateStore` を介した状態管理・`available_tools` 提示・本文ハッシュ参照（fetch_artifact → read_snapshot → request_manual_upload）を実装する。失敗時は QC-015〜018 を返却する。

| ツール名 | 機能 | 具体的なチェック内容 |
|---------|------|---------------------|
| `noveler_check` | 完全品質チェック（3段階） | 基本→小説要素（68項目）→プロレベル評価を段階的実行 |
| `check_basic` | 基本品質チェック | 文字数、禁止表現、文章構造、誤字脱字等 |
| `check_story_elements` | 小説の基本要素評価（68項目） | **感情描写（12項目）**: 「怒り」「喜び」等の感情表現が具体的か/読者が共感できる描写か<br>**キャラクター（12項目）**: 口調・行動パターンが一貫しているか/個性的で魅力的か<br>**ストーリー展開（12項目）**: 起承転結が明確か/伏線が効果的に配置・回収されているか<br>**文章表現（12項目）**: 情景描写に臨場感があるか/比喩・修辞が効果的か<br>**世界観・設定（10項目）**: 設定に矛盾がないか/独自性・オリジナリティがあるか<br>**読者エンゲージメント（10項目）**: 冒頭で読者を引き込めているか/続きが気になる構成か |
| `check_story_structure` | ストーリー構成評価 | **ストーリー整合性**: 前後の展開との矛盾・時系列の破綻を発見<br>**起承転結の完成度**: 導入の引き込み・クライマックスの衝撃・結末の満足度<br>**伏線と回収**: 効果的な配置・意外性と納得感のバランス<br>**ペース配分**: 場面転換の自然さ・読者を飽きさせない展開速度 |
| `check_writing_expression` | 文章表現力評価 | **文章の自然さ**: 不自然な表現・違和感のある文章構造を検出<br>**描写力**: 情景描写の臨場感・五感に訴える表現<br>**比喻と修辞**: 効果的な比喩表現・独創的な表現<br>**商業作品比較**: プロ作家の作品と比較した文章力評価 |
| `check_rhythm` | 文章リズム・読みやすさ分析 | 文の長さのバリエーション・読点の配置・漢字バランス等 |
| `check_fix` | 問題箇所の自動修正実行 | 検出された問題を自動修正（safe/standard/aggressive） |
| `fix_style_extended` | style拡張機能（opt-in） | **FULLWIDTH_SPACE正規化**: 全角スペースの半角化/除去（台詞・地の文切替対応）<br>**BRACKETS_MISMATCH自動補正**: 日本語括弧ペアの不一致を自動修正<br>**dry_runデフォルト**: 差分表示のみで安全性重視 |
| `test_result_analysis` | テスト結果解析とエラー構造化 | pytest の JSON レポートを解析し、失敗分類・再現コマンド・改善提案を LLM が扱いやすい Issue 形式で返却 |

### 📊 プロット関連ツール（1個）

| ツール名 | 機能 | 使用例 |
|---------|------|-------|
| `noveler_plot` | プロット生成 | A28プロンプト準拠のプロット生成（`regenerate=true` で再生成） |

> **補足**: 旧 `plot_validate` ツールは廃止されています。プロット品質の検証は `check_story_structure` や `check_story_elements` を組み合わせて実施してください。

### 🗂️ プロジェクト管理ツール（2個）

| ツール名 | 機能 | 使用例 |
|---------|------|-------|
| `status` | プロジェクト状況確認 | 執筆済み話数、品質スコア、進捗状況を表示 |
| `noveler_complete` | 完了処理・公開準備 | 原稿最終化や成果物パッケージ化を支援 |

> **補足**: `init` ツールは 2025-09-18 に廃止済みです。初期セットアップはテンプレートコピーまたは `noveler` CLI の `project create` 等で実施してください。

### 🔧 JSON変換ツール（3個）

| ツール名 | 機能 | 用途 |
|---------|------|-----|
| `convert_cli_to_json` | CLI→JSON変換実行 | AI エージェント統合・95%トークン削減 |
| `validate_json_response` | JSON形式検証 | データ品質保証 |
| `get_file_reference_info` | ファイル参照情報取得 | 完全性チェック付きファイル情報取得 |

---

## 運用のポイント（2025-09-27更新）

- Progressive Check は LangGraph を既定実行基盤とします。`NOVELER_LG_PROGRESSIVE_CHECK=1` を前提にしてください（互換モードは廃止）。
- pytest の既定タイムアウトは `pytest-timeout` を利用し、長時間テストのハングを防止します（例: `bin/test --timeout=300`）。
- `pytest-xdist` で並列化する場合、ワーカー別ログを分離してください（例: `reports/{worker}/pytest_gw*.log`）。
- 並列実行は `-m "(not e2e) and (not integration_skip)"` で対象を絞ると安定します。

---

## 🎯 効率的な使用パターン

### パターン1: 基本的な修正サイクル
```python
# 1. 完全品質チェック実行
result = mcp__noveler__noveler_check(episode=3)
# → 基本・小説要素・プロレベル評価で問題発見

# 2. 小説要素評価で低スコア項目を自動修正
mcp__noveler__check_fix(episode=3, fix_level="standard")

# 3. 小説要素のみ再チェックして改善確認
mcp__noveler__check_story_elements(episode=3)
```

### パターン2: 段階的執筆と品質確認
```python
# 1. 特定ステージまで執筆
mcp__noveler__write_stage(episode=3, stage="plot_analysis")

# 2. 途中で基本チェック
mcp__noveler__check_basic(episode=3)

# 3. 問題があれば修正後、続きから再開
mcp__noveler__write_resume(episode=3, session_id="xxx")
```

### パターン3: プロレベル評価による高度な改善
```python
# 1. ストーリー構成評価
mcp__noveler__check_story_structure(episode=3)

# 2. 文章表現力評価
mcp__noveler__check_writing_expression(episode=3)

# 3. 文章リズムの詳細分析
mcp__noveler__check_rhythm(episode=3)

# 4. 改善提案に基づく修正
mcp__noveler__check_fix(episode=3, issue_ids=["STRUCT-001", "EXPR-002", "RHYTHM-003"])
```

### パターン4: style拡張機能によるテキスト品質向上
```python
# 1. 全角スペース問題の確認（dry_run）
mcp__noveler__fix_style_extended(episode=3, fullwidth_space_mode="normalize", dry_run=true)

# 2. 台詞内の全角スペースのみ正規化
mcp__noveler__fix_style_extended(episode=3, fullwidth_space_mode="dialogue_only", dry_run=false)

# 3. 括弧の対応不一致を自動補正
mcp__noveler__fix_style_extended(episode=3, brackets_fix_mode="conservative", dry_run=false)

# 4. 複合的な修正（全角スペース+括弧）
mcp__noveler__fix_style_extended(
    episode=3,
    fullwidth_space_mode="narrative_only",
    brackets_fix_mode="auto",
    dry_run=false
)
```

---

## 🧩 エンハンスト執筆ユースケース（診断/復旧対応）

EnhancedWritingUseCase を用いた補助ツールを提供します。標準ツールと併存し、エラーハンドリングや復旧を強化した経路です。

- `enhanced_get_writing_tasks`
  - 例: `noveler mcp call enhanced_get_writing_tasks '{"episode_number":1}'`
- `enhanced_execute_writing_step`
  - 例: `noveler mcp call enhanced_execute_writing_step '{"episode_number":1,"step_id":1,"dry_run":false}'`
- `enhanced_resume_from_partial_failure`
  - 例: `noveler mcp call enhanced_resume_from_partial_failure '{"episode_number":1,"recovery_point":5}'`

戻り値には `execution_method: enhanced_use_case` が含まれ、復旧が適用された場合は `recovery_applied: true` を返します。

---

## ✅ プログレッシブチェック機能（新規）

Progressive Check API は段階的な品質検査の実行・参照を可能にします。各ツールの詳細仕様は `docs/mcp/progressive_check_api.md` を参照してください。

### 提供ツール
- `get_check_tasks(episode_number, m?)` … 実行可能タスク一覧
- `execute_check_step(episode_number, step_id, dry_run?, options?)` … タスク実行
- `get_check_status(episode_number)` … 実行状態・進捗
- `get_check_history(episode_number, limit?)` … 履歴参照
- `generate_episode_preview(episode_number, style?)` … 要約プレビュー

### 統一エラー形式（_safe_async）
すべてのツールは失敗時に以下の形式を返します。

```json
{
  "success": false,
  "error": "<message>",
  "tool": "<tool_name>",
  "arguments": { "episode_number": 1, "step_id": 202 },
  "domain_logs": ["..."]
}
```

### 運用メモ（並列・キャッシュ）
- 並列実行は `-m "(not e2e) and (not integration_skip)"` で対象を絞ると安定します。
- Domain 依存ガードは pytest キャッシュを使うため、Domain 配下更新後は `pytest --cache-clear tests/unit/domain/test_domain_dependency_guards.py` を推奨。
- 既定タイムアウトの指針: 基本 30s、長時間タスクは 120s を目安に設定（クライアント側で上書き可）。
- 同一エピソードの並行実行は非推奨。稼働中の実行がある場合、`busy` エラーで応答する運用を推奨。
- `run_id` 命名は `YYYYMMDD_HHMMSS_{worker}` を推奨し、ワーカー別に `reports/{worker}/` へ出力を分離。
- アーティファクトの保持は既定 30日、1ファイル 50MB を上限の目安とする（運用環境に合わせ調整）。

---

## 🚀 Claude Code統合セットアップ

### 1. 自動セットアップ（推奨）

```bash
# プロジェクトディレクトリで実行
python bin/claude_code_mcp_setup.py
```

**実行結果**:
```
🚀 Claude Code MCP統合セットアップ開始
📦 依存関係インストール中...
✅ mcp インストール完了
✅ pydantic>=2.0.0 インストール完了
⚙️  MCP設定ファイル作成中...
✅ 設定ファイル作成完了: codex.mcp.json
🔍 インストール検証中...
✅ MCPサーバー動作検証成功
🎉 Claude Code MCP統合セットアップ完了!
```

### 2. Claude Code設定統合

生成された設定を Claude Code の設定ファイルにコピー：

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux:** `~/.config/claude/claude_desktop_config.json`

#### 設定ファイルの優先順位と設置場所（重要）
- 優先順位:
  1) `codex.mcp.json`（リポジトリ直下・Claude/Codex用のプロジェクトローカル設定）
  2) `.mcp/config.json`（プロジェクト直下の`.mcp/`フォルダ内・一般的なMCPクライアント設定）
- ルール:
  - 両方が存在する場合は `codex.mcp.json` を優先します。
  - CI/本番向けのサンプルとして `scripts/build.py` は `.mcp.production.json` を生成します（必要に応じて `.mcp.json` にリネームして使用）。

### 3. Claude Code 再起動

設定反映のためClaude Codeを再起動します。

---

## 📊 JSON変換システム（95%トークン削減）

### 入力形式例（CLI結果JSON）

```json
{
  "success": true,
  "command": "core write 1",
  "content": "# 第1話 新しい始まり\n\n朝の陽射しが窓から差し込んでくる。...(5000文字)",
  "yaml_content": "title: \"第1話 新しい始まり\"\nepisode_number: 1",
  "metadata": {
    "word_count": 3500,
    "character_count": 5000,
    "quality_score": 85.5
  }
}
```

### 出力形式（95%削減後）

```json
{
  "success": true,
  "command": "core write 1",
  "execution_time_ms": 2500.0,
  "outputs": {
    "files": [
      {
        "path": "novel_write_1_20250902_214438_c6cad537.md",
        "sha256": "8c7e7f2dbea428f676fcd62da5e39aecaa692fe7abce25a92e04421ccbf481dc",
        "size_bytes": 5123,
        "content_type": "text/markdown"
      }
    ],
    "total_files": 2,
    "total_size_bytes": 225
  },
  "metadata": {
    "word_count": 3500,
    "character_count": 5000,
    "quality_score": 85.5
  }
}
```

---

## 🔧 技術詳細

### 設定ファイル詳細

```json
{
  "mcpServers": {
    "noveler": {
      "command": "python",
      "args": [
        "src/mcp_servers/noveler/main.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "NOVEL_PRODUCTION_MODE": "1",
        "MCP_STDIO_SAFE": "1"
      },
      "cwd": "/path/to/project/root",
      "description": "小説執筆支援システム MCP サーバー（writing/quality ツール群）"
    }
  }
}
```

### マイクロサービス設計原則

1. **単一責任原則**: 1ツール1機能
2. **独立性**: 各ツールが独立して実行可能
3. **再実行可能性**: 個別チェックの繰り返し実行に最適化
4. **段階的修正**: チェック→修正→再チェックのサイクル対応

### 命名規則
- 主要ツール名はシンプルに（`noveler_write`, `noveler_check`等）
- サブ機能は`_`で接続（`check_basic`, `write_stage`等）
- 修正系は`check_fix`として統合

---

## 🔍 トラブルシューティング

### よくあるエラー

#### 1. `ModuleNotFoundError: No module named 'noveler'`

**原因**: PYTHONPATH設定不備

**解決**:
```bash
# 手動でPYTHONPATH設定
export PYTHONPATH="/path/to/project/root:$PYTHONPATH"
```

#### 2. `MCPライブラリが見つかりません`

**原因**: MCP依存関係未インストール

**解決**:
```bash
pip install mcp pydantic>=2.0.0
```

#### 3. `ツールが見つかりません`

**原因**: MCPサーバー登録不備

**解決**:
```bash
# MCPサーバーテスト起動（StdIO 経由）
PYTHONUNBUFFERED=1 MCP_STDIO_SAFE=1 NOVEL_PRODUCTION_MODE=1 \
  python src/mcp_servers/noveler/main.py

# ヘルスチェック
python tests/test_mcp_connection.py
```

---

## 📈 成功指標

### 定量的指標
- **ツール選択精度の向上**: LLMが適切なツールを選択する精度
- **チェック実行時間の短縮**: 個別実行による効率化（平均2秒以下）
- **修正サイクル回数の削減**: チェック→修正→再チェックの効率化
- **トークン削減効果**: 95%トークン削減の実現

### 定性的指標
- **開発者の使いやすさ向上**: 目的に応じたツール選択の容易さ
- **エラーメッセージの分かりやすさ**: 具体的な改善提案
- **新機能追加の容易性**: マイクロサービス化による拡張性

---

## 📚 関連ドキュメント

- **SPEC-MCP-001.md**: MCP Server Granular Microservice Architecture仕様書
- **B31_MCPマイクロサービス設計ガイド.md**: アーキテクチャ設計原則
- **A32_執筆コマンドガイド.md**: 執筆支援コマンド完全リファレンス

---

**最終更新**: 2025-09-02
**バージョン**: v2.0.0 (マイクロサービス統合版)
**責任者**: Claude Code開発チーム

---

## 🆕 新規/拡張ツールと軽量化オプション（B20準拠）

### improve_quality_until（新規）
- 目的: 各評価項目で「自動修正→再評価」を上限付きで反復し、合格（既定80点）で次項目へ進む段階ゲート方式を自動化。
- 既定: `target_score: 80` / `max_iterations: 3` / `min_delta: 0.5` / `severity_threshold: "medium"`。
- 出力方針: 本文は返さず `issue_id`/`file_hash`/`line_hash`/`block_hash` など識別子中心。必要時のみ `get_issue_context` で周辺数行取得。
- 使用例:
  - `improve_quality_until({ episode_number: 1, file_path: "40_原稿/EP001_scene01.md", aspects: ["rhythm","readability","grammar"], target_score: 80, include_diff: false })`

### 既存ツールの軽量オプション
- run_quality_checks
  - `format: "summary"` で要約のみ返却。
  - `page` / `page_size` によるページネーション（既定上限200件、超過時 `metadata.pagination` / `truncated: true`）。
  - `format: "ndjson"` はページ適用後の範囲のみを `metadata.ndjson` に同梱。
  - 付与メタ: `total_issues` / `returned_issues` / `aspect_scores` / `pagination` / `truncated`。
- fix_quality_issues
  - `include_diff: false`（既定）。必要時のみ `true` + `max_diff_lines` で短縮diff。
  - 自動修正対象は安全な `reason_codes` に限定する運用を推奨。


### 🆕 Progressive Check API（12ステップ段階実行・反復）
- 目的: ProgressiveCheckManager を MCP から直接制御し、12ステップを段階実行／反復（until_pass/回数/時間）できるようにする。
- 役割: ライトウェイト系（run_quality_checks/improve_quality_until）とは分離。テンプレートは Schema v2 をロード。

- 初回の `get_tasks` で払い出された `session_id` はレスポンスに含まれるため、後続リクエストは `episode_number` のみ指定すれば自動的に同一セッションへルーティングされる。
```bash
# タスクリスト取得（session_id 付与）
noveler mcp call progressive_check.get_tasks '{"episode_number":1}'
# -> success:true, session_id: "QC_EP001_...", tasks_info: {...}

# ステップ実行（反復3回・合格で停止）
noveler mcp call progressive_check.execute_step '{
  "episode_number":1,
  "step_id": 1,
  "input_data": {"manuscript_content": "..."},
  "iteration_policy": {"count":3, "until_pass": true, "min_improvement": 1.0}
}'

# 進捗取得（episode_number のみで最新セッションを解決）
noveler mcp call progressive_check.get_status '{"episode_number":1}'

# セッション終了（任意で session_id を明示可能）
noveler mcp call progressive_check.end_session '{"session_id":"QC_EP001_..."}'
```

- `progressive_check.start_session` は廃止。呼び出した場合は `"use progressive_check.get_tasks"` ガイダンスを返却する。
- I/O 保存: `.noveler/checks/{session_id}/` に manifest と LLM 入出力 JSON を必ず生成。プロンプト全文や長大な生成物は `.noveler/artifacts/` に参照保存。
- 反復ポリシー: count/time_budget_s/until_pass/min_improvement（詳細は SPEC-QUALITY-110 参照）。
```
```
