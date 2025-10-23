# Claude Code novelerコマンド設定ファイル

このファイルは `/home/bamboocity/.claude/commands/noveler.md` と同期されています。

## 設定内容

### Claude Code の `~/.claude.json` 例（MCPサーバー設定）

```json
{
  "mcpServers": {
    "noveler": {
      "command": ["python", "-u", "dist/mcp_servers/noveler/main.py"],
      "args": [],
      "cwd": "/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド",
      "env": {
        "PYTHONPATH": "/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド:/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/dist",
        "PYTHONUNBUFFERED": "1",
        "NOVEL_PRODUCTION_MODE": "1",
        "MCP_LIGHTWEIGHT_DEFAULT": "1"
      },
      "description": "小説執筆支援"
    }
  }
}
```

トラブルシュート（接続できないとき）:
1. `dist/mcp_servers/noveler/main.py` が存在するか。無い場合は `python scripts/ci/ensure_dist_wrapper.py` を実行して生成。
2. `cwd` と `PYTHONPATH` が実際のリポジトリパスに合っているか確認。
3. ログに `Connection closed` や `can't open .../dist/.../main.py` がある場合は `/mcp restart noveler` を実行し、必要に応じて設定を再保存。

---
allowed-tools: [
  "mcp__noveler__run_quality_checks",
  "mcp__noveler__fix_quality_issues",
  "mcp__noveler__export_quality_report",
  "mcp__noveler__improve_quality_until",
  "mcp__noveler__get_issue_context",
  "mcp__noveler__check_rhythm",
  "mcp__noveler__check_readability",
  "mcp__noveler__check_grammar",
  "mcp__noveler__check_style",
  "mcp__noveler__list_quality_presets",
  "mcp__noveler__get_quality_schema",
  "mcp__noveler__test_result_analysis",
  "mcp__noveler__backup_management",
  "mcp__noveler__design_conversations",
  "mcp__noveler__track_emotions",
  "mcp__noveler__design_scenes",
  "mcp__noveler__design_senses",
  "mcp__noveler__manage_props",
  "mcp__noveler__export_design_data",
  "mcp__noveler__write_step_1",
  "mcp__noveler__write_step_2",
  "mcp__noveler__write_step_3",
  "mcp__noveler__write_step_4",
  "mcp__noveler__write_step_5",
  "mcp__noveler__write_step_6",
  "mcp__noveler__write_step_7",
  "mcp__noveler__write_step_8",
  "mcp__noveler__write_step_9",
  "mcp__noveler__write_step_10"
]
# 既存MCP個別ステップは TenStage (1-10) API。Schema v2 の19ステップ版は
# `noveler_write` で逐次実行される設計で、個別公開は今後の拡張対象です。
argument-hint: "<command> [options]"
description: "小説執筆支援（A38統合18ステップ対応）"
model: "claude-sonnet-4-20250514"
---

小説執筆支援グローバルコマンドを実行します：

## 使用可能コマンド

### 📝 執筆コマンド
- `write <話数> [options]` - エピソード執筆（DDD準拠MCPアダプター経由・A38統合18ステップ対応）
  - 例: `/noveler write 1 --dry-run` (第1話をドライランで執筆)
  - 例: `/noveler write 3` (第3話を実際に執筆)
  - **アーキテクチャ**: DDD準拠MCPアダプター経由で実行（責任分離・テスタビリティ向上）
  - **95%トークン削減**: 既存の最適化システム維持
  - オプション:
    - `--dry-run`: テスト実行（実際のファイル生成なし）
    - `--five-stage`: A30準拠5段階執筆（推奨）

### 🔍 品質チェック
- `check <話数> [--auto-fix]` - 品質チェック
  - 例: `/noveler check 1` (第1話の品質チェック)
  - 例: `/noveler check 5 --auto-fix` (第5話の品質チェック + 自動修正)

### 📊 プロジェクト管理
- `status` - プロジェクト状況確認
  - 執筆済み話数、品質状況、進捗を表示

### 📖 プロット生成
- `plot <話数>` - プロット生成
  - 例: `/noveler plot 7` (第7話のプロット生成)

### 🚀 プロジェクト初期化
- `init <project-name>` - 新規プロジェクト初期化
  - 例: `/noveler init my-novel` (新規プロジェクト作成)

## 🚀 クイックスタート

```bash
/noveler init my-novel          # 新規プロジェクト作成
/noveler write 1 --fresh-start  # 第1話執筆（STEP0保証・推奨）
/noveler check 1                # 第1話品質チェック
/noveler status                 # 現在の執筆状況確認
```

## ⚠️ STEP0開始保証システム

**writeコマンド実行時の必須確認事項**：

1. **新規執筆の場合**: 必ず `--fresh-start` オプションを使用
2. **途中再開の場合**: `--from-step=N` で明示的にステップ番号を指定
3. **実行前チェック**: 以下を確認してからwriteコマンドを実行
   - プロットファイルの存在確認
   - 前回セッションの状態確認
   - A38統合18ステップ（STEP0-17）の理解確認

### A38統合18ステップ実行フロー

**STEP0-6: プロット・設計段階**
- STEP0: スコープ定義（必須開始点）
- STEP1: 大骨（章の目的線）
- STEP2: 中骨（段階目標・行動フェーズ）
- STEP3: セクションバランス設計
- STEP4: 小骨（シーン／ビート）
- STEP5: 論理検証
- STEP6: キャラクター一貫性検証

**STEP7-12: 執筆段階**
- STEP7: 会話設計
- STEP8: 感情曲線
- STEP9: 情景設計
- STEP10: 五感描写設計
- STEP11: 小道具・世界観設計
- STEP12: 初稿生成

**STEP13-17: 品質・公開段階**
- STEP13: 文字数最適化
- STEP14: 文体・可読性パス
- STEP15: 必須品質ゲート
- STEP16: DOD & KPI統合品質認定
- STEP17: 公開準備

## 📋 オプション

- `--dry-run`: テスト実行（実際のファイル生成なし）
- `--auto-fix`: 品質チェック時の自動修正有効
- `--verbose`: 詳細ログ出力

## 🔗 システム連携

このコマンドは95%トークン削減を実現するJSON変換MCPサーバーと統合されており、効率的な小説執筆ワークフローを提供します。

### MCPツール実行制御

**writeコマンド実行時のMCPツール呼び出し制御（DDD準拠アーキテクチャ）**：

1. **mcp__noveler__noveler_write** ツールを自動呼び出し（アダプター経由）
2. **episode_number パラメータ**: 指定話数
3. **dry_run パラメータ**: テスト実行フラグ
4. **five_stage パラメータ**: A30準拠5段階ビュー切替（内部では19ステップを逐次実行）
5. **project_root パラメータ**: プロジェクトルートパス（自動検出）

### 19ステップ執筆フロー（Schema v2）

- `noveler_write` は Template Schema v2 ベースで STEP0〜18 を逐次実行します。
- MCP 個別ステップツール（`write_step_1`〜`write_step_10`）は旧TenStage API の再利用であり、19ステップ版は順次公開予定です。
- 個別ステップ制御が必要な場合は `write_stage` や `write_resume` を併用し、最新テンプレートの定義内容（`templates/writing/write_step*.yaml`）を参照してください。

> **LLM利用フラグ**: `config/novel_config.yaml` の `defaults.writing_steps.use_llm` を `true` にすると、`noveler_write` 実行時に各STEPでテンプレート指示が LLM に送信されます。テスト／オフライン時は `false` とし、モック executor を差し込んでください。

### DDD準拠アーキテクチャの恩恵

- **責任分離**: MCPプロトコル関心とビジネスロジックの分離
- **テスタビリティ**: アダプター層による単体テスト容易性向上
- **保守性**: 外部システム変更に対する耐性向上
- **95%トークン削減**: 既存最適化システムの維持

### 実行前自動チェック

Claude Codeがwriteコマンドを実行する前に以下を自動確認：
- プロジェクトルートの有効性
- 必要ファイルの存在確認
- MCPアダプター層の正常動作確認
- DI（依存性注入）コンテナの準備完了状態

これにより、**DDD準拠の安定した実行環境**が保証されます。
