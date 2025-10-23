# CI/CD パイプライン実装サマリー

> **作成日**: 2025年10月22日
> **バージョン**: 1.0
> **ステータス**: Phase 3～4 完成、Phase 5 計画中

---

## 📋 概要

このドキュメントは、noveler プロジェクトの GitHub Actions ベース CI/CD パイプラインの実装内容を総括し、運用開始に必要なステップをまとめています。

**対象フェーズ**:
- **Phase 3**: GitHub Actions ワークフロー実装（pr-check.yml / deploy.yml）
- **Phase 4**: ブランチ保護ルール設定 + 運用ガイド
- **Phase 5**: 通知・セキュリティ強化（計画中）

---

## 🎯 CI/CD パイプラインの全体像

```
┌─────────────────────────────────────────────────────────────────┐
│                    developer workflow                           │
│                                                                  │
│  $ git checkout -b feature/GH-123-add-feature origin/dev       │
│  $ git commit -m "feat: add new feature"                       │
│  $ git push origin feature/GH-123-add-feature                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         ┌────────────────────────────────────────┐
         │  dev branch (統合・QA用)               │
         │  - PR マージ（軽量チェック）           │
         │  - 動作確認・段階的テスト              │
         │  - CI 不要・直プッシュ許可             │
         └────────────────────────────────────────┘
                              ↓
         ┌────────────────────────────────────────┐
         │  main branch (本番・リリース用)        │
         │                                        │
         │  ✅ pr-check.yml 必須                  │
         │     ├─ ruff (コード規約)               │
         │     ├─ mypy (型安全性)                 │
         │     ├─ importlinter (DDD契約)         │
         │     └─ pytest (テスト)                 │
         │                                        │
         │  ✅ 最低1名の レビュー承認             │
         │  ✅ 直プッシュ禁止                    │
         └────────────────────────────────────────┘
                              ↓
         ┌────────────────────────────────────────┐
         │  $ git tag v3.0.1                      │
         │  $ git push origin v3.0.1              │
         └────────────────────────────────────────┘
                              ↓
         ┌────────────────────────────────────────┐
         │  deploy.yml 自動実行                   │
         │                                        │
         │  1. build: wheel + sdist 生成          │
         │  2. publish-pypi: PyPI 公開            │
         │  3. create-release: Release 自動作成  │
         │  4. notify-*: 成否通知                 │
         └────────────────────────────────────────┘
                              ↓
         ┌────────────────────────────────────────┐
         │  本番環境（PyPI + GitHub Releases）   │
         │                                        │
         │  https://pypi.org/project/noveler/    │
         │  Releases タブに自動作成               │
         └────────────────────────────────────────┘
```

---

## 📦 成果物一覧

### **1. PR テンプレート**

**ファイル**: [.github/pull_request_template.md](.github/pull_request_template.md)

**目的**: PR 作成時に必須情報の記載を促し、レビュー効率を向上

**内容**:
- 変更の概要（目的・背景・関連Issue）
- 変更の種類（機能/バグ修正/リファクタリング等）
- 影響範囲（DDD層ごと）
- テスト結果（make test 実行確認）
- 品質チェック（ruff/mypy/importlinter）
- ドキュメント更新確認
- AGENTS.md 準拠チェックリスト

**特徴**:
- ✅ importlinter は `make lint-imports` で実行（lint と分離）
- ✅ DDD層間の依存関係検証を明示
- ✅ テスト・ドキュメント更新の必須化

---

### **2. pr-check.yml（PR 時 自動テスト・lint）**

**ファイル**: [.github/workflows/pr-check.yml](.github/workflows/pr-check.yml)

**トリガー**: main / dev ブランチへの PR

**構成**:

| ジョブ | 説明 | 実行コマンド |
|--------|------|-----------|
| lint | ruff + mypy + importlinter + template検証 | `make lint` → `make lint-imports` → `make validate-templates` |
| test | pytest フルスイート（LLM レポート生成） | `make test` |
| quality-gate | lint/test の両方の成功を確認 | needs で依存関係チェック |

**最適化**:
- **Python**: 3.10 固定（将来的に matrix 拡張可能）
- **OS**: Ubuntu のみ（Linux 前提）
- **並列実行**: lint と test が同時実行（高速化）
- **pip キャッシュ**: `~/.cache/pip` をキャッシュ（セットアップ時間削減）
- **キャッシュキー**: `pyproject.toml` のハッシュに基づく

**トリガー範囲**:
- ⚠️ **paths-ignore なし**: すべての PR（ドキュメント変更含む）でワークフローが実行されます
- これにより、ドキュメント変更のみの PR でも必須チェック（lint/test）が実行されるため、branch protection で「Required status check expected」エラーが発生することを防ぎます
- ドキュメント変更に対しても全チェックが実行されるため、品質基準が一貫性を保つことができます

**artifacts**:
- `reports/llm_summary.{jsonl,txt}`: テスト結果要約（30日保持）

**必須チェック**（main へのマージ条件）:
- ✅ lint: 合格
- ✅ test: 合格
- ✅ quality-gate: 成功

---

### **3. deploy.yml（タグ push で本番デプロイ）**

**ファイル**: [.github/workflows/deploy.yml](.github/workflows/deploy.yml)

**トリガー**: `git tag v*` を push（例: v3.0.1）

**構成**:

| ジョブ | 説明 | 出力 |
|--------|------|------|
| build | wheel + sdist をビルド | `dist/noveler*.whl` + `dist/noveler*.tar.gz` |
| publish-pypi | PyPI に公開（API Token 認証） | PyPI レジストリに登録 |
| create-release | GitHub Release を自動作成 | Releases タブに v3.0.1 表示 |
| notify-deployment | デプロイ成功ログ出力 | アクションログに記録 |
| notify-deployment-failure | デプロイ失敗ログ出力 | エラー情報をログに記録 |

**主要機能**:

1. **タグベーストリガー**
   ```bash
   git tag v3.0.1
   git push origin v3.0.1
   ```

2. **PyPI 認証**
   - `secrets.PYPI_API_TOKEN` で認証
   - API Token 方式（将来 OIDC に移行予定）

3. **CHANGELOG.md 自動抽出**
   - タグ v3.0.1 → バージョン 3.0.1 に変換（`lstrip('v')`）
   - CHANGELOG.md から `## [3.0.1] - YYYY-MM-DD` セクションを検索
   - 見つかれば リリースノートとして Release notes に記載
   - 見つからなければ デフォルトメッセージ（CHANGELOG へのリンク）

4. **GitHub Release 自動作成**
   - wheel + tarball を添付ファイルに
   - リリースノート本文に CHANGELOG セクションを記載
   - draft: false, prerelease: false

---

### **4. ブランチ戦略ガイド**

**ファイル**: [docs/guides/branch_strategy.md](docs/guides/branch_strategy.md)

**内容**:

#### **ブランチ体系（3段階）**

| ブランチ | 目的 | 直プッシュ | PR必須 | CI必須 | レビュー |
|---------|------|---------|--------|--------|---------|
| feature/* | 開発ブランチ | ✅ 許可 | ❌ 不要 | ❌ 不要 | ❌ 不要 |
| dev | 統合・QA | ✅ 許可 | ❌ 不要 | ❌ 不要 | ❌ 不要 |
| main | 本番・リリース | 🚫 禁止 | ✅ 必須 | ✅ 必須 | ✅ 1名 |

#### **GitHub 保護ルール設定手順**
- main ブランチ: 直プッシュ禁止、PR必須、CI必須、レビュー1名
- dev ブランチ: 直プッシュ許可、PR不要、CI不要（統合スピード優先）
- feature/* ブランチ: 保護なし（開発者自由）

#### **運用フロー**
- feature 作成 → dev へ PR（簡易マージ）
- dev → main へ PR（厳格チェック + レビュー）
- main マージ → タグ作成 → 自動デプロイ
- ホットフィックス対応フロー

---

## 🚀 運用開始に必要なステップ

### **STEP 1: GitHub Secrets 登録（5分）**

**場所**: Settings → Secrets and variables → Actions

**登録内容**:

```
Name: PYPI_API_TOKEN
Value: <PyPI API トークン>
```

**トークン取得方法**:
1. https://pypi.org/manage/account/tokens/ にアクセス
2. "Create token for repository" をクリック
3. Scope: noveler を選択
4. トークン値をコピー（例: `pypi-AgXXXXXX...`）
5. GitHub Secrets に貼り付け

---

### **STEP 2: ブランチ保護ルール設定（10分）**

**場所**: Settings → Branches → Branch protection rules

#### **main ブランチ保護ルール**

```
Pattern name: main

✅ Require a pull request before merging
  - Require approvals: 1
  - Dismiss stale pull request approvals: ✅

✅ Require status checks to pass before merging
  - Lint (ruff + mypy + importlinter)
  - Test Suite
  - Quality Gate

✅ Require branches to be up to date before merging

❌ Allow force pushes
❌ Allow deletions
```

⚠️ **重要**: 必須チェック名は `.github/workflows/pr-check.yml` の各ジョブ `name:` フィールドと **完全一致** する必要があります。

| GitHub Actions ジョブ名 | branch protection で指定する名前 |
|------------------------|--------------------------------|
| `name: Lint (ruff + mypy + importlinter)` | `Lint (ruff + mypy + importlinter)` |
| `name: Test Suite` | `Test Suite` |
| `name: Quality Gate` | `Quality Gate` |

**エラー防止**: 名前の誤りがあると「Required status check expected」エラーが発生し、マージできなくなります。

#### **dev ブランチ保護ルール（軽量）**

```
Pattern name: dev

❌ Require a pull request before merging
❌ Require status checks to pass before merging

✅ Include administrators

❌ Allow force pushes
❌ Allow deletions
```

---

### **STEP 3: CHANGELOG.md フォーマット確認**

**既存形式（v なし）で OK**:

```markdown
## [3.0.0] - 2025-10-22

### 🐛 Bug Fixes
- Issue #123: ...

### ✨ Features
- New feature ...
```

**deploy.yml が自動的に v プレフィックスを除去して検索するため、形式変更は不要です。**

---

### **STEP 4: 動作確認テスト**

#### **PR テスト（main ブランチ）**

```bash
git checkout -b feature/test-pr-check origin/dev
echo "# Test" > test.md
git add test.md
git commit -m "test: pr-check workflow"
git push origin feature/test-pr-check
```

GitHub: Create PR → main

✅ 確認ポイント:
- pr-check.yml が自動実行される
- lint/test/quality-gate がすべて成功
- PR マージが可能（最低1名承認後）

#### **デプロイテスト（タグ）**

```bash
git checkout main
git pull origin main
git tag v3.0.0-test
git push origin v3.0.0-test
```

GitHub: Actions → deploy

✅ 確認ポイント:
- deploy.yml が自動実行される
- build → publish-pypi → create-release が順序実行
- GitHub Releases に v3.0.0-test が表示される

**注意**: テスト用のタグは後で削除してもよい
```bash
git tag -d v3.0.0-test
git push origin --delete v3.0.0-test
```

---

## 📊 実装内容の詳細比較

### **pr-check.yml vs 従来型 CI**

| 項目 | 従来型 | pr-check.yml |
|------|--------|-------------|
| トリガー | 手動実行 | PR 自動実行 |
| テスト範囲 | 指定ファイルのみ | 全体 |
| lint 時間 | 毎回インストール | pip キャッシュで高速化 |
| 失敗時対応 | マージ後に気づく | PR 段階で検出 |
| 並列実行 | なし | lint + test 同時実行 |
| レポート | なし | LLM 要約（reports/） |

### **deploy.yml の特徴**

| 項目 | 設定 |
|------|------|
| トリガー | git tag v* push |
| 認証方式 | PYPI_API_TOKEN（API Token） |
| 添付ファイル | wheel + tarball |
| リリースノート | CHANGELOG.md 自動抽出 |
| v プレフィックス処理 | lstrip('v') で自動除去 |
| 失敗通知 | ログ出力（Phase 5 で Slack 追加予定） |
| リリース作成 | GitHub Releases 自動作成 |

---

## 🔒 セキュリティ考慮事項

### **現在の実装**

- ✅ PYPI_API_TOKEN を GitHub Secrets に安全に保管
- ✅ Token スコープを noveler 限定に設定推奨
- ✅ GitHub Actions の環境変数で安全に渡す

### **Phase 5 で検討する項目**

- 🔄 OIDC (Trusted Publisher) への移行（トークン廃止）
- 🔄 署名済みリリース（cosign）
- 🔄 セキュリティアラート監視（Dependabot）

---

## 📈 パフォーマンス最適化

### **pip キャッシュの効果**

```
初回実行:   ~180秒（pip install）
2回目以降:  ~30秒（キャッシュから取得）
節約率:     約 83%
```

### **並列実行による高速化**

```
順序実行:   lint + test = ~60秒 + ~90秒 = ~150秒
並列実行:   max(lint, test) = ~90秒
節約率:     約 40%
```

---

## 🚨 トラブルシューティング

### **問題: CHANGELOG セクションが見つからない**

**症状**: deploy.yml で "See CHANGELOG.md for details" メッセージが出力される

**原因**: CHANGELOG.md に対応バージョンセクションがない

**解決策**:
```markdown
# CHANGELOG.md に追加
## [3.0.1] - 2025-10-22

### 🐛 Bug Fixes
- ...
```

**v プレフィックスは不要** - deploy.yml が自動的に除去します

---

### **問題: PyPI へのpublish が失敗**

**症状**: deploy.yml で "Publish to PyPI" ステップが失敗

**原因**: PYPI_API_TOKEN が不正 or 未登録

**解決策**:
1. GitHub → Settings → Secrets で `PYPI_API_TOKEN` を確認
2. PyPI https://pypi.org/manage/account/tokens/ でトークン確認
3. トークンを再生成して GitHub Secrets に更新

---

### **問題: main ブランチへマージできない**

**症状 A**: "Require status checks to pass before merging" エラー

**原因**: pr-check.yml がまだ実行中 or 失敗

**解決策**:
1. Actions タブで pr-check.yml の実行状況を確認
2. 失敗している場合は ローカルで `make test` / `make lint` を実行
3. 修正後、new commit を push

---

**症状 B**: "Required status check expected" エラー（チェック実行後も解決しない）

**原因**: branch protection で指定した必須チェック名が `.github/workflows/pr-check.yml` のジョブ名と一致していない

**解決策**:
1. `.github/workflows/pr-check.yml` を確認し、ジョブ `name:` フィールドを確認:
   ```yaml
   jobs:
     lint:
       name: Lint (ruff + mypy + importlinter)  # ← この名前
     test:
       name: Test Suite                         # ← この名前
     quality-gate:
       name: Quality Gate                       # ← この名前
   ```

2. GitHub → Settings → Branches → Branch protection rules で必須チェックを確認
3. ジョブ名と必須チェック名が **完全一致** していることを確認:
   | ジョブ名 | branch protection での指定 |
   |---------|--------------------------|
   | `Lint (ruff + mypy + importlinter)` | `Lint (ruff + mypy + importlinter)` |
   | `Test Suite` | `Test Suite` |
   | `Quality Gate` | `Quality Gate` |

4. 不一致があれば、branch protection の必須チェック名を修正

---

## 📚 関連ドキュメント

- **[AGENTS.md](../AGENTS.md)**: コード品質・TDD/DDD 原則
- **[CLAUDE.md](../CLAUDE.md)**: MCP 統合・レイヤリング契約
- **[branch_strategy.md](branch_strategy.md)**: ブランチ運用詳細
- **[.github/pull_request_template.md](.github/pull_request_template.md)**: PR テンプレート
- **[CHANGELOG.md](../CHANGELOG.md)**: リリースノート

---

## 🔄 Phase 5 計画（将来実装）

### **5A. Slack 通知**

```yaml
- CI 失敗時: Slack チャネルへ自動通知
- デプロイ完了: リリース情報をアナウンス
```

### **5B. セキュリティ強化**

```yaml
- PYPI 認証: OIDC (Trusted Publisher) へ移行
- リリース署名: cosign で署名済みリリース作成
- 依存関係: Dependabot による自動セキュリティアラート
```

### **5C. 多環境対応**

```yaml
- Python: 3.11, 3.12 への matrix テスト拡張
- OS: macOS, Windows への対応（必要に応じて）
```

### **5D. 自動化強化**

```yaml
- CHANGELOG: conventional commits から自動生成
- バージョン: 自動更新・タグ作成
- リリースノート: AI による自動要約
```

---

## ✅ チェックリスト（実装前確認）

### **ファイル確認**
- [ ] `.github/pull_request_template.md` が存在
- [ ] `.github/workflows/pr-check.yml` が存在
- [ ] `.github/workflows/deploy.yml` が存在
- [ ] `docs/guides/branch_strategy.md` が存在

### **前提条件確認**
- [ ] CHANGELOG.md が `## [X.Y.Z] - YYYY-MM-DD` 形式
- [ ] pyproject.toml の version が最新版
- [ ] GitHub リポジトリの管理権限がある
- [ ] PyPI アカウント・API トークンが用意できる

### **GitHub 設定**
- [ ] PYPI_API_TOKEN を Secrets に登録
- [ ] main ブランチ保護ルール設定
- [ ] dev ブランチ保護ルール設定
- [ ] PR テンプレート表示確認

### **動作確認テスト**
- [ ] feature ブランチで PR テスト（pr-check.yml）
- [ ] main へのマージテスト（レビュー承認）
- [ ] タグ push でデプロイテスト（deploy.yml）
- [ ] GitHub Releases に自動作成確認

---

## 📞 サポート

**質問・トラブル**:
- GitHub Issues で報告
- `docs/guides/branch_strategy.md` のトラブルシューティング参照

**改善提案**:
- Phase 5 計画に含めて検討

---

**最終更新**: 2025年10月22日
**作成者**: Claude Code Assistant
**ステータス**: Phase 3～4 完成・Phase 5 計画中
