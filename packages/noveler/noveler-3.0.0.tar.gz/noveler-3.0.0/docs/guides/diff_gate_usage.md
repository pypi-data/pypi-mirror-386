# Diff Gate Usage Guide

このガイドはローカル開発で差分ゲート（collect-only + encoding guard）を実行するための手順をまとめています。

## スクリプト概要
- ファイル: scripts/ci/diff_gate.sh
- 機能:
  1. python3 -m pytest --collect-only -q tests/docs/test_docs_sample_paths.py（軽量スモークでpytest収集を確認）
  2. python scripts/hooks/encoding_guard.py --diff-range … で差分ファイルのみエンコーディングチェック
  3. python3 scripts/report_encoding_summary.py で summary 更新

## 使い方
`ash
# ブランチ差分を対象
scripts/ci/diff_gate.sh origin/main...HEAD

# 直前コミットとの差分
scripts/ci/diff_gate.sh HEAD~1..HEAD

# 変更ファイル一覧をパイプで渡す例
git diff --name-only HEAD~1 | scripts/ci/diff_gate.sh
`

## Git エイリアス例
~/.gitconfig に以下を追記すると git diff-gate で実行できます。
`ini
[alias]
  diff-gate = !bash scripts/ci/diff_gate.sh origin/main...HEAD
`

## CI への組み込み（任意）
Git のローカル管理が前提の場合でも、任意の CI (cron, Jenkins 等) で以下を呼び出せば同様のチェックが可能です。
`ash
python scripts/hooks/encoding_guard.py --diff-range origin/main...HEAD \
  --fail src/**/*.py --warn docs/**/*.md --exclude docs/archive/** docs/backup/**
`

## 失敗時の対応
- collect-only が失敗 → テストコードまたは依存を確認し、python3 -m pytest -q で再現。
- encoding guard が fail → 該当ファイルを開き、UTF-8 保存・U+FFFD の除去後に /scan-encoding で再確認。
