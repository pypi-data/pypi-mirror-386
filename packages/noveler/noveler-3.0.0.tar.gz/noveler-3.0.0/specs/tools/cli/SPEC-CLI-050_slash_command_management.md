# SPEC-CLI-050: Slash Command Management System

**Version**: 1.1
**Status**: Draft (レビュー指摘事項反映版)
**Last Updated**: 2025-10-06

## Purpose
小説執筆支援プロジェクトにおけるチャットスラッシュコマンドを単一ソースで管理し、生成・同期・権限設定・ドキュメント更新を自動化する。

## Scope
- 対象: Codex/Claude Code で使用する全スラッシュコマンド。
- 含む: コマンド定義形式、生成スクリプト、権限同期、ドキュメント生成、CI 検証、移行手順。
- 含まない: コマンドのランタイム挙動、MCP ツール側の実装、E2E 実行の自動テスト。

## 変更履歴 (v1.0 → v1.1)
- P0-1: `.codex/commands.json` 管理方針を明確化 → オプション B 採用 (`.claude/settings.local.json` に統合)
- P0-2: `bin/noveler` プレースホルダ展開仕様を詳細化 (`noveler exec-slash` サブコマンド)
- P0-3: 移行計画に Phase 分割・成功条件・ロールバック手順を追加
- P1-4: CLAUDE.md へ最小限の統合記述を追加
- P1-5: エラーハンドリング仕様を明確化 (PlaceholderTypeError 等)
- P1-6: CI 検証スクリプトの詳細仕様を追加 (diff ロジック)

## 1. 構成要素
### 1.1 定義ファイル (新規)
- パス: `config/slash_commands.yaml`
- 役割: コマンドの唯一のソース (Single Source of Truth)
- 構造例:
  ```yaml
  commands:
    - name: /write-tasks
      script: bin/noveler
      args: ["mcp", "call", "enhanced_get_writing_tasks", "{episode_payload}"]
      description: "18ステップ執筆タスクリストを取得"
      placeholders:
        episode_payload:
          prompt: "Episode number?"
          format: '{"episode_number": %s}'
          type: int
      permissions:
        windows:
          - "Bash(./bin/noveler:*)"
        wsl:
          - "Bash(bin/noveler:*)"
      category: writing
      tags: ["writing", "tasks"]
  ```
- `placeholders` でユーザー入力が必要な項目を定義。`prompt`, `type`, `format`, `default`, `choices` などを拡張可能。

### 1.2 生成スクリプト (新規)
- パス: `scripts/setup/build_slash_commands.py`
- 入力: `config/slash_commands.yaml`
- 出力:
  - `.claude/settings.local.json` (repo 内のローカル設定; slashCommands + permissions を統合管理)
  - `docs/slash_commands/README.md` (自動生成された一覧)
  - ユーザー環境の `~/.claude/commands/noveler.md` など (オプション)
- 機能: YAML を読み込み、生成物を書き出し、必要に応じて乾式実行をサポート。
- 注意: `.codex/commands.json` は生成しない（設計決定: オプション B 採用; 理由は decision_log.yaml 参照）

### 1.3 同期スクリプト (既存整理)
- `scripts/setup/update_slash_commands.py` は YAML を読むよう改修し、ユーザー設定の permissions.allow に追記する責務だけを持つ。
- 生成ロジックは `build_slash_commands.py` へ移管。

### 1.4 CLI ツール (既存整理)
- `bin/update_claude_commands.py` の機能を `build_slash_commands.py` に統合。
- 旧スクリプトは互換モードで新スクリプトを呼び出し、段階的に廃止。

## 2. 導入フロー
1. `config/slash_commands.yaml` を追加し、最小エントリを記述。
2. `python scripts/setup/build_slash_commands.py --dry-run` で妥当性を確認。
3. 生成物 ( `.codex/commands.json` 等 ) をコミット。
4. コマンド追加時は YAML を編集 → 生成スクリプト実行 → 差分レビュー。
5. CI に YAML と生成物の一致チェックを追加。

## 3. テンプレートとプレースホルダ

### 3.1 実装責務
- **Claude Code 側**: `{placeholder}` をそのまま保持し、コマンド実行時に CLI へ渡す
- **CLI 側 (`bin/noveler`)**: 新サブコマンド `noveler exec-slash` を実装
  - `--command-json` で YAML から生成されたコマンド定義を受け取る
  - プレースホルダを検出し、インタラクティブ入力を要求
  - 展開後に実際のコマンド (例: `noveler mcp call ...`) を実行

### 3.2 プレースホルダ定義
- `placeholders` はメタデータとして以下をサポート:
  - `prompt`: ユーザーへの質問文 (必須)
  - `type`: 型 (`int`, `str`, `bool`; デフォルト `str`)
  - `format`: 展開後のフォーマット文字列 (例: `'{"episode_number": %s}'`)
  - `default`: デフォルト値 (任意)
  - `choices`: 選択肢リスト (任意)

### 3.3 エラーハンドリング
- 型変換失敗時: `PlaceholderTypeError` を送出し、再入力を促す
- 必須入力の欠如: `PlaceholderRequiredError` を送出
- 不正な choices: `PlaceholderValidationError` を送出

### 3.4 後方互換性
- 既存の `noveler mcp call` は引き続きサポート
- プレースホルダなしコマンドは従来通り動作 (直接 Bash 実行)

## 4. 権限設定 (permissions.allow)
- YAML の `permissions` で OS / 実行環境別の権限文字列を管理 (Windows / WSL / macOS 等)。
- `build_slash_commands.py` が `.claude/settings.local.json` とユーザー設定へ反映し、重複は除外。
- 既存の `/test*` 権限も YAML へ移植する。

## 5. ドキュメント生成
- `docs/slash_commands/README.md` は生成スクリプトで自動作成。
- 内容:
  - 自動生成の注意書き
  - カテゴリ別コマンド一覧 (`category` でグループ化)
  - 例示的な使用方法 (`args`, `placeholders` から構築)
  - 最終更新日時
- 手動編集は禁止し、ヘッダにその旨を明記。

## 6. 互換オプション
- `--dry-run`: 生成結果を表示のみ。
- `--user-config / --no-user-config`: ユーザー環境への出力を切り替え。
- `update_slash_commands.py` 互換モード: 内部的に `build_slash_commands.py` を呼ぶ。

## 7. CI チェック
- 新スクリプト `scripts/checks/verify_slash_commands.py` を追加。
- 手順:
  1. `build_slash_commands.py --dry-run --output <tmp>` を実行。
  2. リポジトリ内の生成ファイルと diff。相違があれば CI を失敗。
- 対象ファイル: `.claude/settings.local.json`, `docs/slash_commands/README.md`。

## 8. 移行計画

### Phase 1: YAML 準備 (リスクなし; 所要時間 4時間)
**目的**: 新方式の準備と既存方式との一致検証

**タスク**:
- [ ] `config/slash_commands.yaml` を作成し、既存 `/test*` コマンドを登録
- [ ] `scripts/setup/build_slash_commands.py` を実装 (基本機能のみ)
- [ ] dry-run で出力を既存ファイルと diff 比較 → 完全一致を確認

**成功条件**:
```bash
python scripts/setup/build_slash_commands.py --dry-run > /tmp/new_settings.json
diff /tmp/new_settings.json .claude/settings.local.json
# 差分がないこと (permissions.allow の順序のみ許容)
```

**ロールバック**: なし (既存ファイルは変更しない)

---

### Phase 2: 並行運用 (2週間; 検証期間)
**目的**: 新旧両方式の検証と安定性確認

**タスク**:
- [ ] `.claude/settings.local.json` に `# Auto-generated` コメントを追加
- [ ] CI で新旧両方式の出力が一致することを毎日検証
- [ ] `scripts/checks/verify_slash_commands.py` を導入し、pre-push hook に追加

**成功条件**:
- CI が 2週間連続で green (新旧一致)
- 手動での `/test` 実行が正常動作

**ロールバック手順**:
```bash
git checkout HEAD -- .claude/settings.local.json
git checkout HEAD -- scripts/setup/update_slash_commands.py
# Phase 1 のコミットを revert
```

---

### Phase 3: 切り替え (所要時間 2時間)
**目的**: 新方式への完全移行

**タスク**:
- [ ] `update_slash_commands.py` を YAML 読み込み版に置き換え
- [ ] `bin/update_claude_commands.py` に非推奨警告を追加
- [ ] CLAUDE.md に新ワークフローを明記

**成功条件**:
- `python scripts/setup/update_slash_commands.py` が YAML から生成
- `/test` コマンドが引き続き動作

**ロールバック手順**:
```bash
# Phase 2 の最終コミットへ戻す
git revert <phase3-commit-hash>
```

---

### Phase 4: クリーンアップ (1ヶ月後)
**目的**: レガシーコードの削除

**タスク**:
- [ ] BASH_PERMS 定数を削除 (YAML に完全移行)
- [ ] `bin/update_claude_commands.py` を `scripts/legacy/` へ移動
- [ ] 旧方式のドキュメントをアーカイブ

**成功条件**:
- `git grep "BASH_PERMS"` が 0件
- CI が引き続き green

**ロールバック**: Phase 3 へ戻す (旧スクリプトを復元)

## 9. 非対象事項
- IDE 側で `category` を直接利用する仕組み。
- 外部テンプレートエンジン (Jinja2 等) の導入。
- スラッシュコマンド経由の E2E テスト実行自動化。
