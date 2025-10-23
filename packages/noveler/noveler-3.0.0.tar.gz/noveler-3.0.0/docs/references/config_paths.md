#!/usr/bin/env markdown
# パス設定ガイド（config/novel_config.yaml / .novelerrc）

本ガイドでは、パス管理に関する設定方法と strict モードの有効化方法を示します。

## 1. 設定ファイルと優先度

- 環境変数: `NOVELER_STRICT_PATHS`（最優先）
- 統合設定: `config/novel_config.yaml` の `paths.*`
- ローカル設定: `.novelerrc.yaml` / `.yml` / `.json` の `paths.*`

優先度は ENV > novel_config.yaml > .novelerrc です。

## 2. strict モード（推奨）

strict モードは、PathService が旧仕様のフォールバックに頼る状況を検出してエラーや警告にします。

- 有効化（いずれか）
  - `NOVELER_STRICT_PATHS=1`（`true`/`yes`/`on`）
  - `config/novel_config.yaml`:
    ```yaml
    paths:
      strict: true
    ```
  - `.novelerrc.yaml`:
    ```yaml
    paths:
      strict: true
    ```

- 挙動
  - `get_episode_plot_path`/`get_episode_title` で旧仕様フォールバックが必要になると、strict時は `PathResolutionError` を送出
  - 非strict時は warning ログとともに動作継続。MCPツール応答には `path_fallback_used` と `path_fallback_events` を含め可視化します

## 3. パス関連の上書き（任意）

`config/novel_config.yaml` の `paths.project_paths` や `paths.sub_directories` でプロジェクト内のディレクトリ名を上書きできます。

```yaml
paths:
  project_paths:
    manuscripts: "40_原稿"
    management:  "50_管理資料"
    plots:       "20_プロット"
    prompts_dir: "60_プロンプト"

  sub_directories:
    plot_subdirs:
      episode_plots: "話別プロット"
      chapter_plots: "章別プロット"
    management_subdirs:
      quality_records: "品質記録"
    prompt_subdirs:
      analysis_results: "全話分析結果"
```

## 4. 推奨運用

- 開発中: strict を無効（デフォルト）にし、警告や MCP 出力の `path_fallback_events` を見て逐次修正
- CI/本番: strict を有効化し、逸脱を遮断

## 5. 旧命名→新命名の移行支援ツール

プロジェクト内の原稿・話別プロットの旧仕様を検出・移行するツールを同梱しています。

検出のみ:
```bash
python scripts/tools/paths_validate_migrate.py validate \
  --project-root /path/to/project \
  --json-out reports/paths_validate.json
```

自動移行（ドライラン）:
```bash
python scripts/tools/paths_validate_migrate.py migrate \
  --project-root /path/to/project \
  --fix-manuscripts --fix-plots --dry-run \
  --json-out reports/paths_migrate_plan.json
```

実行移行（実ファイル変更あり・慎重に）:
```bash
python scripts/tools/paths_validate_migrate.py migrate \
  --project-root /path/to/project \
  --fix-manuscripts --fix-plots
```

注意:
- 競合（同名ファイルが既に存在）時は自動でスキップします。出力JSONを確認してから再実行してください。
- strict モード有効化前に移行実施することを推奨します。

## 6. CI 連携とフォールバック検出

品質チェックをCIで実行し、PathServiceのフォールバック発生を検出・失敗条件に含める例です。

NDJSON出力＋列拡張（各行に path_fallback_used / path_fallback_events_count を付与）:
```bash
python scripts/ci/run_quality_checks_ndjson.py \
  --project-root /path/to/project \
  --episode 1 \
  --out reports/quality.ndjson
```

フォールバック検出をCI失敗条件に含める:
```bash
python scripts/ci/run_quality_checks_ndjson.py \
  --project-root /path/to/project \
  --episode 1 \
  --fail-on-path-fallback
```

補足:
- `--project-root` を省略し `00_ガイド` 配下で実行した場合、隣接のサンプル「10_Fランク魔法使いはDEBUGログを読む」を自動対象にします（存在時のみ）。
- strictモード（ENV `NOVELER_STRICT_PATHS=1` など）を有効化すると、フォールバックをエラーとして扱いCIで早期検出できます。
