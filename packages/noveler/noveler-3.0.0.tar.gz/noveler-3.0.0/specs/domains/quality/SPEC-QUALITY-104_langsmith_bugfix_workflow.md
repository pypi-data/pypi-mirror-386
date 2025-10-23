# SPEC-QUALITY-104: LangSmithバグ修正ワークフロー統合

## メタデータ

| 項目 | 内容 |
|------|------|
| 仕様ID | SPEC-QUALITY-104 |
| E2EテストID | E2E-QUALITY-104 |
| test_type | unit / integration |
| バージョン | v1.1.0 |
| 作成日 | 2025-09-16 |
| 最終更新 | 2025-09-18 |
| ステータス | canonical |
| 関連仕様 | SPEC-QUALITY-001, SPEC-QUALITY-002, SPEC-QUALITY-003 |

## 1. 概要

LangSmithで記録された失敗ランを起点に、修正提案の生成、パッチ適用、検証再実行までを一気通貫で補助するワークフローを定義する。MCPツール `langsmith_generate_artifacts` / `langsmith_apply_patch` / `langsmith_run_verification` を介し、品質管理ツール群と連携してバグ修正リードタイムを短縮する。

## 2. ビジネス要件

### 2.1 目的
- LangSmithトレーシング情報の可視化により失敗要因の特定を高速化する。
- 修正パッチ作成〜検証の作業を半自動化し、バグ修正リードタイムを短縮する。

### 2.2 成功基準
- run.json から生成した要約・再現データが 60 秒以内に取得できる。
- 失敗ランから再現テストが自動登録され、再実行コマンドが標準化されている。
- 同一 MCP ツール群上でパッチ適用と再検証を完結できる。

## 3. 機能仕様

### 3.1 スコープ
- **含む**: LangSmithランの JSON 取り込み、要約生成、再現データセット作成、パッチ適用、検証コマンド実行、成果物出力管理。
- **含まない**: LangSmith API 呼び出し、リモート Git 操作、LLM による自動パッチ生成、LangSmith UI の代替。

### 3.2 MCPツール連携

| ツール名 | 役割 | 主要入力 | 主な出力/保存先 |
| --- | --- | --- | --- |
| `langsmith_generate_artifacts` | run.json から成果物を生成 | `run_json_path?`, `run_json_content?`, `output_dir`, `dataset_name?`, `expected_behavior?`, `project_root?` | `.noveler/artifacts/langsmith/{run_id}/summary.md`, `prompt.txt`, `datasets/{dataset}.jsonl`, `artifact_manifest.json` |
| `langsmith_apply_patch` | 差分パッチの適用 | `patch_text?`, `patch_file?`, `strip?`, `project_root?` | `applied`, `output`, `stderr`, `patched_files[]` |
| `langsmith_run_verification` | 再検証コマンドの実行 | `command?`, `project_root?`, `env?` | `returncode`, `stdout`, `stderr`, `duration_ms`, `command` |

成果物は `.noveler/artifacts/langsmith/{run_id}/` 配下に保存し、品質レポートや再現テストと連携する。`output_dir` を省略した場合は `reports/langsmith/{run_id}/` が既定値となる。

### 3.3 ユースケース

#### UC-001: 失敗ラン要約生成
```yaml
前提条件: LangSmith run.json が存在
アクター: 開発者
入力: run.json, output_dir, dataset_name?, expected_behavior?
処理手順:
  1. run.json を解析し LangSmithRun エンティティを生成
  2. エラー要約、再現プロンプト、データセットエントリを作成
  3. 成果物を artifacts/langsmith/{run_id}/ に保存
期待出力: summary.md, prompt.txt, dataset jsonl
事後条件: manifest に成果物一覧が追記される
```

#### UC-002: 再現データセット登録
```yaml
前提条件: UC-001 実行済み
アクター: 開発者
入力: LangSmithRun, dataset_name
処理手順:
  1. dataset/{name}.jsonl に run_id, prompt, expected_behavior を追記
  2. 重複 run_id があれば上書き
期待出力: dataset jsonl の更新
事後条件: 再現テストから参照可能なデータセットが最新化
```

#### UC-003: パッチ適用と検証
```yaml
前提条件: 修正 diff が生成済み
アクター: 開発者
入力: patch_text? or patch_file?, strip?, project_root, verification command
処理手順:
  1. patch を適用し結果を出力
  2. 検証コマンド（例: pytest）を実行
  3. stdout/stderr/returncode を保存
期待出力: patch 実行ログ, verification.log
事後条件: 成功/失敗ステータスが artifacts manifest に記録
```

## 4. 技術仕様

### 4.1 インターフェース定義

```python
class LangSmithBugfixWorkflowService:
    def prepare_artifacts(
        self,
        run_json: Path | str | dict,
        output_dir: Path,
        dataset_name: str | None,
        expected_behavior: str | None = None,
    ) -> LangSmithBugfixArtifacts:
        ...

    def apply_patch(
        self,
        patch_text: str | None,
        patch_file: Path | None,
        project_root: Path,
        strip: int = 1,
    ) -> PatchResult:
        ...

    def run_verification(
        self,
        command: Sequence[str] | None,
        project_root: Path,
        env: Mapping[str, str] | None = None,
    ) -> VerificationResult:
        ...
```

CLI フロントエンド: `python -m noveler.tools.langsmith_bugfix_helper` が `summarize` / `apply` / `verify` サブコマンドを提供。MCP ツールはこのサービスクラスをラップし FastMCP のレスポンス形式で返却する。

### 4.2 データモデル

```yaml
LangSmithRun:
  run_id: string
  name: string | null
  status: enum [success, error, running]
  error: string | null
  trace_url: string | null
  inputs: dict
  outputs: dict
  metadata: dict

LangSmithBugfixArtifacts:
  summary_path: Path
  prompt_path: Path
  dataset_entry_path: Path | null
  manifest_path: Path
  run: LangSmithRun

PatchResult:
  applied: bool
  output: string
  error: string | null
  patched_files: list[string]

VerificationResult:
  returncode: int
  stdout: string
  stderr: string
  command: list[string]
  duration_ms: int
```

## 5. 検証仕様

| レベル | テストID | 内容 | 期待結果 |
| --- | --- | --- | --- |
| Integration | INT-QUALITY-104-APPLY | パッチ適用ツールの実行 | patch コマンド経由でファイルが更新される |
| Integration | INT-QUALITY-104-VERIFY | 検証コマンド実行 | returncode/ログが取得できる |
| Unit | UNIT-QUALITY-104-RUN | LangSmithRunLoader | run.json から必要フィールドが抽出される |
| Unit | UNIT-QUALITY-104-SUMMARY | WorkflowService.prepare_artifacts | summary/prompt/dataset が作成される |
| Unit | UNIT-QUALITY-104-DATASET | LangSmithDatasetManager | JSONL 追記が重複なく行われる |

## 6. 非機能要件

- 1MB 以下の run.json を 1 秒以内に解析する。
- patch 適用と検証コマンドは進捗ログをリアルタイムで出力する。
- 成果物パスはすべて `PathService` で正規化し、書き込み権限がない場合は即座に `error` を返却する。

## 7. エラー・リカバリ

| エラーコード | 発生条件 | 対応 |
| --- | --- | --- |
| LS-001 | run.json パース失敗 | 例外詳細を返却し、整形手順を提示 |
| LS-002 | patch 適用失敗 | 標準エラーを `output` に付与し、`--strip` 調整を案内 |
| LS-003 | 検証コマンド非ゼロ終了 | returncode と stderr を artifacts manifest に記録し再実行コマンドを提示 |

## 8. 実装参照

```yaml
production_code:
  - src/noveler/application/services/langsmith_bugfix_workflow_service.py
  - src/noveler/infrastructure/services/langsmith_artifact_manager.py
  - src/noveler/domain/value_objects/langsmith_artifacts.py
  - src/mcp_servers/noveler/tools/langsmith_bugfix_tool.py
  - src/noveler/tools/langsmith_bugfix_helper.py

related_tests:
  - tests/unit/application/services/test_langsmith_bugfix_workflow_service.py
  - tests/unit/infrastructure/services/test_langsmith_artifact_manager.py
  - tests/unit/tools/test_langsmith_bugfix_helper_cli.py
```

---

本仕様書は REQ-QUALITY-LANG-005 (LangSmith連携によるバグ修正フロー) の準拠を担保する。成果物構造や MCP ツールの入出力形式に変更が入った場合は、本書の §3.2/§4.2 を更新し、トレーサビリティマトリクスを併せて修正すること。
