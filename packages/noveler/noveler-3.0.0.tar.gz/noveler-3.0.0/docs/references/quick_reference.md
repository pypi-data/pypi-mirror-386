# Quick Reference

> dist ラッパー生成: CIは `scripts/ci/ensure_dist_wrapper.py`、ローカルは `make build-dist-wrapper`。

## 🚀 よく使用するコマンド
```bash
# テスト実行
ntest                          # 全テスト実行
ntest tests/unit/              # ユニットテストのみ

# 品質チェック
ncheck                         # DDD準拠性チェック
nquality                       # Ruff + mypy チェック
ncoverage                      # カバレッジ分析

# 執筆
nwrite 5                       # 第5話執筆
nplot 5                        # 第5話プロット作成
```

## 🧰 CIで品質チェック（NDJSON + フォールバック検出）
```bash
# NDJSONを生成しつつ、各行に path_fallback_used / path_fallback_events_count を付与
python scripts/ci/run_quality_checks_ndjson.py --episode 1 --out reports/quality.ndjson

# PathServiceのフォールバック発生をCI失敗条件に含める
python scripts/ci/run_quality_checks_ndjson.py --episode 1 --fail-on-path-fallback

# サンプルプロジェクトを明示指定
python scripts/ci/run_quality_checks_ndjson.py \
  --project-root "../10_Fランク魔法使いはDEBUGログを読む" \
  --episode 1 --out reports/quality.ndjson
```

## 🧪 GUIDE_ROOTでテストを動かす（サンプルプロジェクト指定）
- 優先度順でプロジェクトルートが解決されます:
  1) `PROJECT_ROOT` または `NOVELER_TEST_PROJECT_ROOT`
  2) `config/novel_config.yaml` の `paths.samples.root`

### paths セクションのサンプル（config/novel_config.yaml）

以下は、パス関連設定と strict モードを含む最小サンプルです。

```yaml
paths:
  strict: false            # CI/本番で厳格化する場合は true 推奨（ENV優先: NOVELER_STRICT_PATHS）

  project_paths:           # プロジェクト直下のディレクトリ名を上書きしたい場合に使用
    manuscripts: "40_原稿"
    management:  "50_管理資料"
    plots:       "20_プロット"
    prompts_dir: "60_プロンプト"

  sub_directories:         # サブディレクトリ名の上書き（必要に応じて）
    plot_subdirs:
      episode_plots: "話別プロット"
      chapter_plots: "章別プロット"
    management_subdirs:
      quality_records: "品質記録"
    prompt_subdirs:
      analysis_results: "全話分析結果"
```

メモ:
- 環境変数 `NOVELER_STRICT_PATHS` が指定されている場合、`paths.strict` より優先されます。
- `.novelerrc.yaml` の `paths.strict` でも上書き可能（ENV > novel_config.yaml > .novelerrc）。

### QA/スキップ状況
- テストスキップの現状と回復計画は `docs/notes/test_skip_status.md` を参照してください。
  3) `NOVELER_SAMPLES_ROOT`（サンプル親）または既定サンプル

- 本リポジトリでは既定を設定済みです:
  ```yaml
  # config/novel_config.yaml
  paths:
    samples:
      root: "/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/10_Fランク魔法使いはDEBUGログを読む"
  ```

- 一時的に上書きしたい場合:
  ```bash
  export PROJECT_ROOT="/path/to/your/sample-project"
  pytest -c tests/e2e/pytest_e2e.ini -q
  ```

## 📁 重要なファイル
- `CLAUDE.md`: 必須開発ルール
- `docs/_index.yaml`: ドキュメント索引
- `pyproject.toml`: プロジェクト設定

## 🔧 トラブルシューティング
- インポートエラー → `PYTHONPATH=$PWD`
- テスト失敗 → `docs/04_よくあるエラーと対処法.md`
- DDD違反 → `docs/B00_情報システム開発ガイド.md`

## 🎯 開発フロー
1. `ntest` でテスト確認
2. `ncheck` で品質確認
3. コード修正
4. `git add . && git commit -m "fix: ..."`


Tip: Exclude dialogue lines from sentence-length checks by passing `exclude_dialogue_lines: true` to `run_quality_checks`.
