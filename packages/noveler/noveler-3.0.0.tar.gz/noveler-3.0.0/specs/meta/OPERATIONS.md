# Specs Operations

この文書は specs フォルダ運用の手順を簡潔にまとめたものです。

運用方針（要点）
- 現用（canonical）= ISSUE/稼働コンポーネントに紐付く仕様のみ
- 現用の索引と件数は自動生成（README/.spec_counters.json）
- 非現用は `specs/_archive/<timestamp>/` へ退避
- 全現用ファイルはフロントマター必須（spec_id/status/owner/last_reviewed 等）

主要コマンド（Makefile）
- `make specs-sync`: 現用抽出（E2E/REQ）→ 索引/カウンタ更新 → 非現用を `_archive` へ退避
- `make specs-frontmatter`: 現用MDにフロントマターを付与/更新
- `make specs-lint`: 現用仕様のフロントマターとレビュー期限を検証
- `make specs-index`: セマンティック検索用の簡易インデックス生成（`_meta/search_index.json`）
- `make specs-all`: 上記を順番に実行

ローカルチェック（Git Hook）
- インストール: `ln -sf ../../scripts/git-hooks/pre-commit .git/hooks/pre-commit`
- 内容: `specs/_scripts/specs_lint.py` を実行し、不備があればコミットを停止

メンテナンスポイント
- 現用集合の定義は `specs/E2E_TEST_MAPPING.yaml` と `specs/REQ_SPEC_MAPPING_MATRIX.md`
- これらに反映→ `make specs-all` で同期
- 期限基準: `specs_lint.py --max-age-days=120`（必要に応じて変更）
- カテゴリ正規化: `A28→PLOT`, `A30→WRITE`, `A31→QUALITY`, `A38→WRITE`（フロントマター`category`/`tags`にも反映）
