# Task Tracking Workflow Guide

**Version**: 0.3
**Last Updated**: 2025-10-12
**Status**: Draft

## Purpose

本ガイドは `TODO.md` と `CHANGELOG.md` の運用を機械処理しやすい形に統一し、タスク移行や監査を安全かつ再現性高く行うことを目的としています。

---

## Overview

- 作業中のタスクはすべて `TODO.md` の構造化テーブルで管理します。
- 完了したタスクはコミットIDを含めて `CHANGELOG.md` の記録テーブルへ移行します。
- `scripts/task_table_sync.py` を用いて完了行の抽出・整形・検証を自動化します。

---

## Structured Table Format

### TODO.md

`TODO.md` には以下のマーカーで囲まれたテーブルを配置します。

```
<!-- TASK_TABLE_START -->
| ID | Title | Owner | Status | Created | Due | Completed | Commit | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TODO-2025-001 | 例: Progressive Writeの改善計画策定 | yamada | active | 2025-10-12 | 2025-10-20 | | | 主要な検討トピックを箇条書きで整理 |
<!-- TASK_TABLE_END -->
```

### CHANGELOG.md

`CHANGELOG.md` 側では完了済みタスクのみを保持します。**v2025-10-12以降、Categoryフィールドが追加されました。**

```
<!-- CHANGELOG_TABLE_START -->
| ID | Category | Title | Owner | Completed | Commit | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| TODO-2025-000 | Features | 例: Progressive Writeの改善計画策定 | yamada | 2025-10-18 | abc1234 | レビュー: @suzuki / 骨子合意済み |
<!-- CHANGELOG_TABLE_END -->
```

---

## Field Definitions

### TODO.md フィールド

| Field | 必須 | 説明 |
| --- | --- | --- |
| `ID` | ✅ | `TODO-<Year>-<連番>` 形式。ゼロ埋め4桁推奨。 |
| `Title` | ✅ | タスクの概要。50文字以内を目安。 |
| `Owner` | ✅ | タスク責任者のハンドル。複数名はカンマ区切り。 |
| `Status` | ✅ | `active` / `blocked` / `done` のいずれか。 |
| `Created` | ✅ | 着手日（YYYY-MM-DD）。 |
| `Due` | 任意 | 期日がある場合のみ入力。 |
| `Completed` | `done` 行で必須 | 完了日（YYYY-MM-DD）。 |
| `Commit` | `done` 行で必須 | 該当実装コミットID（短縮7文字推奨）。複数ある場合はカンマ区切り。 |
| `Notes` | 任意 | 詳細メモ。`<br>` で複数行表現可。 |

### CHANGELOG.md フィールド

| Field | 必須 | 説明 |
| --- | --- | --- |
| `ID` | ✅ | TODO.mdから引き継ぎ。 |
| `Category` | 自動付与 | `Features` / `Fixes` / `Refactoring` / `Testing` / `Documentation` 等。**自動分類詳細は後述**。 |
| `Title` | ✅ | TODO.mdから引き継ぎ。 |
| `Owner` | ✅ | TODO.mdから引き継ぎ。 |
| `Completed` | ✅ | TODO.mdから引き継ぎ。 |
| `Commit` | ✅ | TODO.mdから引き継ぎ。 |
| `Notes` | 任意 | TODO.mdから引き継ぎ。 |

---

## Automatic Category Classification

**v2025-10-12以降、CHANGELOG移行時にカテゴリが自動付与されます。**

### 分類戦略（3段階）

1. **タイトルパターンマッチング**
   - タスクの `Title` フィールドから正規表現パターンでカテゴリを推論
   - 例: `fix:`, `feat:`, `refactor:`, `修正:`, `実装:` 等のプレフィックス

2. **コミットメッセージ解析**
   - タイトルで判定できない場合、`Commit` フィールドのコミットハッシュから実際のコミットメッセージを取得
   - Conventional Commits形式（`feat(scope): message`）に対応
   - 複数コミットがある場合は最初の3件まで解析（設定で変更可能）

3. **フォールバック**
   - 上記で判定できない場合は既定カテゴリ（`Refactoring`）を適用

### 設定ファイル: `config/task_categories.yaml`

`config/task_categories.yaml` でカテゴリ分類ルールをカスタマイズできます。

**主要カテゴリ**:
- `Features` - 新機能追加
- `Fixes` - バグ修正
- `Refactoring` - リファクタリング・整理
- `Testing` - テスト追加・改善
- `Documentation` - ドキュメント更新
- `Performance` - パフォーマンス改善
- `Security` - セキュリティ修正
- `Dependencies` - 依存関係更新
- `CI/CD` - ビルド・デプロイ改善
- `Maintenance` - その他保守作業

**設定例**:

```yaml
rules:
  - pattern: "^(fix|bugfix|hotfix|修正):"
    category: Fixes
    description: "Bug fixes and error corrections"

  - pattern: "^(feat|feature|add|追加|実装):"
    category: Features
    description: "New features and functionality"

  - pattern: "^(refactor|cleanup|整理):"
    category: Refactoring
    description: "Code refactoring and cleanup"

conventional_commits:
  feat: Features
  fix: Fixes
  refactor: Refactoring
  test: Testing
  docs: Documentation

default_category: Refactoring
fallback_strategy: commit_analysis

options:
  case_sensitive: false
  check_commit_messages: true
  max_commits_to_analyze: 3
```

詳細は `config/task_categories.yaml` のコメントを参照してください。

---

## Workflow

1. **タスク登録**: `TODO.md` のテーブル末尾へ新行を追加し、`Status` を `active` に設定します。
2. **ステータス更新**: 進捗に応じて `Status` を更新し、ブロッカーやメモを `Notes` に追記します。
3. **完了処理**:
   - 実装コミットを作成し、コミットIDを控える。
   - テーブル上で `Status` を `done` に、`Completed` と `Commit` を記入する。
4. **移行実行**:
   1. `scripts/task_table_sync.py --check` で整合性を確認。
   2. フォーマット崩れがあれば `scripts/task_table_sync.py --format-only --apply` で整形。
   3. 問題がなければ `scripts/task_table_sync.py --apply` を実行し、完了行を `CHANGELOG.md` へ移動。
   - **カテゴリは自動付与されます**（タイトルまたはコミットメッセージから推論）
5. **レビュー**: 変更差分を確認し、必要に応じてレビューアへ共有します。

---

## Script Usage

```bash
# Dry-run（確認のみ）
python scripts/task_table_sync.py

# チェックのみ（整合性検査）
python scripts/task_table_sync.py --check

# フォーマットのみ（ズレを自動整形）
python scripts/task_table_sync.py --format-only --apply

# 実際に移行を適用
python scripts/task_table_sync.py --apply

# カテゴリ設定ファイルを明示指定
python scripts/task_table_sync.py --apply --category-config config/task_categories.yaml
```

**主要オプション**:
- `--apply` : 変更を `TODO.md` と `CHANGELOG.md` に書き込みます。このフラグがない場合はdry-runモード（変更は保存されず、移行対象と差分概要のみ標準出力に表示）。
- `--check` : テーブルの整合性を検証します。エラーがある場合は非ゼロ終了コードで詳細を出力します。
- `--format-only` : テーブル内容は移行せず、 Markdown の体裁のみ整えます。`--apply` と併用するとファイルを上書きします。
- `--category-config <path>` : カテゴリ分類ルールファイルを指定（既定: `config/task_categories.yaml`）。
- `--todo-path <path>` : TODO.mdのパスを指定（既定: `TODO.md`）。
- `--changelog-path <path>` : CHANGELOG.mdのパスを指定（既定: `CHANGELOG.md`）。

### Validation Rules

- `ID` は `TODO-YYYY-NNNN` 形式でなければなりません（重複も禁止）。
- `Status` は `active` / `blocked` / `done` のいずれかに限定。
- `done` 行で `Completed` または `Commit` が空の場合は移行されません。
- 同一 `ID` が `CHANGELOG.md` に既に存在する場合は重複としてスキップします。
- `CHANGELOG.md` 側でも `Completed` / `Commit` の未入力や重複IDを検出します。
- 解析エラー時は処理を中断し、問題行を標準エラーに表示します（`--check` で事前検知可能）。

### Formatting Support

- `--format-only` 実行時は、テーブルの列幅を揃えたMarkdownに再整形し、人手編集によるズレを解消します。
- 整形のみ行いたい場合は `python scripts/task_table_sync.py --format-only --apply` を利用し、移行を伴う変更と切り分けてください。

---

## Governance

- テーブル外の詳細レポートが必要な場合は別ファイルへ分離し、`Notes` にリンクを記載します。
- 月次で `CHANGELOG.md` をレビューし、リリースノートへ反映してください。
- フォーマット変更が必要になった場合、本ガイドを更新し `scripts/task_table_sync.py` のテストも調整します。

---

## Changelog

| Date | Version | Changes |
| --- | --- | --- |
| 2025-10-12 | 0.3 | `--check` / `--format-only` を追加し、検証・整形フローを明文化。バリデーション項目を強化。 |
| 2025-10-12 | 0.2 | カテゴリ自動分類機能を追加。CHANGELOG.mdにCategoryフィールド追加。 |
| 2025-10-12 | 0.1 | 初版作成。構造化テーブルと自動移行フローを定義。 |

---

**Maintainer**: Workflow Team
**Review Cycle**: Monthly
**Feedback**: GitHub issue `process-improvement` ラベルで提案してください。
