# Aliases Setup

## 使い方
```bash
source /mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/.novel_aliases
```

## 永続化（推奨）
```bash
echo "source /mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/.novel_aliases" >> ~/.bashrc
```

## 使用可能なエイリアス（例）
- `ntest`: bin/test -q
- `ncheck`: python scripts/tools/check_tdd_ddd_compliance.py
- `ncoverage`: python scripts/tools/test_coverage_analyzer.py
- `mrun`: noveler mcp call run_quality_checks '{"episode_number": 1, "additional_params": {"format": "summary"}}'
- `mpolish`: noveler mcp call polish_manuscript '{"episode_number": 1, "file_path": "40_原稿/第001話_サンプル.md", "stages": ["stage2"], "dry_run": true}'
- `martifacts`: noveler mcp call list_artifacts '{"episode_number": 1}'

Tips:
- テストは `bin/test` または `python3 scripts/run_pytest.py`（推奨）か `make test` を利用すると環境/出力が統一されます。
- 推奨: `bin/test -q` や `bin/test-json -q` を使用して環境/出力を統一します。
- 互換: 直pytestも可能ですが、必要に応じてランナーと同等の環境を整えてください。
- `/test-json` は `--json-only` 相当で、LLM向けに最小のJSON要約のみを出力します。
- `/test-changed` は `RANGE='origin/master...HEAD'` のように差分範囲を指定可能です。
