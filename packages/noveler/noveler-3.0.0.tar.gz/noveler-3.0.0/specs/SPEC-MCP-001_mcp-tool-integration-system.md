---
spec_id: SPEC-MCP-001
status: canonical
owner: bamboocity
last_reviewed: 2025-09-18
category: MCP
sources: [REQ]
tags: [mcp]
requirements:
  - REQ-WRITE-MCP-003
  - REQ-WRITE-TEN-004
  - REQ-QUALITY-STAGED-004
  - REQ-DATA-001
  - REQ-DATA-002
  - REQ-DATA-003
  - REQ-OPS-WRITE-001
---
# SPEC-MCP-001: MCPツール統合システム仕様書

## 要件トレーサビリティ

| 要件ID | 説明 | 本仕様書の対応セクション |
| --- | --- | --- |
| REQ-WRITE-MCP-003 | MCP経由で段階的執筆タスクと復旧を制御する | §2, §3 |
| REQ-WRITE-TEN-004 | 10段階MCPツールで段階執筆を提供する | §3.2, §3.3 |
| REQ-QUALITY-STAGED-004 | 段階的品質チェックフローをMCPで提供する | §4 |
| REQ-DATA-001 | CLI/MCP結果をファイル参照付きJSONとして保存する | §5 |
| REQ-DATA-002 | SHA256ベースのファイル参照と変更検知を提供する | §5 |
| REQ-DATA-003 | アーティファクト保管とバックアップ復元を行う | §5 |
| REQ-OPS-WRITE-001 | MCPクライアントから安全にファイルを書き込む | §6 |

**テストカバレッジ**: `tests/integration/mcp/test_mcp_server_integration.py`, `tests/integration/mcp/test_mcp_server_compliance.py`
**関連仕様書**: `SPEC-MCP-002_mcp-tools-specification.md`、`SPEC-WRITE-018_integrated_writing_flow.md`

---

## 1. 概要

### 1.1 目的
小説執筆支援システム「Noveler」のMCPサーバー機能を包括的に定義し、Claude Code統合による高効率な執筆ワークフローを提供する。

### 1.2 システム特徴
- **マイクロサービス型アーキテクチャ**: 17個の専用MCPツール
- **95%トークン削減**: JSON変換による高効率データ処理
- **10段階執筆システム**: タイムアウト回避の段階別実行
- **Claude Code完全統合**: 外部API不要の内部実行
- **自律実行機能**: LLMが文脈に応じて最適なツールを自動選択

### 1.3 問題の背景
現在のMCPサーバーの課題：
- LLMがツールを選択する際の精度が低い
- 修正→再チェックのサイクルが非効率（全チェックを再実行）
- パラメータスキーマが汎用的で型安全性に欠ける

### 1.4 解決方針
各チェック項目・修正機能を独立したMCPツールとして提供し：
- チェック→修正→再チェックの効率化
- LLMの適切なツール選択支援
- 並列実行による高速化

## 2. システムアーキテクチャ

### 2.1 全体アーキテクチャ
```
ユーザー入力 (/noveler write 1)
    ↓
Claude Code (グローバル noveler.md 読み込み)
    ↓
MCP Server (mcp__noveler__noveler_write)
    ↓
マイクロサービス型ツール群 (write_stage, check_basic, check_a31等)
    ↓
JSON変換・95%トークン削減
    ↓
フォーマット済み結果表示
```

### 2.2 設計原則

#### 2.2.1 コア原則
1. **単一責任原則**: 1ツール1機能
2. **独立性**: 各ツールが独立して実行可能
3. **再実行可能性**: 個別チェックの繰り返し実行に最適化
4. **段階的修正**: チェック→修正→再チェックのサイクル対応

#### 2.2.2 命名規則
- 主要ツール名は `noveler_write`, `noveler_check` など `noveler_` 接頭辞で統一
- サブ機能は`_`で接続（`check_basic`, `write_stage`等）
- 修正系は`check_fix`として統合

## 3. 17個のMCPツール詳細仕様

### 3.1 執筆関連ツール（10段階対応）

| ツール名 | 機能 | 主な用途 | 要件対応 |
|---------|------|---------|----------|
| `noveler_write` | 小説エピソード執筆（全10段階） | A30準拠10段階システムで高品質な原稿を生成 | REQ-MCP-002 |
| `write_stage` | 特定ステージのみ執筆実行 | plot_data_preparation等の個別実行・再開可能 | REQ-MCP-002 |
| `write_resume` | 中断位置から執筆再開 | セッションIDを指定して前回の続きから実行 | REQ-MCP-028 |
| `write_with_claude` | Claude Code内原稿生成 | 外部API不要でClaude Code内で直接原稿生成 | REQ-MCP-030 |

#### 10段階個別実行ツール（タイムアウト完全回避）

| ツール名 | 機能 | 主な用途 |
|---------|------|---------|
| `write_step_1` | STEP1: プロットデータ準備 | 独立5分タイムアウトで実行、セッションID生成 |
| `write_step_2` | STEP2: プロット分析設計 | 前段階のセッションIDを受け取り継続実行 |
| `write_step_3` | STEP3: 感情関係性設計 | 独立タイムアウトでキャラクター感情設計 |
| `write_step_4` | STEP4: ユーモア魅力設計 | 独立タイムアウトで魅力要素追加 |
| `write_step_5` | STEP5: キャラ心理対話設計 | 独立タイムアウトで対話品質向上 |
| `write_step_6` | STEP6: 場面演出雰囲気設計 | 独立タイムアウトで演出強化 |
| `write_step_7` | STEP7: 論理整合性調整 | 独立タイムアウトで矛盾解消 |
| `write_step_8` | STEP8: 原稿執筆 | 独立タイムアウトで初原稿生成 |
| `write_step_9` | STEP9: 品質仕上げ | 独立タイムアウトで品質改善 |
| `write_step_10` | STEP10: 最終調整 | 独立タイムアウトで最終仕上げ |

#### 10段階構成詳細
1. **PlotDataPreparationStage**: プロット・データ準備（2ターン想定）
2. **PlotAnalysisDesignStage**: プロット分析・設計（2ターン想定）
3. **EmotionalRelationshipDesignStage**: 感情・関係性設計（2ターン想定）
4. **HumorCharmDesignStage**: ユーモア・魅力設計（2ターン想定）
5. **CharacterPsychologyDialogueDesignStage**: キャラ心理・対話設計（2ターン想定）
6. **SceneDirectionAtmosphereDesignStage**: 場面演出・雰囲気設計（2ターン想定）
7. **LogicConsistencyAdjustmentStage**: 論理整合性調整（2ターン想定）
8. **ManuscriptWritingStage**: 原稿執筆（3ターン想定）
9. **QualityRefinementStage**: 品質仕上げ（2ターン想定）
10. **FinalAdjustmentStage**: 最終調整（1ターン想定）

### 3.2 品質チェック関連ツール（マイクロサービス）

| ツール名 | 機能 | 主な用途 | 要件対応 |
|---------|------|---------|----------|
| `noveler_check` | 完全品質チェック（3段階） | 基本→A31評価（68項目）→Claude AI分析を段階的実行 | REQ-MCP-003 |
| `check_basic` | 基本品質チェックのみ実行 | 文字数、禁止表現、文章構造、誤字脱字等 | REQ-MCP-003 |
| `check_story_elements` | 小説の基本要素評価（68項目） | 感情・キャラ・ストーリー・文章・世界観・読者エンゲージメント | REQ-MCP-003 |
| `check_story_structure` | ストーリー構成評価 | 整合性、起承転結、伏線回収、ペース配分、ジャンル適合性 | REQ-MCP-003 |
| `check_writing_expression` | 文章表現力評価 | 文章の自然さ、描写力、比喩、文体、読みやすさ、商業比較 | REQ-MCP-003 |
| `check_rhythm` | 文章リズム・読みやすさ分析 | 文長バリエーション、読点配置、漢字バランス等 | REQ-MCP-003 |
| `check_fix` | 問題箇所の自動修正実行 | 検出された問題を自動修正（safe/standard/aggressive） | REQ-MCP-003 |

#### A31評価68項目の詳細内訳

**感情描写（12項目）**
- 感情表現の深さと具体性
- 読者の共感を呼ぶ感情描写
- 感情変化の自然さと論理性
- 内面描写と行動の一致

**キャラクター（12項目）**
- 性格の一貫性と魅力
- キャラクター成長の描写
- 関係性の変化と深まり
- 個性的な話し方・行動パターン

**ストーリー展開（12項目）**
- 起承転結の構成力
- テンポとペーシング
- 伏線の配置と回収
- 意外性と必然性のバランス

**文章表現（12項目）**
- 描写力と臨場感
- 比喩・修辞技法の効果的使用
- 文章リズムと読みやすさ
- 語彙の豊富さと適切性

**世界観・設定（10項目）**
- 設定の一貫性と論理性
- 世界観の深さと魅力
- リアリティと説得力
- 独自性とオリジナリティ

**読者エンゲージメント（10項目）**
- 冒頭の引き込み力
- 続きが気になる構成
- 読後の満足感
- ターゲット読者への訴求力

### 3.3 プロット関連ツール

| ツール名 | 機能 | 主な用途 | 要件対応 |
|---------|------|---------|----------|
| `noveler_plot` | プロット生成 | A28プロンプト準拠のプロット生成（`regenerate=true`で再生成） | REQ-MCP-004 |

> 旧 `plot_generate` / `plot_validate` ツールは 2025-09-18 に廃止されました。プロット品質の検証は `check_story_structure` や `check_story_elements` を組み合わせて実施します。

### 3.4 プロジェクト管理ツール

| ツール名 | 機能 | 主な用途 | 要件対応 |
|---------|------|---------|----------|
| `status` | プロジェクト状況確認 | 執筆済み話数、品質スコア、進捗状況を表示 | REQ-MCP-005 |
| `noveler_complete` | 完了処理・公開準備 | 原稿最終化、成果物パッケージ化、メタデータ更新 | REQ-MCP-005 |

> `init` ツールは 2025-09-18 に廃止されました。新規プロジェクト作成はテンプレートのコピー、または `noveler` CLI (`project create` など) を利用してください。

### 3.5 参照（Artifact）ツール（追加）

| ツール名 | 機能 | 主な用途 | 要件対応 |
|---------|------|---------|----------|
| `fetch_artifact` | 参照IDから内容を取得 | 大きな入力を参照渡しで取得（プロンプト効率化） | REQ-MCP-004 |
| `list_artifacts` | 参照一覧を取得 | 利用可能な参照の把握・デバッグ | REQ-MCP-004 |

スキーマ（概要）:

```json
{
  "name": "fetch_artifact",
  "inputSchema": {
    "type": "object",
    "properties": {
      "artifact_id": {"type": "string"},
      "section": {"type": "string"},
      "project_root": {"type": "string"},
      "format": {"type": "string", "enum": ["raw", "json"], "default": "raw"}
    },
    "required": ["artifact_id"]
  }
}
```

### 3.6 エンハンスト執筆ユースケースツール（新規・診断/復旧対応）

EnhancedWritingUseCase を用いた、診断付きタスクリスト取得・非同期ステップ実行・部分失敗からの復旧を行う補助ツール群。従来の ProgressiveWriteManager ベースのツールを置き換えるものではなく、エラーハンドリング強化版として併存する。

| ツール名 | 機能 | 主な用途 | 要件対応 |
|---------|------|---------|----------|
| `enhanced_get_writing_tasks` | 診断付きタスクリスト取得 | LLM提示用のタスク＋進捗＋診断情報の取得 | REQ-MCP-027,029 |
| `enhanced_execute_writing_step` | 非同期・復旧対応ステップ実行 | 品質に応じた継続/中断判断、復旧の自動適用 | REQ-MCP-027,028 |
| `enhanced_resume_from_partial_failure` | 部分失敗からの復旧実行 | 復旧ポイントからの再実行・結果集計 | REQ-MCP-028 |

スキーマ（概要）:

```json
{
  "name": "enhanced_get_writing_tasks",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode_number": {"type": "integer", "minimum": 1},
      "project_root": {"type": "string"}
    },
    "required": ["episode_number"]
  }
}
```

```json
{
  "name": "enhanced_execute_writing_step",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode_number": {"type": "integer", "minimum": 1},
      "step_id": {"type": "number"},
      "dry_run": {"type": "boolean", "default": false},
      "project_root": {"type": "string"}
    },
    "required": ["episode_number", "step_id"]
  }
}
```

```json
{
  "name": "enhanced_resume_from_partial_failure",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode_number": {"type": "integer", "minimum": 1},
      "recovery_point": {"type": "integer", "minimum": 0},
      "project_root": {"type": "string"}
    },
    "required": ["episode_number", "recovery_point"]
  }
}
```

受け入れ基準:
- それぞれのツールが異常時に構造化エラーを返し、`execution_method: enhanced_use_case` を含む
- `enhanced_execute_writing_step` は復旧適用時に `recovery_applied: true` を `result` 内に含める
- `enhanced_resume_from_partial_failure` は `resumed_steps` と結果配列を返す

```json
{
  "name": "list_artifacts",
  "inputSchema": {
    "type": "object",
    "properties": {
      "project_root": {"type": "string"}
    }
  }
}
```

## 4. 自律実行機能仕様

### 4.1 LLM自律実行の概要
現在のスラッシュコマンド `/noveler` で提供している機能を、MCPサーバー経由でLLMが自律的に実行できるよう個別ツールとして実装する。

### 4.2 目標
- LLMが必要に応じてMCPツールを自律実行可能にする
- 既存のNovelSlashCommandHandlerの機能を活用し重複実装を避ける
- Claude Code統合での95%トークン削減効果を維持

### 4.4 I/Oロギング方針（更新）
- write系の逐次I/Oは `.noveler/writes/` に保存
- quality/check系の逐次I/Oは `.noveler/checks/` に保存
- 目的: プロンプト改善のための時系列ログ蓄積

### 4.5 テスト用サンプルプロジェクトの既定（更新）
- `project_root` が未指定の場合の既定解決:
  1. `PROJECT_ROOT` または `NOVELER_TEST_PROJECT_ROOT` 環境変数が設定されていればそれを採用
  2. 設定が無ければ、GUIDE_ROOT（本リポジトリ: `00_ガイド/`）の親ディレクトリに存在する最新サンプル
     `../10_Fランク魔法使いはDEBUGログを読む/` を既定プロジェクトとして採用
  3. それも無い場合は `cwd` を採用
- 任意で `NOVELER_SAMPLES_ROOT` にサンプルルートを設定可能

### 4.3 個別ツール定義

#### 4.3.1 noveler_write
- **目的**: 指定話数のエピソード執筆
- **パラメータ**:
  - `episode_number` (int, required): 執筆する話数
  - `dry_run` (bool, optional): テスト実行モード（デフォルト: false）
  - `five_stage` (bool, optional): A30準拠5段階執筆モード（デフォルト: true）
  - `project_root` (str, optional): プロジェクトルートパス

#### 4.3.2 noveler_check
- **目的**: 指定話数の品質チェック
- **パラメータ**:
  - `episode_number` (int, required): チェック対象話数
  - `auto_fix` (bool, optional): 自動修正実行（デフォルト: false）
  - `verbose` (bool, optional): 詳細ログ出力（デフォルト: false）
  - `project_root` (str, optional): プロジェクトルートパス

#### 4.3.3 noveler_plot
- **目的**: 指定話数のプロット生成
- **パラメータ**:
  - `episode_number` (int, required): プロット生成対象話数
  - `regenerate` (bool, optional): 既存プロット再生成（デフォルト: false）
  - `project_root` (str, optional): プロジェクトルートパス

#### 4.3.4 noveler_complete
- **目的**: 指定話数の完成処理
- **パラメータ**:
  - `episode_number` (int, required): 完成処理対象話数
  - `auto_publish` (bool, optional): 自動投稿準備（デフォルト: false）
  - `project_root` (str, optional): プロジェクトルートパス

#### 4.3.5 status
- **目的**: プロジェクト状況確認（既存改良）
- **パラメータ**:
  - `project_root` (str, optional): プロジェクトルートパス

## 5. ツール仕様詳細

### 5.1 共通パラメータ（v2.4.0統一）
```json
{
  "episode": {
    "type": "integer",
    "description": "対象エピソード番号",
    "required": true,
    "note": "v2.4.0で全ツール統一（旧episode_number廃止）"
  },
  "project_root": {
    "type": "string",
    "description": "プロジェクトルートパス（省略時は現在のディレクトリ）",
    "required": false
  },
  "session_id": {
    "type": "string",
    "description": "10段階執筆システムのセッション識別子",
    "required": false,
    "note": "write_stage、write_resume、write_manuscript_draftで利用"
  },
  "stage": {
    "type": "string",
    "description": "10段階システムの特定段階名",
    "enum": [
      "plot_data_preparation",
      "analyze_plot_structure",
      "design_emotional_flow",
      "design_humor_elements",
      "design_character_dialogue",
      "design_scene_atmosphere",
      "adjust_logic_consistency",
      "write_manuscript_draft",
      "refine_manuscript_quality",
      "finalize_manuscript"
    ],
    "required": false,
    "note": "write_stageツール専用パラメータ"
  }
}
```

### 5.2 共通レスポンス形式
```json
{
  "success": "boolean",
  "command": "string",
  "output": "string",
  "stderr": "string",
  "execution_time_seconds": "number",
  "project_root": "string"
}
```

### 5.3 個別ツール仕様例

#### write_with_claude
```json
{
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode": {
        "type": "integer",
        "description": "エピソード番号"
      },
      "plot_content": {
        "type": "string",
        "description": "プロット内容（省略時は既存プロットから読み込み）"
      },
      "word_count_target": {
        "type": "integer",
        "default": 4000,
        "description": "目標文字数"
      },
      "project_root": {
        "type": "string",
        "description": "プロジェクトルートパス"
      }
    },
    "required": ["episode"]
  }
}
```

#### write_step_1〜10 共通仕様
```json
{
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode": {
        "type": "integer",
        "description": "エピソード番号"
      },
      "session_id": {
        "type": "string",
        "description": "前段階のセッションID（STEP2以降で必須）",
        "required": false
      },
      "project_root": {
        "type": "string",
        "description": "プロジェクトルートパス"
      }
    },
    "required": ["episode"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": "boolean",
      "step": "integer",
      "session_id": "string",
      "next_step": "integer",
      "result": "object",
      "execution_time_seconds": "number",
      "timeout_reset": "boolean"
    }
  }
}
```

#### check_story_elements
```json
{
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode": {"type": "integer"},
      "auto_fix": {
        "type": "boolean",
        "default": false,
        "description": "自動修正を有効化"
      },
      "fix_level": {
        "type": "string",
        "enum": ["safe", "standard", "aggressive"],
        "default": "safe",
        "description": "修正の積極性レベル"
      }
    },
    "required": ["episode"]
  }
}
```

### 5.4 完全17ツール個別詳細仕様

#### 5.4.1 執筆系ツール（5個）

##### mcp__noveler__noveler_write
```json
{
  "description": "10段階構造化執筆システム完全実行",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode": {
        "type": "integer",
        "description": "執筆対象のエピソード番号",
        "minimum": 1
      },
      "dry_run": {
        "type": "boolean",
        "default": false,
        "description": "テスト実行（実際のファイル変更なし）"
      },
      "project_root": {
        "type": "string",
        "description": "プロジェクトルートパス（省略時は現在のディレクトリから推測）"
      }
    },
    "required": ["episode"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": "boolean",
      "total_stages_completed": "integer",
      "final_manuscript_path": "string",
      "word_count": "integer",
      "quality_score": "number",
      "stage_results": {
        "type": "array",
        "items": {
          "stage": "integer",
          "status": "string",
          "execution_time_seconds": "number",
          "output_summary": "string"
        }
      },
      "execution_time_total_seconds": "number"
    }
  },
  "timeout": "600秒（10分）",
  "errorCodes": {
    "E001": "プロットファイルが存在しない",
    "E002": "10段階実行中にタイムアウト",
    "E003": "品質基準未達で実行停止"
  }
}
```

##### mcp__noveler__write_stage
```json
{
  "description": "10段階システムの特定段階のみを個別実行",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode": {"type": "integer", "minimum": 1},
      "stage": {
        "type": "string",
        "enum": [
          "plot_data_preparation", "plot_structure_analysis", "emotional_flow_design",
          "humor_elements_design", "character_dialogue_design", "scene_atmosphere_design",
          "logic_consistency_adjust", "manuscript_draft_generate", "quality_refinement", "final_adjustment"
        ],
        "description": "実行する段階名"
      },
      "session_id": {
        "type": "string",
        "description": "前段階からの継続セッションID"
      },
      "resume_session": {
        "type": "string",
        "description": "中断したセッションから再開するID"
      },
      "project_root": {"type": "string"}
    },
    "required": ["episode", "stage"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": "boolean",
      "stage": "string",
      "session_id": "string",
      "next_recommended_stage": "string",
      "stage_result": "object",
      "execution_time_seconds": "number"
    }
  },
  "timeout": "60秒（段階別）"
}
```

##### mcp__noveler__write_resume
```json
{
  "description": "中断した執筆セッションから再開",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode": {"type": "integer"},
      "session_id": {
        "type": "string",
        "description": "再開するセッションのID"
      },
      "project_root": {"type": "string"}
    },
    "required": ["episode", "session_id"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": "boolean",
      "resumed_from_stage": "integer",
      "remaining_stages": "array",
      "execution_result": "object"
    }
  }
}
```

##### mcp__noveler__write_manuscript_draft
```json
{
  "description": "段階8原稿執筆を単独で実行",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode": {"type": "integer"},
      "session_id": {"type": "string"},
      "word_count_target": {
        "type": "integer",
        "default": 4000,
        "minimum": 1000,
        "maximum": 20000
      },
      "project_root": {"type": "string"}
    },
    "required": ["episode"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": "boolean",
      "manuscript_text": "string",
      "word_count_actual": "integer",
      "quality_assessment": {
        "overall_score": "number",
        "detailed_scores": "object"
      }
    }
  }
}
```

##### mcp__noveler__write_with_claude
```json
{
  "description": "Claude Code内で完結する原稿生成（外部API不要）",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode": {"type": "integer"},
      "plot_content": {
        "type": "string",
        "description": "プロット内容（省略時は既存から読み込み）"
      },
      "word_count_target": {
        "type": "integer",
        "default": 4000
      },
      "project_root": {"type": "string"}
    },
    "required": ["episode"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": "boolean",
      "manuscript_generated": "string",
      "word_count": "integer",
      "generation_method": "string"
    }
  }
}
```

#### 5.4.2 品質チェック系ツール（7個）

##### mcp__noveler__noveler_check
```json
{
  "description": "完全品質チェック（3段階：基本→A31→Claude分析）",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode": {"type": "integer"},
      "auto_fix": {
        "type": "boolean",
        "default": false,
        "description": "自動修正を実行するか"
      },
      "project_root": {"type": "string"}
    },
    "required": ["episode"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": "boolean",
      "check_stages_completed": {
        "type": "array",
        "items": {"type": "string"}
      },
      "overall_quality_score": "number",
      "basic_check_result": "object",
      "a31_evaluation_result": "object",
      "claude_analysis_result": "object",
      "auto_fix_applied": "boolean",
      "fixed_issues_count": "integer"
    }
  }
}
```

##### mcp__noveler__check_basic
```json
{
  "description": "基本品質チェックのみ（文字数・禁止表現・構造）",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode": {"type": "integer"},
      "project_root": {"type": "string"}
    },
    "required": ["episode"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": "boolean",
      "word_count_check": {
        "actual": "integer",
        "target": "integer",
        "deviation_percentage": "number",
        "status": "string"
      },
      "forbidden_expressions": {
        "found_count": "integer",
        "violations": "array"
      },
      "structure_issues": {
        "paragraph_issues": "array",
        "formatting_issues": "array"
      }
    }
  }
}
```

##### mcp__noveler__check_story_elements
```json
{
  "description": "A31評価68項目による小説要素品質チェック",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode": {"type": "integer"},
      "auto_fix": {"type": "boolean", "default": false},
      "fix_level": {
        "type": "string",
        "enum": ["safe", "standard", "aggressive"],
        "default": "safe"
      },
      "project_root": {"type": "string"}
    },
    "required": ["episode"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": "boolean",
      "a31_scores": {
        "emotional_expression": {"score": "number", "max": 12},
        "character_development": {"score": "number", "max": 12},
        "story_structure": {"score": "number", "max": 12},
        "writing_technique": {"score": "number", "max": 12},
        "world_building": {"score": "number", "max": 10},
        "reader_engagement": {"score": "number", "max": 10}
      },
      "overall_score": "number",
      "low_score_items": "array",
      "improvement_suggestions": "array",
      "auto_fix_results": "object"
    }
  }
}
```

##### mcp__noveler__check_story_structure
```json
{
  "description": "ストーリー構成評価（プロレベル物語構成力チェック）",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode": {"type": "integer"},
      "project_root": {"type": "string"}
    },
    "required": ["episode"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": "boolean",
      "structure_analysis": {
        "story_integration": {"score": "number", "issues": "array"},
        "pacing_rhythm": {"score": "number", "issues": "array"},
        "foreshadowing_recovery": {"score": "number", "issues": "array"},
        "character_psychology_consistency": {"score": "number", "issues": "array"},
        "genre_appropriateness": {"score": "number", "issues": "array"}
      },
      "overall_structure_score": "number"
    }
  }
}
```

##### mcp__noveler__check_writing_expression
```json
{
  "description": "文章表現力評価（プロレベル文章力チェック）",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode": {"type": "integer"},
      "project_root": {"type": "string"}
    },
    "required": ["episode"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": "boolean",
      "expression_analysis": {
        "naturalness": {"score": "number", "issues": "array"},
        "descriptive_power": {"score": "number", "issues": "array"},
        "metaphor_rhetoric": {"score": "number", "issues": "array"},
        "style_consistency": {"score": "number", "issues": "array"},
        "readability": {"score": "number", "issues": "array"},
        "professional_comparison": {"score": "number", "benchmark": "string"}
      }
    }
  }
}
```

##### mcp__noveler__check_rhythm
```json
{
  "description": "文章リズム・読みやすさ分析",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode": {"type": "integer"},
      "project_root": {"type": "string"}
    },
    "required": ["episode"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": "boolean",
      "rhythm_analysis": {
        "sentence_length_variation": {
          "short_ratio": "number",
          "medium_ratio": "number",
          "long_ratio": "number",
          "balance_score": "number"
        },
        "punctuation_rhythm": {"score": "number"},
        "ending_pattern_repetition": {"violations": "array"},
        "character_balance": {
          "kanji_ratio": "number",
          "hiragana_ratio": "number",
          "katakana_ratio": "number"
        },
        "paragraph_distribution": {"average_length": "number", "variation_score": "number"}
      }
    }
  }
}
```

##### mcp__noveler__check_fix
```json
{
  "description": "検出された問題の自動修正実行",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode": {"type": "integer"},
      "fix_level": {
        "type": "string",
        "enum": ["safe", "standard", "aggressive"],
        "default": "safe"
      },
      "issue_ids": {
        "type": "array",
        "items": {"type": "string"},
        "description": "修正対象の問題ID一覧（省略時は全適用可能問題を修正）"
      },
      "project_root": {"type": "string"}
    },
    "required": ["episode"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": "boolean",
      "fixes_applied": {
        "type": "array",
        "items": {
          "issue_id": "string",
          "fix_type": "string",
          "before": "string",
          "after": "string",
          "confidence": "number"
        }
      },
      "fixes_skipped": "array",
      "quality_improvement": {
        "before_score": "number",
        "after_score": "number",
        "improvement": "number"
      }
    }
  }
}
```

#### 5.4.3 プロット系ツール（2個）

##### mcp__noveler__noveler_plot
```json
{
  "description": "A28プロンプト準拠プロット生成",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode": {"type": "integer"},
      "project_root": {"type": "string"}
    },
    "required": ["episode"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": "boolean",
      "plot_generated": "string",
      "plot_file_path": "string",
      "generation_method": "string",
      "plot_quality_preview": {
        "estimated_length": "integer",
        "complexity_score": "number",
        "key_elements": "array"
      }
    }
  }
}
```

##### mcp__noveler__plot_validate
```json
{
  "description": "A29基準でプロット品質検証",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode": {"type": "integer"},
      "project_root": {"type": "string"}
    },
    "required": ["episode"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": "boolean",
      "validation_result": {
        "overall_quality": "number",
        "plot_completeness": {"score": "number", "missing_elements": "array"},
        "character_development": {"score": "number", "issues": "array"},
        "story_logic": {"score": "number", "inconsistencies": "array"},
        "emotional_arc": {"score": "number", "weak_points": "array"}
      },
      "improvement_suggestions": "array"
    }
  }
}
```

#### 5.4.4 プロジェクト管理系ツール（3個）

##### mcp__noveler__status
```json
{
  "description": "プロジェクト状況確認（執筆済み話数・品質スコア・進捗）",
  "inputSchema": {
    "type": "object",
    "properties": {
      "project_root": {"type": "string"}
    }
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": "boolean",
      "project_overview": {
        "project_name": "string",
        "total_episodes": "integer",
        "completed_episodes": "integer",
        "draft_episodes": "integer"
      },
      "quality_summary": {
        "average_quality_score": "number",
        "highest_score": "number",
        "lowest_score": "number",
        "episodes_below_threshold": "array"
      },
      "progress_analysis": {
        "completion_rate": "number",
        "estimated_remaining_work": "string",
        "recent_activity": "array"
      }
    }
  }
}
```

> **廃止済み**: `mcp__noveler__init` は提供を終了しました。初期化は `noveler` CLI (`project create` など)、またはテンプレートのコピーで実施してください。

##### mcp__noveler__noveler_complete
```json
{
  "description": "完了処理・公開準備メタ生成",
  "inputSchema": {
    "type": "object",
    "properties": {
      "episode": {"type": "integer"},
      "auto_publish": {"type": "boolean", "default": false},
      "project_root": {"type": "string"}
    },
    "required": ["episode"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": "boolean",
      "artifacts": "array",
      "publication_status": "string",
      "next_actions": "array"
    }
  }
}
```

### 5.5 エラーレスポンス統一仕様（v2.4.0 完全適用）
**実装状況**: ✅ 全17個ツールで統一エラーハンドリング適用完了

```json
{
  "error_response_format": {
    "success": false,
    "error": {
      "type": "string",
      "code": "string",
      "message": "string",
      "details": "object",
      "tool_name": "string",
      "claude_guidance": {
        "suggested_action": "string",
        "parameters": "object",
        "explanation": "string"
      },
      "alternative_actions": "array",
      "troubleshooting_url": "string"
    }
  }
}
```

**v2.4.0 改善点**:
- `tool_name`フィールド追加（エラー発生ツールの特定）
- 重複メソッド問題解決（`_format_error_result`統一）
- 全ツールで`handle_mcp_error`統一適用

### 5.6 共通エラーコード定義
```yaml
common_error_codes:
  # プロジェクト関連
  P001: "プロジェクトディレクトリが見つからない"
  P002: "設定ファイルが破損している"
  P003: "権限不足でファイル操作が失敗"

  # エピソード関連
  E001: "指定エピソード番号が存在しない"
  E002: "プロットファイルが存在しない"
  E003: "原稿ファイルが見つからない"

  # 実行関連
  R001: "実行タイムアウト"
  R002: "メモリ不足"
  R003: "外部API接続エラー"

  # 品質関連
  Q001: "品質基準未達で処理停止"
  Q002: "A31チェック実行失敗"
  Q003: "自動修正適用失敗"
```

## 6. Claude Code統合インターフェース（REQ-MCP-016〜018）

### 6.1 95%トークン削減JSON変換システム
- **REQ-MCP-016**: JSON変換MCPツール
  ```json
  {
    "name": "mcp__noveler__convert_cli_to_json",
    "description": "CLI実行結果をJSON形式に変換し95%トークン削減とファイル参照アーキテクチャを適用",
    "parameters": {
      "cli_result": "object (required) - 任意のCLI実行結果オブジェクト"
    }
  },
  {
    "name": "mcp__noveler__validate_json_response",
    "description": "JSON レスポンス形式検証",
    "parameters": {
      "json_data": "object (required)"
    }
  },
  {
    "name": "mcp__noveler__get_file_reference_info",
    "description": "ファイル参照情報取得",
    "parameters": {
      "file_path": "string (required)"
    }
  }
  ```

### 6.2 Claude Code対話フロー設計
- **REQ-MCP-017**: 対話型実行フロー
  ```mermaid
  sequenceDiagram
      participant User as 👤 ユーザー
      participant CC as 🔧 Claude Code
      participant MCP as 🔗 MCPサーバー
      participant Noveler as 📝 Novelerシステム

      User->>CC: "第1話を執筆して"
      CC->>MCP: mcp__noveler__noveler_write(episode=1)
      MCP->>Noveler: 10段階執筆プロセス開始

      loop 各段階（STEP1-10）
          Noveler->>MCP: 段階結果（JSON形式、95%削減済み）
          MCP->>CC: ファイル参照付き結果
          CC->>User: 段階成果物提示

          alt ユーザー確認・修正要求
              User->>CC: "もう少し感情描写を強化して"
              CC->>MCP: mcp__noveler__write_stage(episode=1, stage="design_emotional_flow")
          else 次段階継続
              CC->>MCP: 次段階実行指示
          end
      end

      MCP->>CC: 完成原稿 + 品質レポート
      CC->>User: 完成報告 + 品質スコア表示
  ```

### 6.3 エラーハンドリング・ガイダンス統合
- **REQ-MCP-018**: Claude Code統合エラー処理
  - **エラー応答フォーマット**:
    ```json
    {
      "success": false,
      "error": {
        "type": "EpisodeNotFound",
        "code": "D001",
        "message": "エピソード5のプロットが見つかりません",
        "claude_guidance": {
          "suggested_action": "mcp__noveler__noveler_plot",
          "parameters": {"episode": 5},
          "explanation": "まずプロットを生成してから執筆を開始することをお勧めします"
        },
        "alternative_actions": [
          {
            "action": "mcp__noveler__write_with_claude",
            "description": "プロット無しで直接執筆を開始（上級者向け）"
          }
        ]
      }
    }
    ```

## 7. パフォーマンス・可用性要件（REQ-MCP-026〜030）

### 7.1 レスポンス時間要件
- **REQ-MCP-026**: MCPツール性能要件
  - **ツール別応答時間目標**:
    ```yaml
    tool_performance_targets:
      mcp__noveler__status: "< 2秒"
      mcp__noveler__noveler_plot: "< 30秒"
      mcp__noveler__write_stage: "< 45秒"
      mcp__noveler__write: "< 400秒 (10段階合計)"
      mcp__noveler__check_basic: "< 10秒"
      mcp__noveler__noveler_check: "< 60秒"
    ```

### 7.2 並行実行・リソース管理
- **REQ-MCP-027**: 並列処理制御
  - **MCPサーバー並行実行制限**:
    ```python
    # 同時実行数制御
    MAX_CONCURRENT_WRITE_OPERATIONS = 1  # 執筆は排他制御
    MAX_CONCURRENT_CHECK_OPERATIONS = 3  # チェックは並列実行可
    MAX_CONCURRENT_PLOT_OPERATIONS = 2   # プロット生成は中程度の並行性

    # メモリ制限
    MEMORY_LIMIT_PER_OPERATION = "500MB"
    TOTAL_MEMORY_LIMIT = "2GB"
    ```

### 7.3 セッション・状態管理
- **REQ-MCP-028**: 状態永続化
  - **セッション状態ファイル構造**:
    ```yaml
    # .noveler/sessions/session_20250904_103000.yaml
    session_id: "session_20250904_103000"
    created_at: "2025-09-04T10:30:00Z"
    last_updated: "2025-09-04T10:35:30Z"

    episode: 1
    current_stage: "design_emotional_flow"
    total_stages: 10
    completed_stages: ["plot_data_preparation", "analyze_plot_structure"]

    stage_outputs:
      plot_data_preparation:
        output_file: "episodes/episode_001_stage1.json"
        execution_time: 25.5
        quality_score: 8.1
      analyze_plot_structure:
        output_file: "episodes/episode_001_stage2.json"
        execution_time: 28.2
        quality_score: 8.3

    user_feedback:
      - stage: "plot_data_preparation"
        feedback: "approved"
        timestamp: "2025-09-04T10:32:15Z"
    ```

### 7.4 トラブルシューティング・デバッグ
- **REQ-MCP-029**: デバッグ支援機能
  - **詳細ログ出力**:
    ```python
    # MCPツール実行ログ形式
    {
      "timestamp": "2025-09-04T10:30:00.123Z",
      "tool_name": "mcp__noveler__noveler_write",
      "parameters": {"episode": 1, "dry_run": false},
      "execution_trace": [
        {"stage": "plot_data_preparation", "start": "10:30:00", "end": "10:30:25", "status": "completed"},
        {"stage": "analyze_plot_structure", "start": "10:30:25", "end": "10:30:53", "status": "completed"},
        {"stage": "design_emotional_flow", "start": "10:30:53", "end": "10:31:18", "status": "error",
         "error": "FileNotFoundError: character_relationships.yaml"}
      ],
      "resource_usage": {
        "peak_memory": "285MB",
        "cpu_time": "45.2s",
        "file_operations": 156
      }
    }
    ```

### 7.5 Claude Code最適化統合
- **REQ-MCP-030**: Claude Code特化最適化
  - **トークン効率化機能**:
    ```python
    # Claude Code向け最適化応答
    def optimize_for_claude_code(result: dict) -> dict:
        return {
            "success": True,
            "summary": "第1話執筆完了（4,200字、品質スコア8.5/10）",
            "primary_output": {
                "file_reference": "episodes/episode_001.md",
                "preview": "第一章　魔法学院への入学\\n\\n朝の光が石造りの校舎に差し込む中、エリア・ヴァルディスは...",
                "word_count": 4200,
                "quality_metrics": {
                    "overall_score": 8.5,
                    "top_strengths": ["キャラクター描写", "場面設定"],
                    "improvement_areas": ["アクション描写"]
                }
            },
            "detailed_report_reference": "quality_reports/episode_001_detailed.json",
            "next_suggested_actions": [
                "mcp__noveler__noveler_check(episode=1) で品質最終チェック",
                "mcp__noveler__noveler_plot(episode=2) で次話プロット作成"
            ]
        }
    ```

## 8. 技術実装要件

### 8.1 実装場所
- **メインファイル**: `src/mcp_servers/noveler/json_conversion_server.py`
- **実装方法**: `JSONConversionServer._register_novel_tools` メソッドの拡張

### 8.2 アーキテクチャ設計

```python
class JSONConversionServer:
    def _register_novel_tools(self) -> None:
        # 既存の統合ツール（下位互換維持）
        self._register_unified_novel_tool()

        # 新規個別ツール（LLM自律実行用）
        self._register_individual_novel_tools()

    def _register_individual_novel_tools(self) -> None:
        # 各ツールを個別に登録
        self._register_noveler_write()
        self._register_noveler_check()
        # ...
```

### 8.3 依存関係
- **NovelSlashCommandHandler**: 既存のコマンド処理ロジックを再利用
- **PathService**: パス管理統一（B20準拠）
- **Logger**: 統一ロギング（B20準拠）

### 8.4 技術要件
- Python 3.11以上
- MCP Server Framework準拠
- JSON変換による95%トークン削減の活用
- 既存のnovelerツールとの並存（後方互換性）
- Claude Code内部実行による外部API依存の排除

### 8.5 品質要件
- テストカバレッジ80%以上
- 各ツールの独立テストが可能
- エラーハンドリングの完備
- 適切なログ出力

### 8.6 性能要件
- 個別チェックの実行時間: 平均2秒以下
- 並列実行時のメモリ効率性
- 大量エピソードでの安定動作

## 9. 使用シナリオ

### 9.1 基本的な修正サイクル
```python
# 1. 完全品質チェック実行
result = mcp__noveler__noveler_check(episode=3)
# → 基本・A31・Claude分析で問題発見

# 2. 小説要素評価で低スコア項目を自動修正
mcp__noveler__check_fix(episode=3, fix_level="standard")

# 3. 小説要素のみ再チェックして改善確認
mcp__noveler__check_story_elements(episode=3)
```

### 9.2 段階的執筆と品質確認
```python
# 1. 特定ステージまで執筆
mcp__noveler__write_stage(episode=3, stage="episode_design")

# 2. 途中で基本チェック
mcp__noveler__check_basic(episode=3)

# 3. 問題があれば修正後、続きから再開
mcp__noveler__write_resume(episode=3, session_id="xxx")
```

### 9.3 Claude Code内部原稿生成（外部API不要）
```python
# 1. 既存プロットから原稿生成
mcp__noveler__write_with_claude(episode=3)

# 2. プロット内容を指定して原稿生成
mcp__noveler__write_with_claude(
    episode=3,
    plot_content="第3話のプロット内容...",
    word_count_target=5000
)

# 3. 生成された原稿の品質チェック
mcp__noveler__noveler_check(episode=3)
```

### 9.4 プロレベル評価による高度な改善
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

### 9.5 10段階個別実行によるタイムアウト完全回避
```python
# LLM側で各ステップを個別に実行（各5分タイムアウト）
result1 = mcp__noveler__write_step_1(episode=1)
# → 5分タイムアウトでSTEP1実行、セッションID生成

result2 = mcp__noveler__write_step_2(
    episode=1,
    session_id=result1["session_id"]
)
# → 新たな5分タイムアウトでSTEP2実行

result3 = mcp__noveler__write_step_3(
    episode=1,
    session_id=result2["session_id"]
)
# → 新たな5分タイムアウトでSTEP3実行

# ... STEP4-9も同様に個別実行

result10 = mcp__noveler__write_step_10(
    episode=1,
    session_id=result9["session_id"]
)
# → 最後の5分タイムアウトでSTEP10実行

# 結果: 合計50分（5分×10ステップ）の実行時間を確保
# タイムアウトエラー完全解決！
```

## 10. グローバルコマンド統合機能

### 10.1 概要
MCPサーバーと連携するグローバルコマンド `/noveler` を提供し、任意の場所からの小説執筆を可能にします。

### 10.2 グローバルコマンド仕様

#### 10.2.1 コマンド構造
```bash
/noveler write <話数> [options]    # エピソード執筆
/noveler check <話数> [options]    # 品質チェック
/noveler plot <話数>               # プロット生成
/noveler status                    # プロジェクト状況確認
/noveler init <project-name>       # 新規プロジェクト初期化
```

#### 10.2.2 設置場所
- グローバル設定: `~/.claude/commands/noveler.md`
- ローカル設定: `<project>/.claude/commands/noveler.md`（優先）

#### 10.2.3 YAMLフロントマター
```yaml
---
allowed-tools: ["mcp__noveler__*"]
argument-hint: "<command> [options]"
description: "小説執筆支援（グローバル）"
model: "claude-3-5-sonnet-20241022"
---
```

## 11. 移行戦略

### 11.1 段階的移行
1. **Phase 1**: 基本ツール実装完了（v2.0.0）
2. **Phase 2**: Claude Code内部実行対応（v2.1.0完了）
   - `write_with_claude`ツール追加
   - 外部API依存の排除
   - ドライラン実行の実ファイル生成対応
3. **Phase 3**: 10段階個別実行対応（v2.2.0完了）
   - `write_step_1`〜`write_step_10`ツール追加
   - タイムアウト問題の完全解決
   - LLM協調実行パターン確立
   - 中断・再開機能の柔軟化
4. **Phase 4**: 詳細分析ツール追加（計画中）
5. **Phase 5**: AI連携強化（計画中）

### 11.2 後方互換性
- 既存のコマンド体系は維持
- 新ツールへの段階的移行を推奨
- レガシーサポートの継続

### 11.3 v2.4.0 新規実装ツール
**追加された必須ツール（98%準拠達成）**:

#### `write_stage` - 特定段階個別実行
```json
{
  "name": "write_stage",
  "description": "10段階システムの特定段階のみを個別実行",
  "parameters": {
    "episode": {"type": "integer", "required": true},
    "stage": {"type": "string", "enum": ["plot_data_preparation", "plot_structure_analysis", ...]},
    "session_id": {"type": "string", "optional": true},
    "resume_session": {"type": "string", "optional": true}
  }
}
```

#### `write_resume` - セッション再開
```json
{
  "name": "write_resume",
  "description": "中断した執筆セッションから再開",
  "parameters": {
    "episode": {"type": "integer", "required": true},
    "session_id": {"type": "string", "required": true}
  }
}
```

#### `write_manuscript_draft` - 原稿執筆段階のみ
```json
{
  "name": "write_manuscript_draft",
  "description": "段階8原稿執筆を単独で実行",
  "parameters": {
    "episode": {"type": "integer", "required": true},
    "word_count_target": {"type": "integer", "default": 4000}
  }
}
```

## 12. 成功指標

### 12.1 定量的指標
- ツール選択精度の向上（LLMのツール選択ログ分析）
- チェック実行時間の短縮（個別実行による効率化）
- 修正サイクル回数の削減
- **グローバルコマンド利用率** （任意場所からの実行回数）
- **タイムアウト発生率の削減** （5分超過エラー0%達成目標）
- **10段階完全実行成功率** （100%達成目標）

### 12.2 定性的指標
- 開発者の使いやすさ向上
- エラーメッセージの分かりやすさ
- 新機能追加の容易性
- **初回利用時の設定簡易性**

## 13. 期待される効果

### 13.1 LLM自律実行
```python
# LLMが文脈に応じて自動実行
await mcp__noveler__noveler_write(episode_number=1)
await mcp__noveler__noveler_check(episode_number=1, auto_fix=True)
```

### 13.2 ワークフローの自動化
- エピソード執筆 → 品質チェック → 完成処理の自動連携
- エラー検出時の自動復旧提案
- プロジェクト状況に応じた最適なアクション提案

### 13.3 保守性向上
- 機能追加時の独立実装が可能
- ツールごとの最適化とエラーハンドリング
- 段階的な機能拡張が容易

---

**最終更新日**: 2025-09-05
**バージョン**: v2.4.0
**作成者**: Claude Code (Serena MCP)
**承認**: [✓] 統合仕様書として承認
**重要変更**: 98%準拠達成、新規ツール3個追加、統一スキーマ適用完了

---

## 6. 段階的品質チェック API (REQ-QUALITY-STAGED-004)

段階的品質チェックは `ProgressiveCheckManager` を中心に段階タスクの定義・実行・履歴管理を行う。各ツールは `SPEC-QUALITY-110_progressive_check_flow.md`（ドラフト）で詳細 I/O を定義するが、本書では統合観点を示す。

| ツール名 | 役割 | 主なフィールド |
| --- | --- | --- |
| `get_check_tasks` | チェック手順案内 | `tasks[]` (id, phase, description, llm_instruction, estimated_duration) |
| `execute_check_step` | 段階実行 | `step_id`, `episode_number`, `manuscript_content?`, `check_focus?` → `success`, `quality_score`, `issues_found`, `files` |
| `get_check_status` | 進捗モニタ | `progress_percentage`, `completed_steps`, `current_phase`, `next_step` |
| `get_check_history` | 実行ログ | `history[]` (step_id, executed_at, execution_time, success, quality_score) |
| `check_basic` | CLI互換の簡易チェック | CLI `noveler check --basic` を内部的に呼び出し、互換性を維持 |

すべてのレスポンスは `session_id` を含み、WorkflowStateStore 経由で `.noveler/checks/{session_id}/` に永続化される（詳細は SPEC-QUALITY-120）。 セッションは復旧や再開時に `execute_check_step` へ再注入できる。

## 7. データ／アーティファクト統合 (REQ-DATA-001〜003)

- `convert_cli_to_json` と `validate_json_response` は CLI 実行結果を `StandardResponseModel` / `ErrorResponseModel` へ正規化し、`temp/json_output/` に保存する。
- `get_file_reference_info` / `list_files_with_hashes` / `get_file_by_hash` / `check_file_changes` は SHA256 を用いた差分検知を提供し、MCP クライアントが安全に成果物を再取得できるようにする。
- `fetch_artifact` / `list_artifacts` / `backup_management` は `.noveler/artifacts/` を介した成果物保全・バックアップ機構を統括する。

各成果物メタデータには `source_tool`, `created_at`, `hash` を付与し、`requirements_traceability_matrix.yaml` と整合する。

## 8. MCP書き込みツールの安全対策 (REQ-OPS-WRITE-001)

`write` ツールは次の安全策を満たす。

1. **プロジェクトルート正規化**: `create_path_service(project_root)` が環境変数や設定ファイルを参照し、作業ディレクトリ外への書き込みを防止。
2. **親ディレクトリ生成時の安全性**: `Path.mkdir(parents=True, exist_ok=True)` を使用し、権限が不足する場合は早期に例外を送出。
3. **レスポンス情報**: `absolute_path`, `relative_path`, `project_root`, `content_length` を返却し、クライアントが検証できるようにする。
4. **エラー伝搬**: 例外発生時は `success: False` とともに `arguments` を返却し、再試行判断を支援。

`status` ツールは読み取り専用であり、`noveler` エイリアスは CLI コマンドを実行後に `convert_cli_to_json` へ委譲して構造化レスポンスに変換する。

## 9. TenStage/18ステップ統合連携

- `write_step_*` と `write_stage`/`write_resume` は `TenStageSessionManager` が生成する JSON セッションを共有し、途中再開を保証する。
- `enhanced_*` 系ツールは PathService フォールバックイベントと診断情報を含み、LLM が自律的にリカバリフローを構築できるようにする。
- CLI `noveler write` フローは MCP ツール群をオーケストレーションするアダプタであり、詳細は `SPEC-WRITE-018` を参照。

---
